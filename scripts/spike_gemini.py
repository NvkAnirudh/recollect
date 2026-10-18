"""SPIKE (#20), throwaway: how well does one Gemini call understand a reel?

Downloads each reel in backend/tests/eval/reels.toml (yt-dlp, local only), sends it to Gemini
with the ReelUnderstanding schema from the v1 spec (§4) under several settings, and scores
recall of the hand-checked on-screen and spoken reference phrases.

Not production code: no tests, no reuse. The decision it informs goes into an ADR + the spec.

Usage (from repo root, GEMINI_API_KEY in backend/.env):
    uv run --no-project --with google-genai --with pydantic --with python-dotenv \
        python scripts/spike_gemini.py --list-models
    uv run --no-project --with google-genai --with pydantic --with python-dotenv \
        python scripts/spike_gemini.py --models <model-a>,<model-b>
"""

import argparse
import json
import os
import re
import subprocess
import time
import tomllib
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "backend/tests/eval/reels.toml"
MEDIA = ROOT / ".spike-media"  # git-ignored
OUT = ROOT / "scripts/.spike-results"  # git-ignored


class ReelUnderstanding(BaseModel):
    """Spec §4 output schema."""

    transcript: str = Field(
        description="Spoken words, verbatim, in the original language. Empty if no speech; "
        "do not transcribe song lyrics as speech unless clearly the main content."
    )
    on_screen_text: str = Field(
        description="All legible text overlaid or shown in the video (captions, titles, "
        "lists, UI, signs), in order of appearance, deduplicated."
    )
    visual_description: str = Field(
        description="What is shown: setting, people, objects, actions, notable visuals."
    )
    summary: str = Field(description="1-2 sentences: what this reel is about.")
    topics: list[str] = Field(description="3-8 short lowercase keywords for search.")
    language: str = Field(
        description="ISO 639-1 code of the main spoken (or, if no speech, written) language."
    )


PROMPT = """You are indexing a short social video (an Instagram Reel) so its owner can find it
later by searching for anything that was said, shown on screen, or captioned.
The post's caption is given for context; do not copy it into the other fields.

Caption:
{caption}

Return the structured fields. Be exhaustive for on_screen_text: users search for exact words
they remember seeing. Keep transcript in the original language."""

SETTINGS = {
    # name: (fps, media_resolution)
    "fps1": (1.0, None),
    "fps3": (3.0, None),
    "fps1-low": (1.0, types.MediaResolution.MEDIA_RESOLUTION_LOW),
}


@dataclass
class Result:
    reel: int
    category: str
    model: str
    setting: str
    ok: bool
    error: str
    latency_s: float
    prompt_tokens: int
    output_tokens: int
    thinking_tokens: int
    on_screen_recall: float | None
    spoken_recall: float | None
    language: str
    language_ok: bool | None
    missed_on_screen: list[str]
    summary: str


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s%]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def found(phrase: str, haystack: str) -> bool:
    """Phrase counts as found if ≥80% of its tokens appear in the haystack."""
    tokens = norm(phrase).split()
    hay = set(norm(haystack).split())
    return bool(tokens) and sum(t in hay for t in tokens) / len(tokens) >= 0.8


def recall(phrases: list[str], haystack: str) -> tuple[float | None, list[str]]:
    if not phrases:
        return None, []
    missed = [p for p in phrases if not found(p, haystack)]
    return 1 - len(missed) / len(phrases), missed


def download(reel: dict) -> tuple[Path, str]:
    MEDIA.mkdir(exist_ok=True)
    path = MEDIA / f"{reel['id']}.mp4"
    info_path = MEDIA / f"{reel['id']}.info.json"
    if not path.exists():
        subprocess.run(
            [
                "yt-dlp",
                "-q",
                "--no-warnings",
                "-f",
                "b[ext=mp4]/b",
                "--write-info-json",
                "-o",
                str(MEDIA / f"{reel['id']}.%(ext)s"),
                reel["url"],
            ],
            check=True,
        )
    if not info_path.exists():
        return path, ""
    caption = json.loads(info_path.read_text()).get("description") or ""
    return path, caption


