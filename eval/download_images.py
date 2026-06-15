#!/usr/bin/env python3
"""Download the evaluation test set from Pexels (free, no API key).

Reads ``image_urls.json`` and saves each image into ``images/<id>.jpg``. Images
are public-domain / Pexels-licensed (free to use). Re-running skips files that
already exist.
"""
import json
import os
import time

import httpx

HERE = os.path.dirname(__file__)
URLS_PATH = os.path.join(HERE, "image_urls.json")
IMAGES_DIR = os.path.join(HERE, "images")


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    with open(URLS_PATH) as f:
        urls = json.load(f)

    ok = skipped = failed = 0
    for item in urls:
        dest = os.path.join(IMAGES_DIR, f"{item['id']}.jpg")
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            skipped += 1
            continue
        try:
            resp = httpx.get(item["url"], timeout=30, follow_redirects=True)
            resp.raise_for_status()
            with open(dest, "wb") as out:
                out.write(resp.content)
            ok += 1
            print(f"  downloaded {item['id']}")
            time.sleep(0.15)  # be polite to the CDN
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAILED {item['id']}: {exc}")

    print(f"\nDone. {ok} downloaded, {skipped} skipped, {failed} failed.")
    print(f"Images in {IMAGES_DIR}")


if __name__ == "__main__":
    main()
