"""SPIKE (#20), throwaway: summarise scripts/.spike-results/results.json as markdown tables."""

import json
import statistics
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent / ".spike-results/results.json"

# USD per 1M tokens (input, output incl. thinking), from
# ai.google.dev/gemini-api/docs/pricing on 2026-10-19.
# gemini-3.8-flash is at an introductory rate until 2026-12-31, then doubles (1.50 / 7.50).
PRICES = {"gemini-3.8-flash": (0.75, 3.75), "gemini-3.5-flash-lite": (0.30, 2.50)}


def mean(xs: list[float]) -> str:
    return f"{statistics.mean(xs):.0%}" if xs else "-"


def main() -> None:
    rows = json.loads(RESULTS.read_text())
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["setting"])].append(r)

    print(
        "| Model | Setting | OK | On-screen recall | Speech recall | Language "
        "| Latency (avg) | Cost / reel |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for (model, setting), rs in sorted(groups.items()):
        ok = [r for r in rs if r["ok"]]
        pin, pout = PRICES.get(model, (0, 0))
        cost = [
            (r["prompt_tokens"] * pin + (r["output_tokens"] + r["thinking_tokens"]) * pout) / 1e6
            for r in ok
        ]
        print(
            f"| {model} | {setting} | {len(ok)}/{len(rs)} "
            f"| {mean([r['on_screen_recall'] for r in ok if r['on_screen_recall'] is not None])} "
            f"| {mean([r['spoken_recall'] for r in ok if r['spoken_recall'] is not None])} "
            f"| {sum(bool(r['language_ok']) for r in ok)}/{len(ok)} "
            f"| {statistics.mean([r['latency_s'] for r in ok]) if ok else 0:.1f}s "
            f"| ${statistics.mean(cost) if cost else 0:.4f} |"
        )

    print("\n| Reel | Category | " + " | ".join(f"{m} {s}" for m, s in sorted(groups)) + " |")
    print("|---|---|" + "---|" * len(groups))
    for reel in sorted({r["reel"] for r in rows}):
        cells = []
        for key in sorted(groups):
            r = next((x for x in groups[key] if x["reel"] == reel), None)
            if r is None or not r["ok"]:
                cells.append("fail")
                continue
            os_ = "-" if r["on_screen_recall"] is None else f"{r['on_screen_recall']:.0%}"
            sp = "-" if r["spoken_recall"] is None else f"{r['spoken_recall']:.0%}"
            cells.append(f"os {os_} / sp {sp} / {r['language']}")
        category = next(r["category"] for r in rows if r["reel"] == reel)
        print(f"| {reel} | {category} | " + " | ".join(cells) + " |")

    print("\nMissed on-screen phrases (best setting per model shown first):")
    for r in sorted(rows, key=lambda r: (r["model"], r["setting"], r["reel"])):
        if r["ok"] and r["missed_on_screen"]:
            print(f"- {r['model']} {r['setting']} reel {r['reel']}: {r['missed_on_screen']}")


if __name__ == "__main__":
    main()
