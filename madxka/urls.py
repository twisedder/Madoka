from __future__ import annotations

SITE = "https://madxka.com"
API = f"{SITE}/apisite"


def catalog_item(item_id: int) -> str:
    return f"{SITE}/catalog/{int(item_id)}"


def user_profile(user_id: int) -> str:
    return f"{SITE}/users/{int(user_id)}/profile"


def group_page(group_id: int) -> str:
    return f"{SITE}/groups/{int(group_id)}/group"


def thumb_url(path: str) -> str:
    if path.startswith("http"):
        return path
    if path.startswith("/"):
        return f"{SITE}{path}"
    return f"{SITE}/{path}"
