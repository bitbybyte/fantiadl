#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download media and other data from Fantia"""

import requests

from urllib.parse import urljoin
import json
import mimetypes
import os
import re
import sys


class FantiaDownloader:
    ME_API = "https://fantia.jp/api/v1/me"
    FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
    FANCLUB_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"
    POST_API = "https://fantia.jp/api/v1/posts/{}"
    POSTS_URL = "https://fantia.jp/posts"
    POST_URL_RE = re.compile(r"href=['\"]\/posts\/([0-9]+)")

    def __init__(self, session_id, chunk_size=1024):
        self.session_id = session_id
        self.chunk_size = chunk_size
        self.session = requests.session()
        self.login()


    def login(self):
        session_cookie = {
            "_session_id" : self.session_id
        }
        requests.utils.add_dict_to_cookiejar(self.session.cookies, session_cookie)
        response = self.session.get(self.ME_API)
        if not response.status_code == 200:
            sys.exit("Invalid session key")


    def download_fanclub_posts(self, fanclub):
        post_ids = self.fetch_fanclub_posts(fanclub)
        for post_id in post_ids:
            self.download_post(post_id)


    def fetch_fanclub_posts(self, fanclub):
        all_posts = []
        page_number = 1
        while True:
            response = self.session.get(self.FANCLUB_HTML.format(fanclub.id, page_number))
            response.raise_for_status()
            post_ids = re.findall(self.POST_URL_RE, response.text)
            if not post_ids:
                return all_posts
            else:
                all_posts += post_ids
                page_number += 1


    def perform_download(self, url, filename):
        request = self.session.get(url, stream=True)
        request.raise_for_status()
        with open(filename, "wb") as file:
            for chunk in request.iter_content(self.chunk_size):
                file.write(chunk)


    def download_photo(self, photo, photo_counter, gallery_directory):
        download_url = photo["url"]["original"]
        photo_header = self.session.head(download_url)
        extension = mimetypes.guess_extension(photo_header.headers["Content-Type"], strict=True)
        filename = os.path.join(gallery_directory, str(photo_counter) + extension) if gallery_directory else str()
        self.perform_download(download_url, filename)


    def download_video(self, post, post_directory):
        filename = post["filename"]
        download_url = urljoin(self.POSTS_URL, post["download_uri"])
        self.perform_download(download_url, filename)


    def download_post_content(self, post_json, post_directory):
        if post_json["category"] == "photo_gallery":
            photo_gallery_title = post_json["title"]
            photo_gallery = post_json["post_content_photos"]
            photo_counter = 0
            gallery_directory = os.path.join(sanitize_for_path(post_directory), sanitize_for_path(photo_gallery_title))
            os.mkdir(gallery_directory)
            for photo in photo_gallery:
                self.download_photo(photo, photo_counter, gallery_directory)
                photo_counter += 1
        elif post_json["category"] == "file":
            self.download_video(post_json, post_directory)


    def download_post(self, post_id):
        response = self.session.get(self.POST_API.format(post_id))
        response.raise_for_status()
        post_json = json.loads(response.text)["post"]
        post_id = post_json["id"]
        print(post_id)
        post_title = post_json["title"]
        post_contents = post_json["post_contents"]
        post_directory = sanitize_for_path(str(post_id) + " - " + post_title)
        os.mkdir(post_directory)
        for post in post_contents:
            self.download_post_content(post, post_directory)


class FantiaClub:
    def __init__(self, fanclub_id):
        self.id = fanclub_id


def sanitize_for_path(value, replace=' '):
    """Remove potentially illegal characters from a path."""
    return re.sub(r'[<>\"\?\\\/\*:]', replace, value)


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        sys.exit("Usage: fantiadl.py [session_key] [fanclub_id]")

    downloader = FantiaDownloader(sys.argv[1])
    fanclub = FantiaClub(sys.argv[2])

    downloader.download_fanclub_posts(fanclub)
