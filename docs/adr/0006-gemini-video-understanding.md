# 0006. Gemini 3.8 Flash at 1 fps for reel understanding, Flash-Lite fallback, no OCR

Date: 2026-10-19 · Status: Accepted

## Context
Recollect must find reels by what was said, shown on screen, or seen. The spec planned one
multimodal Gemini call per reel and left the model, frame rate and OCR to a spike (#20).
Results: [docs/spikes/2026-10-19-gemini-understanding.md](../spikes/2026-10-19-gemini-understanding.md).

## Decision
- **Primary model:** `gemini-3.8-flash`, video sampled at **1 fps**, default media resolution,
  structured output (`ReelUnderstanding`), temperature 0, with the caption as context.
  It reached 97–98% on-screen and 95% speech recall, handled fast cuts, and transcribes
  non-Latin speech in its own script.
- **Fallback:** `gemini-3.5-flash-lite` at 1 fps, used when the primary returns 429/5xx after
  retries (92–95% on-screen recall, about a third of the cost).
- **No separate OCR pass.**
- Model IDs and fps are settings (`GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`, `GEMINI_VIDEO_FPS`),
  not code, so they can change without a code change.

## Consequences
- About 1.2¢ per reel today, about 2.4¢ from 2027-01-01 when the introductory price ends. 1,000 reels a month is $12–24.
- The Gemini key needs billing enabled for real use; free-tier quota ran out after about 20 calls.
- 15–30s per reel, within the spec's "searchable within 2 minutes" target.
- Re-run `scripts/spike_gemini.py` when changing model or fps; the eval set is the regression check.
- Carousels (image posts) are out of scope until a separate feature adds an image fetcher.
