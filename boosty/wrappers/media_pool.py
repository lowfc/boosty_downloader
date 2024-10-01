from typing import List, Dict

from core.config import conf


class MediaPool:

    __images: dict
    __videos: dict
    __audios: dict

    def __init__(self):
        self.__videos = {}
        self.__images = {}
        self.__audios = {}

    def add_image(self, _id: str, url: str, width: int, height: int):
        if not conf.need_load_photo:
            return
        total_weight = width * height
        current = self.__images.get(_id)
        if current:
            if total_weight < current["total_weight"]:
                return
        self.__images[_id] = {
            "total_weight": total_weight,
            "url": url
        }

    def add_video(self, _id: str, url: str, size_amount: int):
        if not conf.need_load_video:
            return
        current = self.__videos.get(_id)
        if current:
            if size_amount < current["size_amount"]:
                return
        self.__videos[_id] = {
            "url": url,
            "size_amount": size_amount
        }

    def add_audio(self, _id: str, url: str, size_amount: int):
        if not conf.need_load_audio:
            return
        current = self.__audios.get(_id)
        if current:
            if size_amount < current["size_amount"]:
                return
        self.__audios[_id] = {
            "url": url,
            "size_amount": size_amount
        }

    def get_images(self) -> List[Dict]:
        """
        Get all images
        :return: [{"id": 1, "url": "https://s3.com/1"}, ...]
        """
        res = []
        for img_id in self.__images.keys():
            res.append(
                {
                    "id": img_id,
                    "url": self.__images[img_id]["url"]
                }
            )
        return res

    def get_videos(self) -> List[Dict]:
        """
        Get all videos
        :return: [{"id": 1, "url": "https://s3.com/1"}, ...]
        """
        res = []
        for video_id in self.__videos.keys():
            res.append(
                {
                    "id": video_id,
                    "url": self.__videos[video_id]["url"]
                }
            )
        return res

    def get_audios(self) -> List[Dict]:
        """
        Get all audios
        :return: [{"id": 1, "url": "https://s3.com/1"}, ...]
        """
        res = []
        for audio_id in self.__audios.keys():
            res.append(
                {
                    "id": audio_id,
                    "url": self.__audios[audio_id]["url"]
                }
            )
        return res
