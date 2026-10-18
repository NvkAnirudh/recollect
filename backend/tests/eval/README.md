# Evaluation set

`reels.toml` is a fixed set of 10 public Instagram posts used to measure content understanding
(spike #20) and, later, search quality (#42).

| Category | Items | Why |
|---|---|---|
| Text on screen / music only | 1–4 | No speech, so content is only in the visuals and on-screen text |
| Non-English | 5 (Telugu), 6 (Hindi) | Multilingual transcription and search |
| Spoken English | 7–10 | Typical talking-head reels with captions and diagrams |

Items 1 and 3 are **image carousels** (`/p/` posts with no video). `yt-dlp` returns only their
captions, and the v1 pipeline is reel-only. They stay in the set to track carousel support as a
later feature.

Rules:
- Store canonical URLs only. Strip share-tracking query params (`?igsh=`, `?rpxt=`, …), which can identify the sharer.
- Never commit media. Scripts download it to a local, git-ignored directory.
- `on_screen`/`spoken` phrases are hand-checked references; add distinctive phrases rather than exhaustive transcripts.
