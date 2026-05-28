# core/images/processors.py

from pathlib import Path

from PIL import Image

from core.images.defaults import (
    DEFAULT_BACKGROUND_COLOR,
    DEFAULT_IMAGE_FORMAT,
    DEFAULT_MAX_IMAGE_SIZE,
    DEFAULT_WEBP_QUALITY,
)


def normalize_image_mode(img):
    """
    Convert image to RGB safely.
    Prevent black background when converting transparent images.
    """

    if img.mode in ("RGB", "L"):
        return img

    if img.mode == "CMYK":
        return img.convert("RGB")

    if img.mode in ("RGBA", "LA"):
        rgba = img.convert("RGBA")

        background = Image.new(
            "RGB",
            rgba.size,
            DEFAULT_BACKGROUND_COLOR,
        )

        background.paste(
            rgba,
            mask=rgba.getchannel("A"),
        )

        return background

    if img.mode == "P":
        if "transparency" in img.info:
            rgba = img.convert("RGBA")

            background = Image.new(
                "RGB",
                rgba.size,
                DEFAULT_BACKGROUND_COLOR,
            )

            background.paste(
                rgba,
                mask=rgba.getchannel("A"),
            )

            return background

        return img.convert("RGB")

    return img.convert("RGB")


def process_image(
    source_path,
    dest_path=None,
    size=DEFAULT_MAX_IMAGE_SIZE,
    quality=DEFAULT_WEBP_QUALITY,
    image_format=DEFAULT_IMAGE_FORMAT,
):
    """
    Process image:
    - normalize color mode
    - resize
    - optimize
    - convert format

    If dest_path is None:
    overwrite source image.
    """

    source = Path(source_path)

    if not source.exists():
        raise FileNotFoundError(f"Source image not found: {source}")

    if dest_path:
        dest = Path(dest_path)
    else:
        dest = source

    dest.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    img = Image.open(source)

    img = normalize_image_mode(img)

    if size:
        if img.width > size[0] or img.height > size[1]:
            img.thumbnail(
                size,
                Image.Resampling.LANCZOS,
            )

    img.save(
        dest,
        format=image_format,
        optimize=True,
        quality=quality,
    )

    return str(dest)


def create_image_version(
    source_path,
    dest_path,
    size,
):
    """
    Create resized image version.
    """

    return process_image(
        source_path=source_path,
        dest_path=dest_path,
        size=size,
    )