def upload(client: genai.Client, path: Path) -> types.File:
    f = client.files.upload(file=path)
    while f.state and f.state.name == "PROCESSING":
        time.sleep(2)
        f = client.files.get(name=f.name)  # type: ignore[arg-type]
    if f.state and f.state.name != "ACTIVE":
        raise RuntimeError(f"upload failed: {f.state}")
    return f


def understand(client, model, file, caption, fps, resolution):
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ReelUnderstanding,
        media_resolution=resolution,
        temperature=0,
    )
    contents = [
        types.Part(
            file_data=types.FileData(file_uri=file.uri, mime_type=file.mime_type),
            video_metadata=types.VideoMetadata(fps=fps),
        ),
        PROMPT.format(caption=caption or "(none)"),
    ]
    for attempt in range(6):
        try:
            start = time.perf_counter()
            resp = client.models.generate_content(model=model, contents=contents, config=config)
            return resp, time.perf_counter() - start
        except errors.APIError as e:
            if e.code in (429, 500, 503) and attempt < 5:
                time.sleep(min(60, 5 * 2**attempt))
                continue
            raise
    raise RuntimeError("unreachable")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    ap.add_argument("--settings", default=",".join(SETTINGS))
    ap.add_argument("--reels", default="", help="comma-separated ids (default: all video reels)")
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    load_dotenv(ROOT / "backend/.env")
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    if args.list_models:
        for m in client.models.list():
            if "generateContent" in (m.supported_actions or []) and "gemini" in (m.name or ""):
                print(m.name, "|", m.display_name)
        return

    reels = [r for r in tomllib.loads(EVAL.read_text())["reel"] if r["kind"] == "reel"]
    if args.reels:
        wanted = {int(x) for x in args.reels.split(",")}
        reels = [r for r in reels if r["id"] in wanted]

    OUT.mkdir(exist_ok=True)
    results: list[Result] = []
    for reel in reels:
        path, caption = download(reel)
        file = upload(client, path)
        try:
            for model in args.models.split(","):
                for name in args.settings.split(","):
                    fps, res = SETTINGS[name]
                    try:
                        resp, latency = understand(client, model, file, caption, fps, res)
                        u: ReelUnderstanding = resp.parsed  # type: ignore[assignment]
                        usage = resp.usage_metadata
                        visual = f"{u.on_screen_text}\n{u.visual_description}"
                        os_recall, missed = recall(reel["on_screen"], visual)
                        sp_recall, _ = recall(reel["spoken"], u.transcript)
                        (OUT / f"{reel['id']}-{model.replace('/', '_')}-{name}.json").write_text(
                            u.model_dump_json(indent=2)
                        )
                        r = Result(
                            reel["id"],
                            reel["category"],
                            model,
                            name,
                            True,
                            "",
                            round(latency, 1),
                            usage.prompt_token_count or 0,
                            usage.candidates_token_count or 0,
                            usage.thoughts_token_count or 0,
                            os_recall,
                            sp_recall,
                            u.language,
                            u.language.lower().startswith(reel["language"]),
                            missed,
                            u.summary[:120],
                        )
                    except Exception as e:
                        r = Result(
                            reel["id"],
                            reel["category"],
                            model,
                            name,
                            False,
                            str(e)[:200],
                            0,
                            0,
                            0,
                            0,
                            None,
                            None,
                            "",
                            None,
                            [],
                            "",
                        )
                    results.append(r)
                    brief = {
                        k: v
                        for k, v in asdict(r).items()
                        if k not in ("missed_on_screen", "summary")
                    }
                    print(json.dumps(brief))
        finally:
            client.files.delete(name=file.name)  # type: ignore[arg-type]

    (OUT / "results.json").write_text(json.dumps([asdict(r) for r in results], indent=2))
    print(f"\nwrote {OUT / 'results.json'}")


if __name__ == "__main__":
    main()
