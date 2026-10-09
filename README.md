# Image Tool

An interactive command-line tool to **resize**, **convert** and **compress** images. Every option is asked interactively, so there are no flags to remember.

## Features

- **Resize** by width, height (aspect ratio preserved) or percentage
- **Convert** to another image type: JPG, PNG, WEBP, BMP, TIFF, GIF
- **Compress** an image when you don't want to resize it
- Output is saved **next to the source image**, and the file name is suffixed with what changed
- Never overwrites an existing file (adds `_1`, `_2`, ... if needed)
- Respects camera (EXIF) rotation and handles transparency when converting to JPG/BMP (white background)

## Requirements

- Python 3.9+
- [Pillow](https://python-pillow.org/)

## Installation

It is recommended to install the dependencies inside a virtual environment so they don't affect your global Python install.

### 1. Create the virtual environment

From the project folder (where `image_tool.py` lives):

```bash
python -m venv .venv
```

> On macOS/Linux you may need to use `python3` instead of `python`.

### 2. Activate the virtual environment

| Shell                   | Command                            |
|-------------------------|------------------------------------|
| Windows (PowerShell)    | `.venv\Scripts\Activate.ps1`       |
| Windows (cmd)           | `.venv\Scripts\activate.bat`       |
| macOS / Linux (bash/zsh)| `source .venv/bin/activate`        |

Once active, your prompt is prefixed with `(.venv)`.

> **PowerShell tip:** if activation is blocked by the execution policy, run this once for your user and try again:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### 3. Install the requirements

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Deactivate when finished (optional)

```bash
deactivate
```

The next time you use the tool, you only need to activate the environment again (step 2); there is no need to reinstall.

## Usage

Make sure the virtual environment is activated (see [Installation](#installation)), then run:

```bash
python image_tool.py
```

The tool then asks, in order:

1. **Path to the image file** (quotes are fine, e.g. when dragging a file into the terminal)
2. **Resize the image?**
   - By width, height or percentage
3. **Convert to a different image type?**
   - Pick the target type from the menu
4. **Compress the image?** (only asked if you chose *not* to resize)
   - JPG / WEBP: choose a quality from 1 to 100
   - PNG: lossless re-compression, with an optional reduction to 256 colors for a much smaller file
5. **Process another image?**

### Example session

```text
=== Image Tool: resize / convert / compress ===

Path to the image file: C:\Photos\holiday.jpg

Loaded holiday.jpg: 4000x3000, JPEG, 5.2 MB

Resize the image? [y/N]: n
Convert to a different image type? [y/N]: y
Target image type:
  1) JPG
  2) PNG
  3) WEBP
  ...
Choose: 3
Compress the image? [y/N]: y
Quality 1-100 (lower = smaller file, e.g. 70): 75

Saved: C:\Photos\holiday_compressed_converted.webp
Size : 4000x3000, 640.3 KB (original 5.2 MB)
```

## Output file naming

The output is written to the same folder as the source, with the changes appended to the name:

| Action                    | Source        | Output                                |
|---------------------------|---------------|---------------------------------------|
| Resize by width/height    | `photo.jpg`   | `photo_resized_800x600.jpg`           |
| Resize by percentage      | `photo.jpg`   | `photo_resized_50pct.jpg`             |
| Compress only             | `photo.jpg`   | `photo_compressed.jpg`                |
| Convert only              | `photo.jpg`   | `photo_converted.png`                 |
| Resize + convert          | `photo.jpg`   | `photo_resized_50pct_converted.webp`  |
| Compress + convert        | `photo.png`   | `photo_compressed_converted.jpg`      |

## Notes

- Compression is only offered when you don't resize, as resizing already reduces file size.
- Animated GIFs are saved as a single frame.
- BMP, TIFF and GIF have no adjustable quality, so "compress" re-saves them with default settings.
- Converting transparent images to JPG/BMP flattens them onto a white background.
