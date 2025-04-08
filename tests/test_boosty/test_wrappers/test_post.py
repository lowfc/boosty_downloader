import pytest
from unittest.mock import patch
import json
from boosty.wrappers.post import Post
from core.logger import logger


class TestPost:
    def test_initialization(self):
        """Тестирование инициализации поста"""
        post = Post(_id="123", title="Test Post")
        assert post.id == "123"
        assert post.title == "Test Post"
        assert post.text_blocks == []
        assert post.markdown_text is False
        assert post.publish_time is None
        assert post._text_content_malformed is False

    def test_add_image(self):
        """Тестирование добавления изображения"""
        post = Post(_id="123", title="Test Post")
        with patch.object(post.media_pool, 'add_image') as mock_add_image:
            post.add_image("img1", "http://test.com/img1.jpg", 100, 200)
            mock_add_image.assert_called_once_with("img1", "http://test.com/img1.jpg", 100, 200)

    def test_add_video(self):
        """Тестирование добавления видео"""
        post = Post(_id="123", title="Test Post")
        with patch.object(post.media_pool, 'add_video') as mock_add_video:
            post.add_video("vid1", "http://test.com/vid1.mp4", 500)
            mock_add_video.assert_called_once_with("vid1", "http://test.com/vid1.mp4", 500, meta={})

    def test_parse_line_markdown(self):
        """Тестирование парсинга markdown текста"""
        post = Post(_id="123", title="Test Post", markdown_text=True)
        text = "sample text"
        codes = [[0, 0, 1]]  # bold at position 0
        result = post.parse_line_markdown(text, codes)
        assert result == "**s**ample text"

    @pytest.mark.parametrize("input_text,expected", [
        (json.dumps(["plain text", "unstyled", []]), "plain text"),
        (json.dumps(["", "unstyled", []]), None),
        (json.dumps("invalid format"), None),
    ])
    def test_unmarshal_text(self, input_text, expected):
        """Тестирование разбора текстового блока"""
        post = Post(_id="123", title="Test Post")
        with patch.object(logger, 'error') as mock_logger:
            result = post.unmarshal_text(input_text)
            assert result == expected
            if expected is None and input_text != json.dumps(["", "unstyled", []]):
                assert mock_logger.called

    def test_add_marshaled_text(self):
        """Тестирование добавления маршалированного текста"""
        post = Post(_id="123", title="Test Post")
        test_text = json.dumps(["test text", "unstyled", []])

        post.add_marshaled_text(test_text)
        assert post.text_blocks == ["test text"]
        assert post._text_content_malformed is False

        post.add_marshaled_text("invalid json")
        assert post._text_content_malformed is True

    def test_add_block_end(self):
        """Тестирование добавления разделителя блоков"""
        post = Post(_id="123", title="Test Post")
        post.add_block_end()
        assert post.text_blocks == ["\n\n"]

    @pytest.mark.parametrize("markdown,text,link,expected", [
        (True, json.dumps(["link text", "unstyled", []]), "http://test.com", "[link text](http://test.com)"),
        (False, json.dumps(["link text", "unstyled", []]), "http://test.com", "link text (ссылка: http://test.com)"),
        (False, "invalid json", "http://test.com", "http://test.com"),
    ])
    def test_add_link(self, markdown, text, link, expected):
        """Тестирование добавления ссылки"""
        post = Post(_id="123", title="Test Post", markdown_text=markdown)
        post.add_link(text, link)
        assert post.text_blocks == [expected]

    @pytest.mark.parametrize("markdown,title,texts,publish_time,expected", [
        (False, "Title", ["text1", "text2"], None, "Title\n-----\n\ntext1text2"),
        (True, "Title", ["text1", "text2"], None, "# Title\ntext1text2"),
        (False, "", ["text1"], 1640977200, "text1\n\n[Опубликовано 01.01.2022 00:00]\n"),
        (True, "", ["text1"], 1640977200, "text1\n\n---\n\n*Опубликовано 01.01.2022 00:00*\n"),
    ])
    def test_get_contents_text(self, markdown, title, texts, publish_time, expected):
        """Тестирование формирования итогового текста"""
        with patch('time.timezone', 0), \
                patch('datetime.datetime') as mock_datetime:

            if publish_time:
                mock_datetime.fromtimestamp.return_value.strftime.return_value = "01.01.2022 00:00"

            post = Post(_id="123", title=title, markdown_text=markdown, publish_time=publish_time)
            for text in texts:
                post.text_blocks.append(text)

            result = post.get_contents_text()
            assert result == expected
