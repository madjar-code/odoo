import re
import time
import requests
from typing import (
    Union,
    Dict,
    List,
    Optional,
)
from pydantic import HttpUrl
from abc import (
    ABC,
    abstractmethod,
)
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
from ...custom_types import (
    Message,
    PostObject,
    FieldName,
)


class PreparerInterface(ABC):
    @abstractmethod
    def check_image(self, image_path: Path) -> Message:
        pass

    @abstractmethod
    def check_text(self, text: str) -> Message:
        pass

    @abstractmethod
    def check_schedule_time(self, unix_timestamp: int) -> Message:
        pass

    @abstractmethod
    def transform_time(self, timestamp: str) -> int:
        pass

    @abstractmethod
    def analyze_post_data(self) ->\
            Optional[Dict[FieldName, Message]]:
        pass


class FacebookPreparer(PreparerInterface):
    TEXT_MAX_LENGTH = 63602
    MAX_LINK_QTY = 5
    MIN_TIMEDELTA_SECS = 600

    def __init__(self, post_data: PostObject) -> None:
        self._post_data = post_data
        self._errors: Dict[FieldName, List[str]] = dict()

    def check_image(self, image_id: int,
                    image_path: Union[Path, HttpUrl]) -> Message:
        try:
            if isinstance(image_path, Path):
                # create image object
                img = Image.open(image_path)
            elif isinstance(image_path, str) and\
                    image_path.startswith(('http://', 'https://')):
                # download image
                response = requests.get(image_path, timeout=1)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
            else:
                return Message(
                    success=False,
                    field_name='attach_images',
                    text=f'{image_id} - Invalid image path or URL'
                )

            img = Image.open(BytesIO(response.content))
            image_width, image_height = img.size
            image_size = len(response.content)
            image_format = img.format
            # check image parameters here
            return Message(
                success=True,
                field_name='attach_images',
                text=f'{image_id} - The image is correct'
            )

        except Exception as e:
            return Message(
                success=False,
                field_name='attach_images',
                text=f'{image_id} - Image not available'
            )

    def check_text(self, text: str) -> Message:
        if len(text) > self.TEXT_MAX_LENGTH:
            return Message(
                success=False,
                field_name='message',
                text='Post text too long'
            )
        return Message(
            success=True,
            field_name='message',
            text='Post text is correct'
        )

    def check_links(self, text: str) -> Message:
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)

        for i, url in enumerate(urls):
            if not self._is_url_valid(url):
                return Message(
                    success=False,
                    field_name='message',
                    text=f'Invalid URL: {url}'
                )
            if i > self.MAX_LINK_QTY:
                break

        return Message(
            success=True,
            field_name='message',
            text='All links in the post text are correct'
        )

    def _is_url_valid(self, url: HttpUrl) -> bool:
        try:
            response = requests.get(url)
            return response.status_code == 200
        except Exception as e:
            return False

    def check_schedule_time(self, unix_timestamp: int) -> Message:
        time_difference = unix_timestamp - int(time.time())
        if time_difference < self.MIN_TIMEDELTA_SECS:
            return Message(
                success=False,
                field_name='schedule_time',
                text='The post can be sent no earlier '\
                     'than 10 minutes from the current time'
            )
        return Message(
            success=True,
            field_name='schedule_time',
            text='UNIX timestamp is correct'
        )

    def transform_time(self, timestamp: str) -> int:
        date_format = '%Y-%m-%d %H:%M:%S'
        datetime_object = datetime.strptime(timestamp, date_format)
        unix_time_stamp = datetime_object.timestamp()
        return unix_time_stamp

    def analyze_post_data(self) -> Dict[FieldName, List[str]]:
        post_data = self._post_data
        if post_data.message:
            self._update_errors(self.check_text(post_data.message))
            self._update_errors(self.check_links(post_data.message))
        if not post_data.message and not post_data.image_objects:
            self._update_errors(
                Message(
                    success=False,
                    field_name='common_data',
                    text='No images and no message'
                )
            )
        # if post_data.schedule_time:
        #     unix_timestamp: int = self.transform_time(post_data.schedule_time)
        #     self._update_errors(self.check_schedule_time(unix_timestamp))
            # post_data.schedule_time = str(round(unix_timestamp))
        # if post_data.attach_images:
        #     for i, image_url in enumerate(post_data.attach_images):
        #         self._update_errors(self.check_image(i, image_url))
        return self._errors

    def _update_errors(self, message: Message) -> None:
        if not message.success:
            if message.field_name not in self._errors:
                self._errors[message.field_name] = []
            self._errors[message.field_name].append(message.text)

