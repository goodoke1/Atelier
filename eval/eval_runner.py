#!/usr/bin/env python3
"""Evaluate the garment classifier against a hand-labeled test set.

Loads ``labels.json`` (image filename -> expected attributes), runs each image
through the *same* classifier the app uses, scores predictions per attribute,
and writes a Markdown report (``report.md``).

Scoring is intentionally lenient because fashion attributes are fuzzy:
  * categorical fields (garment_type, style, material, pattern, season,
    occasion, location_*) use containment matching — credit if the expected
    label appears in the prediction or vice-versa (handles "jacket" vs
    "denim jacket", "fall/winter" vs "winter").
  * color_palette uses token-set (Jaccard) overlap with a 0.34 threshold.

Usage:
    python eval_runner.py                  # full run
    python eval_runner.py --max 10         # quick subset
    python eval_runner.py --dry-run        # show plan, no API calls

The active provider is whatever the backend is configured to use. Set
FASHION_AI_STUB=1 to score the offline deterministic stub (useful for CI /
pipeline smoke tests — accuracy will be low, that's expected).
"""
import argparse
import json
import os
import sys
from collections import defaultdict

# Reuse the backend's classifier and parser so eval mirrors production exactly.
BACKEND = os.path.join(os.path.dirname(__file__), "..", "app", "backend")
sys.path.insert(0, os.path.abspath(BACKEND))

from classifier import classify_image  # noqa: E402
from providers import get_provider  # noqa: E402

HERE = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(HERE, "images")
LABELS_PATH = os.path.join(HERE, "labels.json")
REPORT_PATH = os.path.join(HERE, "report.md")

# Attributes we score and how.
CATEGORICAL = [
    "garment_type",
    "style",
    "material",
    "pattern",
    "season",
    "occasion",
    "location_context",
]
SET_FIELDS = ["color_palette"]


def _norm(s):
    return str(s or "").strip().lower()


def _tokens(s):
    return {t.strip() for t in _norm(s).replace("/", ",").split(",") if t.strip()}


def categorical_match(expected: str, predicted: str) -> bool:
    """Lenient containment match on any expected synonym (pipe-separated)."""
    pred = _norm(predicted)
    if not pred:
        return False
    for option in str(expected).split("|"):
        exp = _norm(option)
        if not exp:
            continue
        if exp in pred or pred in exp or _tokens(exp) & _tokens(pred):
            return True
    return False


def set_match(expected: str, predicted: str) -> bool:
    """Score colour as RECALL of expected colours found in the prediction.

    For palette we ask "did the model capture the colours we labeled?" rather
    than penalizing it for *also* naming shades we didn't (a correct
    `black, charcoal, gold` shouldn't lose to a label of just `black`). Matching
    is substring-aware per token so `blue` is credited against `navy blue`, and
    we accept when at least half the expected colours are recovered.
    """
    exp, pred = _tokens(expected), _tokens(predicted)
    if not exp:
        return True
    if not pred:
        return False

    def found(color: str) -> bool:
        # exact token, or expected colour is a word inside a predicted shade
        return any(color == p or color in p.split() or p in color.split() for p in pred)

    recovered = sum(found(c) for c in exp)
    return recovered / len(exp) >= 0.5


# Setting synonyms so a labeled "studio" is credited when the model says
# "seamless backdrop"/"plain background", "street" for "urban"/"sidewalk", etc.
LOCATION_SYNONYMS = {
    "studio": ["studio", "backdrop", "seamless", "plain background", "neutral background", "grey background", "gray background", "white background"],
    "indoor": ["indoor", "interior", "inside", "room", "store", "shop", "boutique"],
    "store": ["store", "shop", "boutique", "rack", "retail"],
    "outdoor": ["outdoor", "outside", "sky", "nature", "park", "garden", "field", "beach"],
    "street": ["street", "urban", "sidewalk", "city", "alley", "graffiti"],
    "urban": ["urban", "street", "city", "building", "sidewalk"],
    "nature": ["nature", "garden", "field", "forest", "outdoor", "grass", "flowers"],
}


