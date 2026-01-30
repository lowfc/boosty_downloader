from typing import Optional

from aiohttp import ClientSession

from core.boosty.defs import BoostyPostDto, BoostyMediaType, BoostyImageDto, BoostyVideoDto, BoostyVideoSizesType, \
    BoostyPlayerUrlDto, BoostyAudioDto, BoostyFileDto, BoostyTextDto, BoostyLinkDto, VIDEO_QUALITY_GRADE, \
    BoostyPostTextDto, BoostyListDto
from core.defs.common import AuthToken


class BoostyClient:

    def __init__(self,
        chunk_size: int,
        download_timeout: int,
        post_text_in_md: bool,
        auth_token: Optional[AuthToken] = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.download_timeout = download_timeout
        self.base_url = "https://api.boosty.to"
        self._base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",  # noqa: E501
            "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
        self.post_text_in_md = post_text_in_md
        self.auth_token = auth_token

    def _get_headers(self) -> dict:
        if self.auth_token:
            return {
                **self._base_headers,
                "Authorization": f"Bearer {self.auth_token.authorization}",
                "Cookie": self.auth_token.cookie

            }
        return self._base_headers

    def get_client_session(self) -> ClientSession:
        return ClientSession(headers=self._get_headers())

    async def get_post_info(self, author: str, post_id: str) -> BoostyPostDto:
        url = self.base_url + f"/v1/blog/{author}/post/{post_id}"
        async with self.get_client_session() as session:
            response = await session.get(url)
            response.raise_for_status()
            content = await response.json()

        text_content = BoostyPostTextDto()
        result = BoostyPostDto(
            has_access=content["hasAccess"],
            id=content["id"],
            title=content["title"],
            publish_time=content["publishTime"],
            signed_query=content["signedQuery"],
        )

        for media in content["data"]:
            match media["type"]:
                case BoostyMediaType.IMAGE.value:
                    if "width" not in media:  # issues/30 "узкая" картинка
                        continue
                    result.media.append(BoostyImageDto(
                        id=media["id"],
                        url=media["url"],
                        width=media["width"],
                        height=media["height"],
                        size=media["size"],
                    ))
                case BoostyMediaType.VIDEO.value:
                    video = BoostyVideoDto(id=media["id"], title=media["title"])
                    for url in media["playerUrls"]:
                        if url["url"] != "" and url["type"] in VIDEO_QUALITY_GRADE:
                            size = BoostyVideoSizesType(url["type"])
                            video.player_urls[size] = BoostyPlayerUrlDto(
                                url=url["url"],
                                size=size,
                            )
                    result.media.append(video)
                case BoostyMediaType.AUDIO.value:
                    result.media.append(BoostyAudioDto(
                        id=media["id"],
                        url=media["url"],
                        size=media["size"],
                        title=media["title"],
                    ))
                case BoostyMediaType.FILE.value:
                    result.media.append(BoostyFileDto(
                        id=media["id"],
                        url=media["url"],
                        size=media["size"],
                        title=media["title"],
                    ))
                case BoostyMediaType.TEXT.value | BoostyMediaType.HEADER.value:
                    text_content.content.append(BoostyTextDto(
                        content=media["content"],
                        modificator=media["modificator"],
                    ))
                case BoostyMediaType.LINK.value:
                    text_content.content.append(BoostyLinkDto(
                        content=media["content"],
                        url=media["url"],
                    ))
                case BoostyMediaType.LIST.value:
                    text_content.content.append(BoostyListDto(
                        style=media["style"],
                        items=media["items"],
                    ))

        result.text_content = text_content
        return result
