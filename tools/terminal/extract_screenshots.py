#!/usr/bin/env python3
"""
extract_screenshots.py — OCR text extractor for screenshot libraries.

Extracts readable text from images using Tesseract OCR and compiles
the results into a single Markdown file for indexing or RAG pipelines.

Usage:
    python3 extract_screenshots.py --input ~/Downloads/Screenshots --output ~/output.md
    python3 extract_screenshots.py --input ~/Tech_Screenshots --output ~/output.md --append
    python3 extract_screenshots.py --input ~/Screenshots --output ~/output.md --filter Instagram

Requirements:
    sudo apt install tesseract-ocr -y
"""

from __future__ import annotations
import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime


def check_tesseract():
    """Verify Tesseract is installed before doing any work."""
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ Tesseract OCR is not installed.")
        print("   Install it with: sudo apt install tesseract-ocr -y")
        sys.exit(1)


def find_images(input_dir: str, name_filter: str | None) -> list[str]:
    """Collect all jpg/png images from the input directory, optionally filtered by filename."""
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.PNG"]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(os.path.join(input_dir, pattern)))

    if name_filter:
        images = [img for img in images if name_filter.lower() in os.path.basename(img).lower()]

    return sorted(images)


def extract_text_from_image(image_path: str) -> str:
    """Run Tesseract OCR on a single image, return cleaned text."""
    result = subprocess.run(
        ["tesseract", image_path, "stdout"],
        capture_output=True,
        text=True,
    )
    raw = result.stdout.strip()
    # Remove blank lines to reduce noise
    return "\n".join(line for line in raw.split("\n") if line.strip())


def run(input_dir: str, output_file: str, name_filter: str | None, append: bool):
    check_tesseract()

    input_dir = os.path.expanduser(input_dir)
    output_file = os.path.expanduser(output_file)

    if not os.path.isdir(input_dir):
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)

    images = find_images(input_dir, name_filter)
    if not images:
        filter_msg = f" matching '*{name_filter}*'" if name_filter else ""
        print(f"No images found{filter_msg} in: {input_dir}")
        sys.exit(0)

    print(f"🔍 Found {len(images)} image(s) in '{input_dir}'")
    if name_filter:
        print(f"   Filter applied: '{name_filter}'")

    mode = "a" if append else "w"
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    with open(output_file, mode, encoding="utf-8") as f:
        if not append:
            f.write("# 📱 Extracted Screenshot Knowledge Base\n\n")
            f.write(f"> Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            f.write(f" from `{input_dir}`\n\n")
            f.write("> Raw OCR output — parse and curate before adding to Library.\n\n---\n\n")
        else:
            f.write(f"\n\n---\n\n## 📂 Appended from: `{input_dir}`\n\n---\n\n")

        for idx, image_path in enumerate(images, 1):
            filename = os.path.basename(image_path)
            print(f"⏳ [{idx}/{len(images)}] {filename}")
            f.write(f"## `{filename}`\n\n")

            text = extract_text_from_image(image_path)
            if text:
                f.write(text + "\n\n")
            else:
                f.write("*[No readable text detected — image may be purely graphical.]*\n\n")

            f.write("---\n\n")

    action = "Appended to" if append else "Saved to"
    print(f"\n✅ Done! {action}: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="OCR extractor — pull text from screenshots into a Markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing screenshots to process.",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output Markdown file path.",
    )
    parser.add_argument(
        "--filter", "-f",
        default=None,
        metavar="KEYWORD",
        help="Only process images whose filename contains KEYWORD (e.g. 'Instagram', 'LinkedIn').",
    )
    parser.add_argument(
        "--append", "-a",
        action="store_true",
        help="Append to output file instead of overwriting it.",
    )

    args = parser.parse_args()
    run(args.input, args.output, args.filter, args.append)


if __name__ == "__main__":
    main()
