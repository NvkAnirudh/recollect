# Spike: Gemini video understanding quality

Date: 2026-10-19 · Issue: [#20](https://github.com/NvkAnirudh/recollect/issues/20) (feature #18) ·
Decision: [ADR 0006](../adr/0006-gemini-video-understanding.md)

## Question

Can one Gemini call per reel capture what is **said**, **shown on screen** and **seen** well
enough for search, without a separate OCR pass? Which model and frame rate should we use?

## Method

- **Set:** the 8 video reels in [`backend/tests/eval/reels.toml`](../../backend/tests/eval/reels.toml), 17–180s long: 2 music-only/on-screen-text, 2 non-English (Telugu, Hindi), 4 spoken English with captions and diagrams. The two carousels (#1, #3) are images, not video, and were excluded.
- **Script:** [`scripts/spike_gemini.py`](../../scripts/spike_gemini.py), using the spec §4 `ReelUnderstanding` schema as structured output, temperature 0, with the caption as context.
- **Settings:** 1 fps, 3 fps, and 1 fps at low media resolution, on `gemini-3.8-flash` and `gemini-3.5-flash-lite` (48 calls). `gemini-2.5-flash` is retired for new keys; `gemini-3.1-flash-lite` matched 3.5-flash-lite on a smoke test.
- **Scoring:** recall of hand-checked reference phrases. A phrase counts as found when ≥80% of its tokens appear in `on_screen_text` + `visual_description` (on-screen) or in `transcript` (speech).
- **Cost:** from the token usage, at ai.google.dev pricing on 2026-10-19. 3.8-flash: $0.75 in / $3.75 out per 1M tokens (introductory rate until 2026-12-31, then $1.50 / $7.50). 3.5-flash-lite: $0.30 / $2.50.

## Results

| Model | Setting | OK | On-screen recall | Speech recall | Language | Latency (avg) | Cost / reel |
|---|---|---|---|---|---|---|---|
| gemini-3.5-flash-lite | fps1 | 8/8 | 89% | 96% | 8/8 | 8.3s | $0.0036 |
| gemini-3.5-flash-lite | fps1-low | 8/8 | 92% | 96% | 8/8 | 4.8s | $0.0037 |
| gemini-3.5-flash-lite | fps3 | 8/8 | 95% | 96% | 8/8 | 7.1s | $0.0065 |
| gemini-3.8-flash | fps1 | 7/8 | 97% | 95% | 7/7 | 18.9s | $0.0118 |
| gemini-3.8-flash | fps1-low | 6/8 | 98% | 93% | 6/6 | 16.3s | $0.0120 |
| gemini-3.8-flash | fps3 | 7/8 | 97% | 95% | 7/7 | 27.7s | $0.0196 |

| Reel | Category | gemini-3.5-flash-lite fps1 | gemini-3.5-flash-lite fps1-low | gemini-3.5-flash-lite fps3 | gemini-3.8-flash fps1 | gemini-3.8-flash fps1-low | gemini-3.8-flash fps3 |
|---|---|---|---|---|---|---|---|
| 2 | text_or_music_only | os 100% / sp - / en | os 100% / sp - / en | os 100% / sp - / en | os 100% / sp - / en | os 100% / sp - / en | os 100% / sp - / en |
| 4 | text_or_music_only | os 57% / sp - / en | os 86% / sp - / en | os 86% / sp - / en | os 100% / sp - / en | os 100% / sp - / en | os 100% / sp - / en |
| 5 | non_english | os 100% / sp - / te | os 100% / sp - / te | os 100% / sp - / te | os 100% / sp - / te | os 100% / sp - / te | os 100% / sp - / te |
| 6 | non_english | os 100% / sp 100% / hi | os 80% / sp 100% / hi | os 100% / sp 100% / hi | os 100% / sp 100% / hi | os 100% / sp 100% / hi | os 100% / sp 100% / hi |
| 7 | spoken_english | os 73% / sp 80% / en | os 73% / sp 80% / en | os 73% / sp 80% / en | os 82% / sp 80% / en | os 91% / sp 80% / en | os 82% / sp 80% / en |
| 8 | spoken_english | os 86% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en |
| 9 | spoken_english | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | fail | os 100% / sp 100% / en |
| 10 | spoken_english | os 100% / sp 100% / en | os 100% / sp 100% / en | os 100% / sp 100% / en | fail | fail | fail |

`os` = on-screen recall, `sp` = speech recall (`-` = no reference phrases), then the detected language.
4 of the 24 `gemini-3.8-flash` calls failed with `429 RESOURCE_EXHAUSTED` (free-tier quota),
on reels 9 and 10.

## Findings

1. **No OCR pass needed.** Both models read the 40+ terms of the music-only list reel (#2) at
   100%, and the on-screen text of the Telugu and Hindi reels at 100% (3.8-flash).
2. **Most remaining "misses" are covered by the transcript.** In reel #7, "database index",
   "sharding" and "server sent events" are burned-in speech captions, and they are all in the
   transcript. Search indexes transcript + on-screen text together (spec §5.2), so these are found.
3. **Fast cuts separate the models.** Reel #4 flashes country names on photo books.
   3.5-flash-lite at 1 fps missed Brazil, Italy and Rome; 3.8-flash at 1 fps, or Lite at 3 fps, caught them.
4. **Non-Latin speech:** 3.8-flash transcribes Telugu in Telugu script, keeping English terms;
   3.5-flash-lite romanises it. Both keep the searchable English terms (Karpathy, agentic engineering).
   Local Whisper `base` produced nothing usable for Telugu.
5. **Latency** (16–28s for 3.8-flash) is irrelevant because processing is asynchronous.
6. **Free-tier quota** for 3.8-flash ran out after about 20 calls. Production needs billing enabled.
7. **Carousels** (`/p/` image posts) aren't fetchable with yt-dlp. They need an image fetcher and an image prompt; that's a separate future feature.