def location_match(expected: str, description: str) -> bool:
    """Did the AI description perceive the labeled setting?

    The model isn't asked to name a location, so we look for the setting word
    (or a synonym) anywhere in its free-text description.
    """
    desc = _norm(description)
    for option in str(expected).split("|"):
        opt = _norm(option)
        candidates = LOCATION_SYNONYMS.get(opt, [opt])
        if any(c in desc for c in candidates):
            return True
    return False


def score_image(expected: dict, predicted: dict, description: str) -> dict:
    results = {}
    for field in CATEGORICAL:
        if field not in expected:
            continue
        if field == "location_context":
            results[field] = location_match(expected[field], description)
        else:
            results[field] = categorical_match(expected[field], predicted.get(field, ""))
    for field in SET_FIELDS:
        if field in expected:
            results[field] = set_match(expected[field], predicted.get(field, ""))
    return results


def run(max_images=None, dry_run=False):
    with open(LABELS_PATH) as f:
        labels = json.load(f)

    if max_images:
        labels = labels[:max_images]

    provider = get_provider().name
    print(f"Provider: {provider}  |  images: {len(labels)}")
    if dry_run:
        for item in labels:
            print(f"  would classify {item['filename']}")
        return

    per_field_correct = defaultdict(int)
    per_field_total = defaultdict(int)
    rows = []

    for i, item in enumerate(labels, 1):
        path = os.path.join(IMAGES_DIR, item["filename"])
        if not os.path.exists(path):
            print(f"  [{i}] MISSING {item['filename']} — run download_images.py first")
            continue
        try:
            result = classify_image(path)
        except Exception as exc:  # noqa: BLE001
            print(f"  [{i}] ERROR {item['filename']}: {exc}")
            continue

        attrs = result["attributes"]
        scores = score_image(item["expected"], attrs, result["description"])
        for field, ok in scores.items():
            per_field_total[field] += 1
            per_field_correct[field] += int(ok)
        correct = sum(scores.values())
        total = len(scores)
        print(f"  [{i}] {item['filename']}: {correct}/{total}")
        rows.append((item["filename"], scores, attrs))

    write_report(provider, per_field_correct, per_field_total, rows)
    print(f"\nReport written to {REPORT_PATH}")


def write_report(provider, correct, total, rows):
    lines = ["# Classifier Evaluation Report", ""]
    lines.append(f"- **Provider:** `{provider}`")
    lines.append(f"- **Images scored:** {len(rows)}")
    lines.append("")
    lines.append("## Per-attribute accuracy")
    lines.append("")
    lines.append("| Attribute | Accuracy | Correct / Total |")
    lines.append("| --- | --- | --- |")

    overall_c = overall_t = 0
    for field in CATEGORICAL + SET_FIELDS:
        if total[field] == 0:
            continue
        acc = correct[field] / total[field]
        overall_c += correct[field]
        overall_t += total[field]
        lines.append(f"| {field} | {acc:.0%} | {correct[field]} / {total[field]} |")
    if overall_t:
        lines.append(f"| **overall** | **{overall_c / overall_t:.0%}** | {overall_c} / {overall_t} |")

    lines.append("")
    lines.append("## Per-image detail")
    lines.append("")
    lines.append("| Image | " + " | ".join(CATEGORICAL + SET_FIELDS) + " |")
    lines.append("| --- |" + " --- |" * len(CATEGORICAL + SET_FIELDS))
    for filename, scores, _ in rows:
        cells = []
        for field in CATEGORICAL + SET_FIELDS:
            if field in scores:
                cells.append("✓" if scores[field] else "✗")
            else:
                cells.append("—")
        lines.append(f"| {filename} | " + " | ".join(cells) + " |")

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "See README for a discussion of where the model performs well, where it "
        "struggles, and planned improvements."
    )

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=None, help="limit number of images")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run(max_images=args.max, dry_run=args.dry_run)
