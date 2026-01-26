from aiohttp import ClientSession

from core.boosty.defs import BoostyPostDto, BoostyMediaType, BoostyImageDto, BoostyVideoDto, BoostyVideoSizesType, \
    BoostyPlayerUrlDto, BoostyAudioDto, BoostyFileDto, BoostyTextDto, BoostyLinkDto


class BoostyClient:

    def __init__(self,
        chunk_size: int,
        download_timeout: int,
        post_text_in_md: bool,
    ) -> None:
        self.chunk_size = chunk_size
        self.download_timeout = download_timeout
        self.base_url = "https://api.boosty.to"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",  # noqa: E501
            "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
        self.post_text_in_md = post_text_in_md

    def get_client_session(self) -> ClientSession:
        return ClientSession(headers=self.headers)

    async def get_post_info(self, author: str, post_id: str) -> BoostyPostDto:
        url = self.base_url + f"/v1/blog/{author}/post/{post_id}"
        async with self.get_client_session() as session:
            response = await session.get(url)
            response.raise_for_status()
            content = await response.json()
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
                    result.media.append(BoostyImageDto(
                        id=media["id"],
                        url=media["url"],
                        width=media["width"],
                        height=media["height"],
                        size=media["size"],
                    ))
                case BoostyMediaType.VIDEO.value:
                    video = BoostyVideoDto()
                    for url in media["playerUrls"]:
                        if url["url"] != "":
                            size = BoostyVideoSizesType(url["type"])
                            video.player_urls[size] = BoostyPlayerUrlDto(
                                id=url["id"],
                                url=url["url"],
                                size=size,
                            )
                    result.media.append(video)
                case BoostyMediaType.AUDIO.value:
                    result.media.append(BoostyAudioDto(
                        id=media["id"],
                        url=media["url"],
                        size=media["size"],
                    ))
                case BoostyMediaType.FILE.value:
                    result.media.append(BoostyFileDto(
                        id=media["id"],
                        url=media["url"],
                        size=media["size"],
                        title=media["title"],
                    ))
                case BoostyMediaType.TEXT.value:
                    result.media.append(BoostyTextDto(
                        content=media["content"],
                        modificator=media["modificator"],
                    ))
                case BoostyMediaType.LINK.value:
                    result.media.append(BoostyLinkDto(
                        content=media["content"],
                        url=media["url"],
                    ))

        return result
