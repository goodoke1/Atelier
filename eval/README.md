# Evaluation

A reproducible accuracy harness for the garment classifier.

```
eval/
├── image_urls.json     50 Pexels image URLs (free license) — the test set
├── labels.json         hand-labeled ground truth, one entry per image
├── download_images.py  fetches the images into images/
├── eval_runner.py      classifies + scores + writes report.md
└── images/             downloaded test images (gitignored)
```

## Run it

```bash
# from the repo root, with backend deps installed (see top-level README)
cd eval
python download_images.py            # fetch the 50 images
python eval_runner.py                # full run -> report.md

python eval_runner.py --max 10       # quick subset
python eval_runner.py --dry-run      # list the plan, no API calls
FASHION_AI_STUB=1 python eval_runner.py   # offline pipeline check (low accuracy by design)
```

The active provider is whatever the backend is configured to use
(`MODEL_PROVIDER` + key, or the stub). The runner imports the app's own
`classifier`/`parser`, so evaluation mirrors production exactly.

## Methodology

- **Test set:** 50 garment / street-fashion images from Pexels, each labeled by
  visual inspection. Non-garment images were excluded.
- **Ground truth:** `labels.json` records expected `garment_type, style,
  material, pattern, season, occasion, color_palette, location_context`.
  Genuinely ambiguous fields list alternatives separated by `|`
  (e.g. `"jacket|coat"`), any of which counts as correct.
- **Scoring** (lenient, because fashion attributes are fuzzy):
  - categorical fields → containment match (substring / token overlap),
  - `color_palette` → recall of the labelled colours, token-aware so `blue`
    counts against `navy blue`; correct if at least half are recovered (extra
    shades the model also names aren't penalized),
  - `location_context` → matched against the AI's free-text description, with a
    small synonym map (`studio` ≈ "seamless backdrop", `street` ≈ "urban"). The
    model isn't asked to name a location, so this tests whether it *perceived*
    the setting — and it's the weakest attribute as a result.

See the top-level **README → Model evaluation** for the discussion of where the
model performs well, where it struggles, and how it would be improved.
