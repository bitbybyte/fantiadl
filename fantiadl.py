#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download media and other data from Fantia"""

import requests

import json
import re
import sys

class FantiaDownloader:
    ME_API = "https://fantia.jp/api/v1/me"
    FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
    FANCLUB_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"
    POST_API = "https://fantia.jp/api/v1/posts/{}"
    POST_URL_RE = re.compile(r"href=['\"]\/posts\/([0-9]+)")

    def __init__(self, session_id):
        self.session_id = session_id
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


    def download_post(self, post_id):
        response = self.session.get(self.POST_API.format(post_id))
        response.raise_for_status()
        response_json = json.loads(response.text)
        print(json.dumps(response_json, sort_keys=True, indent=4))


class FantiaClub:
    def __init__(self, fanclub_id):
        self.id = fanclub_id


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        sys.exit("Usage: fantiadl.py [session_key] [fanclub_id]")

    downloader = FantiaDownloader(sys.argv[1])
    fanclub = FantiaClub(sys.argv[2])

    downloader.download_fanclub_posts(fanclub)
