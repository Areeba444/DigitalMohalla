# ADR-0016 memory test: sentence-embedding model next to the API

| Field | Value |
| :--- | :--- |
| Date | 15 November 2026 |
| Purpose | ADR-0016 decision 3 and design-gate item: does a small sentence-embedding model fit in the API process on Render's free tier (512 MB)? |
| Machine | The team's development laptop (Windows 11, Python 3.12). **Not** Render: Linux memory figures will differ, so this is an indication, not the final answer |
| Model | `BAAI/bge-small-en-v1.5` through `fastembed` (ONNX runtime), 384 dimensions, the size `item_embedding` stores |
| Script | Measured in an isolated environment with `psutil` (resident set size); input = the 170 rows of `data/derived/search/catalogue.csv` |
| Run by | Areeba Javed's A9 work, in the shared session; to be repeated on Render |

## Measured

| Step | Resident memory | Time |
| :--- | ---: | ---: |
| Python alone | 19 MB | |
| After importing fastembed | 83 MB | |
| After loading the model (first run downloads it) | 222 MB | 61 s (download included) |
| After embedding all 170 catalogue texts in one batch | 418 MB (peak) | 4.1 s |
| One query (mean of 3) | | 14 ms |
| The API process at import (FastAPI, SQLAlchemy, NumPy, SciPy), measured separately | 141 MB | |

## What it means

- Loading the model adds about 200 MB to the API, so the API with the model loaded is roughly 140 + 200 = 340 MB before any work, on this machine.
- Embedding one query is cheap (14 ms). The risk is the **backfill**: one batch of 170 texts raised the process to 418 MB on its own, and added to the API it would pass 512 MB. The backfill should embed in small batches (a few items per job claim, as `EmbeddingBackfill` does: one item per claim), which keeps the peak near the loaded size.
- The first load takes about a minute because the model is downloaded; on Render it would happen at each cold start unless the model is baked into the image.

## Decision still owed (Fatima and Areeba, ADR-0016)

1. Repeat the measurement on Render itself (or a 512 MB Linux container) with the API running.
2. Choose: enable `EMBEDDING_MODEL` on Render with the model in the image, or keep deployment keyword-only and run meaning-based search for the evaluation (M11) locally. Until then `EMBEDDING_MODEL` is unset in `render.yaml`, so the deployed search is KEYWORD_ONLY, the designed fallback (FR-S-02).
3. Add `fastembed` (Apache-2.0), `onnxruntime` (MIT) and the model (MIT licence on its model card; to be confirmed) to the dependency register when it is enabled.
