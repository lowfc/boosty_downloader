import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

from core.dto.common import PostInfo

post_link_re = re.compile(r'https://boosty\.to/(.*)/posts/([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})', re.I)


def parse_post_link(post_link: str) -> Optional[PostInfo]:
    try:
        parsed_url = urlparse(post_link)
        clean_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            '',
            '',
            ''
        ))
    except Exception as e:
        print(e)
        return None
    result = post_link_re.match(clean_url)
    if result:
        return PostInfo(
            author=result.group(1),
            id=result.group(2)
        )
    return None
