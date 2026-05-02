from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "profile-icons"
README_PATH = REPO_ROOT / "README.md"

CONNECT_START = "<!-- icons:connect:start -->"
CONNECT_END = "<!-- icons:connect:end -->"
TOOLS_START = "<!-- icons:tools:start -->"
TOOLS_END = "<!-- icons:tools:end -->"

DEVICON_BASE = "https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons"
SOCIAL_ICON_ALIASES = {
    "x": "twitter",
}
URL_VARIANT_PATTERN = re.compile(
    r"^(?P<base>.+)_(?P<variant>white|black)(?P<tail>(?:\.[^/?#]+)?(?:[?#].*)?)$",
    re.IGNORECASE,
)
PX_MARGIN_PATTERN = re.compile(r"^(?P<value>\d+(?:\.\d+)?)px$", re.IGNORECASE)
REM_MARGIN_PATTERN = re.compile(r"^(?P<value>\d+(?:\.\d+)?)rem$", re.IGNORECASE)
EM_MARGIN_PATTERN = re.compile(r"^(?P<value>\d+(?:\.\d+)?)em$", re.IGNORECASE)
NUMBER_MARGIN_PATTERN = re.compile(r"^\d+(?:\.\d+)?$")


def is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


@dataclass
class IconItem:
    name: str
    source: str
    link: str | None
    variant: str | None


def split_icon_variant(name: str) -> tuple[str, str | None]:
    if is_url(name):
        match = URL_VARIANT_PATTERN.match(name)
        if match:
            variant = match.group("variant").lower()
            base = match.group("base")
            tail = match.group("tail")
            return f"{base}{tail}", variant
        return name, None

    normalized = name.lower()
    if normalized.endswith("_white") and len(normalized) > len("_white"):
        return normalized[: -len("_white")], "white"
    if normalized.endswith("_black") and len(normalized) > len("_black"):
        return normalized[: -len("_black")], "black"

    return normalized, None


def parse_config(config_text: str) -> tuple[list[IconItem], list[IconItem], str | None, str | None]:
    section = ""
    connect: list[IconItem] = []
    tools: list[IconItem] = []
    global_margin: str | None = None
    connect_margin: str | None = None
    tools_margin: str | None = None

    for raw_line in config_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            continue

        if section == "options" and "=" in line:
            key, raw_value = line.split("=", 1)
            normalized_key = key.strip().lower().replace("-", "_")
            margin_value = normalize_margin(raw_value.strip())
            if normalized_key == "margin":
                global_margin = margin_value
            elif normalized_key == "connect_margin":
                connect_margin = margin_value
            elif normalized_key == "tools_margin":
                tools_margin = margin_value
            continue

        if section not in {"connectwithme", "languagesandtools"}:
            continue

        if "=" in line:
            raw_name, raw_url = line.split("=", 1)
            raw_name = raw_name.strip()
            raw_url = raw_url.strip()
            parsed_name, variant = split_icon_variant(raw_name)
            url = raw_url or None
        else:
            raw_name = line.strip()
            parsed_name, variant = split_icon_variant(raw_name)
            url = None

        source = raw_name if is_url(raw_name) else parsed_name
        name = parsed_name

        if not name:
            continue

        if section == "connectwithme":
            connect.append(IconItem(name=name, source=source, link=url, variant=variant))
        else:
            tools.append(IconItem(name=name, source=source, link=url, variant=variant))

    if connect_margin is None:
        connect_margin = global_margin
    if tools_margin is None:
        tools_margin = global_margin

    return connect, tools, connect_margin, tools_margin


def normalize_margin(value: str) -> str | None:
    raw = value.strip().lower()
    if not raw:
        return None
    if raw == "0":
        return "0"

    if NUMBER_MARGIN_PATTERN.fullmatch(raw):
        return to_px_int(float(raw))

    px_match = PX_MARGIN_PATTERN.fullmatch(raw)
    if px_match:
        return to_px_int(float(px_match.group("value")))

    rem_match = REM_MARGIN_PATTERN.fullmatch(raw)
    if rem_match:
        return to_px_int(float(rem_match.group("value")) * 16)

    em_match = EM_MARGIN_PATTERN.fullmatch(raw)
    if em_match:
        return to_px_int(float(em_match.group("value")) * 16)

    return None


def to_px_int(value: float) -> str:
    return str(max(0, round(value)))


def icon_url(name: str, variant: str | None = None) -> str:
    if is_url(name):
        return name

    icon_name = SOCIAL_ICON_ALIASES.get(name, name)
    if variant == "white":
        return f"{DEVICON_BASE}/{icon_name}/{icon_name}-original-white.svg"

    return f"{DEVICON_BASE}/{icon_name}/{icon_name}-original.svg"


def icon_alt(name: str) -> str:
    if is_url(name):
        return "custom icon"

    return name


