#!/usr/bin/env bash
# Rebuild assets/AppIcon.icns from assets/icon.svg, the icon's master copy.
#
# Only needed after editing assets/icon.svg: the compiled .icns is committed, so
# building or running the app never calls this script.
#
# No web browser is involved. macOS has no command-line SVG renderer, so this uses
# QuickLook (qlmanage) to rasterise, then Pillow to restore the transparent margin
# that QuickLook flattens onto white. Requires macOS and Pillow.
#
# That last point is learned the hard way: an earlier version of this script drove
# Google Chrome and cleared stale instances with `pkill -f "Google Chrome"`, which
# matched the developer's own browser window and closed it. This version starts and
# stops nothing but its own temporary files, and must stay that way.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."

[[ -f assets/icon.svg ]] || { echo "assets/icon.svg is missing." >&2; exit 1; }
for tool in qlmanage sips iconutil; do
  command -v "$tool" >/dev/null || { echo "$tool is required (macOS only)." >&2; exit 1; }
done

python_bin=""
for candidate in .venv/bin/python python3; do
  if [[ -x "$candidate" ]] || command -v "$candidate" >/dev/null 2>&1; then
    python_bin="$candidate"; break
  fi
done
[[ -n "$python_bin" ]] || { echo "python3 is required." >&2; exit 1; }
"$python_bin" -c 'import PIL' 2>/dev/null || {
  echo "Pillow is required to restore the icon's transparent margin:" >&2
  echo "  $python_bin -m pip install pillow" >&2
  exit 1
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# 1. Rasterise the master SVG at 1024. QuickLook composites onto opaque white.
qlmanage -t -s 1024 -o "$work" assets/icon.svg >/dev/null 2>&1
[[ -f "$work/icon.svg.png" ]] || { echo "QuickLook produced no thumbnail." >&2; exit 1; }

# 2. Restore the transparent margin by masking to the squircle in the SVG. The
#    geometry must match the <rect x="100" y="100" width="824" height="824"
#    rx="186"> in assets/icon.svg.
"$python_bin" - "$work/icon.svg.png" "$work/icon-1024.png" <<'PY'
import sys
from PIL import Image, ImageDraw

source, destination = sys.argv[1], sys.argv[2]
image = Image.open(source).convert("RGBA")
mask = Image.new("L", image.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([100, 100, 923, 923], radius=186, fill=255)
image.putalpha(mask)
image.save(destination)

# A macOS icon needs transparent corners or it shows as a white square in the Dock.
corner = image.getpixel((2, 2))
assert corner[3] == 0, f"corner is not transparent: {corner}"
assert image.size == (1024, 1024), image.size
print(f"masked icon: {image.size}, corner alpha {corner[3]}")
PY

# 3. Build the iconset macOS expects.
mkdir -p "$work/icon.iconset"
while read -r pixels name; do
  sips -z "$pixels" "$pixels" "$work/icon-1024.png" --out "$work/icon.iconset/$name.png" >/dev/null
done <<'SIZES'
16 icon_16x16
32 icon_16x16@2x
32 icon_32x32
64 icon_32x32@2x
128 icon_128x128
256 icon_128x128@2x
256 icon_256x256
512 icon_256x256@2x
512 icon_512x512
1024 icon_512x512@2x
SIZES

# 4. Compile and place it.
iconutil -c icns "$work/icon.iconset" -o assets/AppIcon.icns
echo "Wrote assets/AppIcon.icns from assets/icon.svg"
