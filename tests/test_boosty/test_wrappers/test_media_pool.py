import pytest
from unittest.mock import patch, MagicMock
from boosty.wrappers.media_pool import MediaPool
from core.config import conf


class TestMediaPool:
    def setup_method(self):
        """Сбрасываем конфиг перед каждым тестом"""
        conf.need_load_photo = True
        conf.need_load_video = True
        conf.need_load_audio = True
        conf.need_load_files = True

    def test_initialization(self):
        """Тестирование инициализации пула"""
        pool = MediaPool()
        assert pool._MediaPool__images == {}
        assert pool._MediaPool__videos == {}
        assert pool._MediaPool__audios == {}
        assert pool._MediaPool__files == {}

    def test_add_image_basic(self):
        """Тестирование добавления изображения"""
        pool = MediaPool()
        pool.add_image("img1", "http://test.com/img1.jpg", 100, 200)

        assert "img1" in pool._MediaPool__images
        assert pool._MediaPool__images["img1"]["url"] == "http://test.com/img1.jpg"
        assert pool._MediaPool__images["img1"]["total_weight"] == 20000

    def test_add_image_when_photo_disabled(self):
        """Тестирование добавления изображения при отключенной загрузке фото"""
        conf.need_load_photo = False
        pool = MediaPool()
        pool.add_image("img1", "http://test.com/img1.jpg", 100, 200)

        assert pool._MediaPool__images == {}

    def test_add_image_with_lower_weight(self):
        """Тестирование добавления изображения с меньшим весом (не должно заменить существующее)"""
        pool = MediaPool()
        pool.add_image("img1", "http://test.com/high.jpg", 200, 200)  # 40000
        pool.add_image("img1", "http://test.com/low.jpg", 100, 100)  # 10000

        assert pool._MediaPool__images["img1"]["url"] == "http://test.com/high.jpg"
        assert pool._MediaPool__images["img1"]["total_weight"] == 40000

    def test_add_video_basic(self):
        """Тестирование добавления видео"""
        pool = MediaPool()
        test_meta = {"duration": 120}
        pool.add_video("vid1", "http://test.com/vid1.mp4", 500, test_meta)

        assert "vid1" in pool._MediaPool__videos
        assert pool._MediaPool__videos["vid1"]["url"] == "http://test.com/vid1.mp4"
        assert pool._MediaPool__videos["vid1"]["size_amount"] == 500
        assert pool._MediaPool__videos["vid1"]["meta"] == test_meta

    def test_add_video_when_video_disabled(self):
        """Тестирование добавления видео при отключенной загрузке видео"""
        conf.need_load_video = False
        pool = MediaPool()
        pool.add_video("vid1", "http://test.com/vid1.mp4", 500, {})

        assert pool._MediaPool__videos == {}

    def test_add_audio_basic(self):
        """Тестирование добавления аудио"""
        pool = MediaPool()
        pool.add_audio("aud1", "http://test.com/aud1.mp3", 300)

        assert "aud1" in pool._MediaPool__audios
        assert pool._MediaPool__audios["aud1"]["url"] == "http://test.com/aud1.mp3"
        assert pool._MediaPool__audios["aud1"]["size_amount"] == 300

    def test_add_file_basic(self):
        """Тестирование добавления файла"""
        pool = MediaPool()
        pool.add_file("file1", "http://test.com/file1.pdf", 1000, "Document.pdf")

        assert "file1" in pool._MediaPool__files
        assert pool._MediaPool__files["file1"]["url"] == "http://test.com/file1.pdf"
        assert pool._MediaPool__files["file1"]["size_amount"] == 1000
        assert pool._MediaPool__files["file1"]["title"] == "Document.pdf"

    def test_get_images(self):
        """Тестирование получения списка изображений"""
        pool = MediaPool()
        pool.add_image("img1", "http://test.com/img1.jpg", 100, 100)
        pool.add_image("img2", "http://test.com/img2.jpg", 200, 200)

        result = pool.get_images()
        assert len(result) == 2
        assert {"id": "img1", "url": "http://test.com/img1.jpg"} in result
        assert {"id": "img2", "url": "http://test.com/img2.jpg"} in result

    def test_get_videos(self):
        """Тестирование получения списка видео"""
        pool = MediaPool()
        test_meta = {"duration": 120}
        pool.add_video("vid1", "http://test.com/vid1.mp4", 500, test_meta)

        result = pool.get_videos()
        assert len(result) == 1
        assert result[0] == {
            "id": "vid1",
            "url": "http://test.com/vid1.mp4",
            "meta": test_meta
        }

    def test_get_audios(self):
        """Тестирование получения списка аудио"""
        pool = MediaPool()
        pool.add_audio("aud1", "http://test.com/aud1.mp3", 300)

        result = pool.get_audios()
        assert len(result) == 1
        assert result[0] == {
            "id": "aud1",
            "url": "http://test.com/aud1.mp3"
        }

    def test_get_files(self):
        """Тестирование получения списка файлов"""
        pool = MediaPool()
        pool.add_file("file1", "http://test.com/file1.pdf", 1000, "Document.pdf")

        result = pool.get_files()
        assert len(result) == 1
        assert result[0] == {
            "id": "file1",
            "url": "http://test.com/file1.pdf",
            "title": "Document.pdf"
        }
