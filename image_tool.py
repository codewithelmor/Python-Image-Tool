#!/usr/bin/env python3
"""
image_tool.py - Interactive image resizer / converter / compressor.

Everything is asked interactively:
  1. Source image path
  2. Resize? (by width, height or percentage)
  3. Convert to another image type?
  4. Compress? (only asked when you are NOT resizing)

The output is saved next to the source image, with the name of what was
changed appended to the file name, e.g.:

    photo.jpg -> photo_resized_800x600.jpg
    photo.jpg -> photo_compressed.jpg
    photo.jpg -> photo_converted.png
    photo.jpg -> photo_resized_50pct_converted.webp
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

# Target formats offered to the user: key -> (PIL format, file extension)
FORMATS = {
    "jpg": ("JPEG", ".jpg"),
    "jpeg": ("JPEG", ".jpg"),
    "png": ("PNG", ".png"),
    "webp": ("WEBP", ".webp"),
    "bmp": ("BMP", ".bmp"),
    "tiff": ("TIFF", ".tiff"),
    "tif": ("TIFF", ".tiff"),
    "gif": ("GIF", ".gif"),
}
MENU_FORMATS = ["jpg", "png", "webp", "bmp", "tiff", "gif"]

# Formats that support an adjustable quality setting
LOSSY_FORMATS = {"JPEG", "WEBP"}
# Formats that cannot store transparency
NO_ALPHA_FORMATS = {"JPEG", "BMP"}


# --------------------------------------------------------------------------- #
# Prompt helpers
# --------------------------------------------------------------------------- #
def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(0)


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = ask(f"{prompt} [{hint}]: ").lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("  Please answer y or n.")


def ask_number(prompt: str, minimum: float, maximum: float, as_int: bool = True):
    while True:
        raw = ask(prompt)
        try:
            value = float(raw)
        except ValueError:
            print("  Please enter a number.")
            continue
        if not (minimum <= value <= maximum):
            print(f"  Value must be between {minimum:g} and {maximum:g}.")
            continue
        return int(round(value)) if as_int else value


def ask_choice(prompt: str, options: list[str]) -> int:
    """Show a numbered menu, return the 0-based index chosen."""
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"  {i}) {option}")
    return ask_number("Choose: ", 1, len(options)) - 1


def ask_source_path() -> Path:
    while True:
        raw = ask("Path to the image file: ").strip("\"'")
        if not raw:
            continue
        path = Path(raw).expanduser()
        if not path.is_file():
            print("  File not found, try again.")
            continue
        try:
            with Image.open(path):
                pass
        except Exception:
            print("  That file is not a readable image, try again.")
            continue
        return path.resolve()


# --------------------------------------------------------------------------- #
# Interactive questions
# --------------------------------------------------------------------------- #
def ask_resize(width: int, height: int):
    """Return (new_size, label) or None if the user does not want to resize."""
    if not ask_yes_no("Resize the image?"):
        return None

    mode = ask_choice(
        "Resize by:", ["Width (keep aspect ratio)", "Height (keep aspect ratio)", "Percentage"]
    )
    if mode == 0:
        new_w = ask_number(f"New width in pixels (current {width}): ", 1, 100000)
        new_h = max(1, round(height * new_w / width))
    elif mode == 1:
        new_h = ask_number(f"New height in pixels (current {height}): ", 1, 100000)
        new_w = max(1, round(width * new_h / height))
    else:
        pct = ask_number("Percentage of original size (e.g. 50): ", 1, 1000, as_int=False)
        new_w = max(1, round(width * pct / 100))
        new_h = max(1, round(height * pct / 100))
        label = f"resized_{pct:g}pct"
        return (new_w, new_h), label

    return (new_w, new_h), f"resized_{new_w}x{new_h}"


def ask_convert(current_format: str | None):
    """Return (pil_format, extension) or None if the user does not want to convert."""
    if not ask_yes_no("Convert to a different image type?"):
        return None
    idx = ask_choice("Target image type:", [f.upper() for f in MENU_FORMATS])
    return FORMATS[MENU_FORMATS[idx]]


def ask_compress(pil_format: str):
    """Return a dict of compression settings, or None if not compressing."""
    if not ask_yes_no("Compress the image?"):
        return None

    if pil_format in LOSSY_FORMATS:
        quality = ask_number("Quality 1-100 (lower = smaller file, e.g. 70): ", 1, 100)
        return {"quality": quality}
    if pil_format == "PNG":
        print("  PNG is lossless; it will be re-saved with maximum compression.")
        reduce = ask_yes_no("  Also reduce to 256 colors for a much smaller file (lossy)?")
        return {"png_palette": reduce}
    print(f"  {pil_format} has no adjustable compression; saving with default settings.")
    return {}


# --------------------------------------------------------------------------- #
# Image processing
# --------------------------------------------------------------------------- #
def prepare_for_format(img: Image.Image, pil_format: str) -> Image.Image:
    """Make the image mode compatible with the target format."""
    if pil_format in NO_ALPHA_FORMATS and img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if pil_format in NO_ALPHA_FORMATS and img.mode != "RGB":
        return img.convert("RGB")
    if pil_format == "GIF" and img.mode not in ("P", "L"):
        return img.convert("P", palette=Image.ADAPTIVE)
    return img


def build_save_kwargs(pil_format: str, compression: dict | None) -> dict:
    kwargs: dict = {}
    if pil_format == "JPEG":
        kwargs.update(quality=95, optimize=True)
    elif pil_format == "WEBP":
        kwargs.update(quality=95)
    elif pil_format == "PNG":
        kwargs.update(optimize=True)

    if compression is not None:
        if pil_format in LOSSY_FORMATS:
            kwargs["quality"] = compression["quality"]
            if pil_format == "JPEG":
                kwargs.update(optimize=True, progressive=True)
        elif pil_format == "PNG":
            kwargs.update(optimize=True, compress_level=9)
    return kwargs


def unique_path(path: Path) -> Path:
    """Never overwrite an existing file: add _1, _2, ... if needed."""
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def process_image() -> None:
    source = ask_source_path()

    with Image.open(source) as opened:
        source_format = opened.format
        img = ImageOps.exif_transpose(opened)  # respect camera rotation
        img.load()

    width, height = img.size
    print(f"\nLoaded {source.name}: {width}x{height}, {source_format}, {human_size(source.stat().st_size)}\n")

    resize = ask_resize(width, height)
    convert = ask_convert(source_format)

    # Determine the output format (same as source unless converting)
    if convert:
        pil_format, extension = convert
    else:
        pil_format = source_format if source_format in {f for f, _ in FORMATS.values()} else "PNG"
        extension = source.suffix.lower() if source_format == pil_format else FORMATS[pil_format.lower()][1]

    # Compression is only offered when the user is not resizing
    compression = None
    if resize is None:
        compression = ask_compress(pil_format)

    if resize is None and convert is None and compression is None:
        print("\nNothing to do - no resize, conversion or compression selected.")
        return

    # Build the suffix describing what changed
    labels = []
    if resize:
        new_size, resize_label = resize
        img = img.resize(new_size, Image.LANCZOS)
        labels.append(resize_label)
    if compression is not None:
        labels.append("compressed")
    if convert:
        labels.append("converted")

    img = prepare_for_format(img, pil_format)
    if compression and compression.get("png_palette"):
        img = img.convert("RGBA" if "A" in img.getbands() else "RGB").quantize(
            colors=256, method=Image.FASTOCTREE if "A" in img.getbands() else Image.MEDIANCUT
        )

    output = unique_path(source.with_name(f"{source.stem}_{'_'.join(labels)}{extension}"))
    img.save(output, format=pil_format, **build_save_kwargs(pil_format, compression))

    print(f"\nSaved: {output}")
    print(f"Size : {img.size[0]}x{img.size[1]}, {human_size(output.stat().st_size)} "
          f"(original {human_size(source.stat().st_size)})")


def main() -> None:
    print("=== Image Tool: resize / convert / compress ===\n")
    while True:
        try:
            process_image()
        except Exception as exc:  # keep the interactive loop alive
            print(f"\nError: {exc}")
        print()
        if not ask_yes_no("Process another image?"):
            break
    print("Done.")


if __name__ == "__main__":
    main()
