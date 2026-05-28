# core/images/versions.py

IMAGE_VERSIONS = {
    "avatar_thumb": {
        "size": (50, 50),
        "crop": True,
        "folder": "resized_50x50_crop",
    },

    "avatar_medium": {
        "size": (200, 200),
        "crop": True,
        "folder": "resized_200x200_crop",
    },

    "product_thumb": {
        "size": (300, 300),
        "crop": False,
        "folder": "resized_300x300",
    },

    "product_medium": {
        "size": (800, 800),
        "crop": False,
        "folder": "resized_800x800",
    },
}