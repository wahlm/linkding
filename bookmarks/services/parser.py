import json
import logging
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Dict, List

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

@dataclass
class NetscapeBookmark:
    href: str
    title: str
    description: str
    date_added: str
    tag_string: str


class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bookmarks = []

        self.current_tag = None
        self.bookmark = None
        self.href = ''
        self.add_date = ''
        self.tags = ''
        self.title = ''
        self.description = ''

    def handle_starttag(self, tag: str, attrs: list):
        name = 'handle_start_' + tag.lower()
        if name in dir(self):
            getattr(self, name)({k.lower(): v for k, v in attrs})
        self.current_tag = tag

    def handle_endtag(self, tag: str):
        name = 'handle_end_' + tag.lower()
        if name in dir(self):
            getattr(self, name)()
        self.current_tag = None

    def handle_data(self, data):
        name = f'handle_{self.current_tag}_data'
        if name in dir(self):
            getattr(self, name)(data)

    def handle_end_dl(self):
        self.add_bookmark()

    def handle_start_dt(self, attrs: Dict[str, str]):
        self.add_bookmark()

    def handle_start_a(self, attrs: Dict[str, str]):
        vars(self).update(attrs)
        self.bookmark = NetscapeBookmark(
            href=self.href,
            title='',
            description='',
            date_added=self.add_date,
            tag_string=self.tags,
        )

    def handle_a_data(self, data):
        self.title = data.strip()

    def handle_dd_data(self, data):
        self.description = data.strip()

    def add_bookmark(self):
        if self.bookmark:
            self.bookmark.title = self.title
            self.bookmark.description = self.description
            self.bookmarks.append(self.bookmark)
        self.bookmark = None
        self.href = ''
        self.add_date = ''
        self.tags = ''
        self.title = ''
        self.description = ''


def parse(html: str) -> List[NetscapeBookmark]:
    parser = BookmarkParser()
    parser.feed(html)
    return parser.bookmarks


def grab_keys(bookmarks_data, bookmarks_list, path):
    title = bookmarks_data['title']
    code = bookmarks_data['typeCode']
    if code == 2 and title != '':
        path.append(title)
    if 'children' in bookmarks_data:
        for item in bookmarks_data['children']:
            code = item.get('typeCode')
            url = item.get('uri', None)
            if code == 1 and url is not None:
                val = URLValidator()
                try:
                    val(url)
                    tags = item.get('tags', '')
                    tag_path = ''
                    for tag in path:
                        if tags != '':
                            tags = tags + ','
                        tags = tags + tag
                        if tag_path != '':
                            tag_path = tag_path + ';'
                        else:
                            tag_path = '/p/'
                        tag_path = tag_path + tag
                    if tag_path != '':
                        tags = tags + ',' + tag_path
                    bookmark = NetscapeBookmark(
                        href=url,
                        title=item.get('title', '')[:512],
                        description='',
                        date_added=item.get('dateAdded', 0),
                        tag_string=tags,
                    )
                    bookmarks_list.append(bookmark)
                except ValidationError as e:
                    logging.warning(f"URL ignored: {url}")
            work_path = path.copy()
            grab_keys(item, bookmarks_list, work_path)
    return bookmarks_list


def json_parse(html: str) -> List[NetscapeBookmark]:
    bookmarks = []
    path = []
    json_dict = json.loads(html)
    grab_keys(json_dict, bookmarks, path)
    return bookmarks
