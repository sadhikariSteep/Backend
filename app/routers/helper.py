import re
from typing import List
from markdown import markdown # type: ignore
from bs4 import BeautifulSoup, Tag
from markdown import markdown
from app.schemas.chat_schema import ContentBlock


def parse_markdown_to_blocks(ans: str) -> List[ContentBlock]:
    """Converts markdown text to HTML and structures it into blocks."""
    blocks = []
    
    # Extract <think> blocks using regex
    think_pattern = r'<think>(.*?)</think>'
    think_matches = re.finditer(think_pattern, ans, re.DOTALL)

    last_end = 0
    for match in think_matches:
        start, end = match.start(), match.end()

        # Add preceding text as a "text" block
        if start > last_end:
            text_part = ans[last_end:start]
            if text_part:
                text_part_with_br = text_part.replace('\n', '<br />')  # Replace newlines with <br />
                blocks.append(ContentBlock(type="text", content=markdown(text_part_with_br)))  # Convert to HTML

        # Add the "think" block (converted to HTML)
        think_content = match.group(1)
        think_content_with_br = think_content.replace('\n', '<br />')  # Replace newlines with <br />
        blocks.append(ContentBlock(type="think", content=markdown(think_content_with_br)))  # Convert to HTML

        last_end = end

    # Add remaining text as a "text" block
    if last_end < len(ans):
        text_part = ans[last_end:]
        if text_part:
            text_part_with_br = text_part.replace('\n', '<br />')  # Replace newlines with <br />
            blocks.append(ContentBlock(type="text", content=markdown(text_part_with_br)))  # Convert to HTML

    return blocks

