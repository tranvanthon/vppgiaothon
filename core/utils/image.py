import logging

from PIL import Image, ImageOps

logger = logging.getLogger(__name__)


def normalize_image_mode(img):
    """
    Chuyển ảnh về RGB để lưu WEBP an toàn
    """

    if img.mode in ("RGB", "L"):
        return img

    if img.mode == "CMYK":
        return img.convert("RGB")

    if img.mode in ("RGBA", "LA", "PA"):

        rgba = img.convert("RGBA")

        background = Image.new(
            "RGB",
            rgba.size,
            (255, 255, 255),
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
                (255, 255, 255),
            )

            background.paste(
                rgba,
                mask=rgba.getchannel("A"),
            )

            return background

        return img.convert("RGB")

    return img.convert("RGB")


def resize_image(
    img,
    size,
    mode="thumbnail",
):
    """
    mode:
    thumbnail -> giữ tỷ lệ
    crop      -> cắt giữa ảnh
    pad       -> thêm nền
    """

    copy_img = img.copy()

    if mode == "thumbnail":

        copy_img.thumbnail(
            size,
            Image.Resampling.LANCZOS,
        )

        return copy_img

    if mode == "crop":

        return ImageOps.fit(
            copy_img,
            size,
            method=Image.Resampling.LANCZOS,
        )

    if mode == "pad":

        return ImageOps.pad(
            copy_img,
            size,
            method=Image.Resampling.LANCZOS,
            color=(255, 255, 255),
        )

    copy_img.thumbnail(
        size,
        Image.Resampling.LANCZOS,
    )

    return copy_img


def create_versions(
    source_path,
    thumb_path,
    medium_path,
    thumb_size=(300, 300),
    medium_size=(800, 800),
    thumb_quality=75,
    medium_quality=80,
    mode="crop",
):

    logger.debug(f"Processing {source_path}")

    img = Image.open(source_path)

    img = normalize_image_mode(img)

    thumb = resize_image(
        img,
        thumb_size,
        mode,
    )

    medium = resize_image(
        img,
        medium_size,
        "thumbnail",
    )

    thumb.save(
        thumb_path,
        format="WEBP",
        quality=thumb_quality,
        optimize=True,
    )

    medium.save(
        medium_path,
        format="WEBP",
        quality=medium_quality,
        optimize=True,
    )

    logger.info(f"Created {thumb_path}")

    logger.info(f"Created {medium_path}")