def resolve_source(item: IconItem | None, preferred_variant: str | None) -> str | None:
    if item is None:
        return None
    if is_url(item.source):
        return item.source

    variant = item.variant or preferred_variant
    return icon_url(item.source, variant)


def image_spacing_attr(margin: str | None) -> str:
    if not margin or margin == "0":
        return ""
    return f' hspace="{margin}" vspace="{margin}"'


def image_behavior_attr(disable_click: bool) -> str:
    if not disable_click:
        return ""
    return ' style="pointer-events: none;"'


def build_theme_aware_image_from_items(
    name: str,
    default_item: IconItem | None,
    white_item: IconItem | None,
    black_item: IconItem | None,
    margin: str | None,
    disable_click: bool = False,
) -> str:
    has_white = white_item is not None
    has_black = black_item is not None
    behavior_attr = image_behavior_attr(disable_click)

    if not has_white and not has_black:
        default_src = resolve_source(default_item, None) or icon_url(name)
        return f"<img src=\"{default_src}\" width=\"40\" height=\"40\" alt=\"{icon_alt(name)}\"{image_spacing_attr(margin)}{behavior_attr} />"

    dark_src = resolve_source(white_item, "white") or resolve_source(default_item, "white") or resolve_source(black_item, "black")
    light_src = resolve_source(black_item, "black") or resolve_source(default_item, "black") or resolve_source(white_item, "white")

    if dark_src is None or light_src is None:
        fallback_src = resolve_source(default_item, None) or icon_url(name)
        return f"<img src=\"{fallback_src}\" width=\"40\" height=\"40\" alt=\"{icon_alt(name)}\"{image_spacing_attr(margin)}{behavior_attr} />"

    return (
        "<picture>"
        f"<source media=\"(prefers-color-scheme: dark)\" srcset=\"{dark_src}\" />"
        f"<source media=\"(prefers-color-scheme: light)\" srcset=\"{light_src}\" />"
        f"<img src=\"{light_src}\" width=\"40\" height=\"40\" alt=\"{icon_alt(name)}\"{image_spacing_attr(margin)}{behavior_attr} />"
        "</picture>"
    )


def build_items_html(items: list[IconItem], margin: str | None = None, disable_click: bool = False) -> list[str]:
    grouped: dict[tuple[str, str | None], dict[str, IconItem | None]] = {}
    order: list[tuple[str, str | None]] = []

    for item in items:
        key = (item.name, item.link)
        if key not in grouped:
            grouped[key] = {"default": None, "white": None, "black": None}
            order.append(key)
        if item.variant in {"white", "black"}:
            grouped[key][item.variant] = item
        else:
            grouped[key]["default"] = item

    rendered_items: list[str] = []
    for name, link in order:
        item_group = grouped[(name, link)]
        disable_click_for_item = disable_click and not bool(link)
        image = build_theme_aware_image_from_items(
            name,
            default_item=item_group["default"],
            white_item=item_group["white"],
            black_item=item_group["black"],
            margin=margin,
            disable_click=disable_click_for_item,
        )
        if link:
            rendered_items.append(f"[{image}]({link})")
        else:
            rendered_items.append(image)

    # Keep the section as one Markdown paragraph so GitHub renders icons inline.
    return [" &nbsp; ".join(rendered_items)]


def build_connect_html(items: list[IconItem], margin: str | None = None) -> list[str]:
    return build_items_html(items, margin=margin)


def build_tools_html(items: list[IconItem], margin: str | None = None) -> list[str]:
    return build_items_html(items, margin=margin, disable_click=True)


def replace_marked_block(readme_text: str, start_marker: str, end_marker: str, block_lines: list[str]) -> str:
    start_index = readme_text.find(start_marker)
    end_index = readme_text.find(end_marker)

    if start_index == -1 or end_index == -1 or end_index < start_index:
        raise ValueError(f"Missing README markers: {start_marker} ... {end_marker}")

    before = readme_text[: start_index + len(start_marker)]
    after = readme_text[end_index:]
    block = "\n" + "\n".join(block_lines) + "\n"
    return before + block + after


def main() -> None:
    config_text = CONFIG_PATH.read_text(encoding="utf-8")
    readme_text = README_PATH.read_text(encoding="utf-8")

    connect_items, tool_items, connect_margin, tools_margin = parse_config(config_text)
    connect_html = build_connect_html(connect_items, margin=connect_margin)
    tools_html = build_tools_html(tool_items, margin=tools_margin)

    updated = replace_marked_block(readme_text, CONNECT_START, CONNECT_END, connect_html)
    updated = replace_marked_block(updated, TOOLS_START, TOOLS_END, tools_html)

    if updated != readme_text:
        README_PATH.write_text(updated, encoding="utf-8")
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
