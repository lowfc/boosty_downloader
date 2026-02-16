import json
from typing import List, Union, Tuple

from core.boosty.defs import BoostyTextDto, BoostyLinkDto, BoostyListDto


class DraftJsConverter:
    STYLE_MAP = {
        0: "**",  # BOLD
        2: "*",  # ITALIC
        4: "__",  # UNDERLINE
    }

    BLOCK_TYPES = {
        "header": "## ",
        "header-one": "# ",
        "header-two": "## ",
        "header-three": "### ",
        "blockquote": "> ",
        "unordered-list-item": "* ",
        "ordered-list-item": "1. ",
    }

    def __init__(self, data: List[Union[BoostyTextDto, BoostyLinkDto, BoostyListDto]]):
        self.data = data

    def _parse_boosty_text(self, content_json: str) -> Tuple[str, str, list]:
        if content_json == "":
            return "", "unstyled", []
        try:
            data = json.loads(content_json)
            text = data[0]
            block_type = data[1]
            styles = data[2] if len(data) > 2 else []
            return text, block_type, styles
        except (json.JSONDecodeError, IndexError, TypeError):
            return "", "unstyled", []

    def _apply_markdown_styles(self, text: str, styles: list) -> str:
        if not styles:
            return text

        text_length = len(text)
        points = []
        for style_id, offset, length in styles:
            if offset > text_length:
                continue
            tag = self.STYLE_MAP.get(style_id, "")
            if tag:
                points.append((offset, tag))
                points.append((offset + length, tag))

        points.sort(key=lambda x: x[0], reverse=True)
        result_text = list(text)
        for pos, tag in points:
            result_text.insert(pos, tag)

        return "".join(result_text)

    def _process_list(self, list_dto: BoostyListDto, level: int = 0) -> List[str]:
        """Рекурсивно обрабатывает BoostyListDto."""
        lines = []
        prefix = "* "
        indent = "    " * level

        for item in list_dto.items:
            item_text_parts = []
            for text_dto in item.get("data", []):
                text, _, styles = self._parse_boosty_text(text_dto.get("content"))
                item_text_parts.append(self._apply_markdown_styles(text, styles))

            combined_text = "".join(item_text_parts)
            if combined_text:
                lines.append(f"{indent}{prefix}{combined_text}")

            if item.items:
                for sub_list in item.get("items", []):
                    lines.extend(self._process_list(sub_list, level + 1))
            lines.append("\n\n")
        return lines

    def to_markdown(self) -> str:
        result = []
        for item in self.data:
            if isinstance(item, BoostyLinkDto):
                text, b_type, styles = self._parse_boosty_text(item.content)
                formatted_text = self._apply_markdown_styles(text, styles)
                result.append(f"[{formatted_text}]({item.url})")

            elif isinstance(item, BoostyTextDto):
                if item.modificator == "BLOCK_END":
                    result.append("\n\n")
                else:
                    text, b_type, styles = self._parse_boosty_text(item.content)
                    formatted_text = self._apply_markdown_styles(text, styles)
                    prefix = self.BLOCK_TYPES.get(b_type, "")
                    result.append(f"{prefix}{formatted_text}")

            elif isinstance(item, BoostyListDto):
                list_lines = self._process_list(item)
                result.extend(list_lines)
        return "".join(result)

    def to_plain_text(self) -> str:
        result = []

        def process_plain_list(list_dto, level=0):
            lines = []
            indent = "  " * level
            for i in list_dto.items:
                text_parts = [self._parse_boosty_text(d.get("content"))[0] for d in i.get("data")]
                lines.append(f"{indent}- {''.join(text_parts)}")
                for sub in i.get("items"):
                    lines.extend(process_plain_list(sub, level + 1))
                lines.append("\n")
            return lines

        for item in self.data:
            if isinstance(item, BoostyLinkDto):
                text, _, _ = self._parse_boosty_text(item.content)
                result.append(f"{text} (ссылка: {item.url})")
            elif isinstance(item, BoostyTextDto):
                if item.modificator == "BLOCK_END":
                    result.append("\n")
                else:
                    text, _, _ = self._parse_boosty_text(item.content)
                    result.append(text)
            elif isinstance(item, BoostyListDto):
                result.extend(process_plain_list(item))
        return "".join(result)
