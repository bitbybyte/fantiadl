#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

from urllib.parse import urljoin
from urllib.parse import unquote
import json
import mimetypes
import os
import re
import sys
import traceback


class FantiaDownloader:
    FANTIA_URL_RE = re.compile(r"(?:https?://(?:(?:www\.)?(?:fantia\.jp/(fanclubs|posts)/)))([0-9]+)")
    EXTERNAL_LINKS_RE = re.compile(r"(?:[\s]+)?((?:(?:https?://)?(?:(?:www\.)?(?:mega\.nz|mediafire\.com|(?:drive|docs)\.google\.com|youtube.com)\/))[^\s]+)")

    LOGIN_URL = "https://fantia.jp/auth/login"
    LOGIN_CALLBACK_URL = "https://fantia.jp/auth/toranoana/callback?code={}&state={}"

    ME_API = "https://fantia.jp/api/v1/me"

    FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
    FANCLUB_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"

    POST_API = "https://fantia.jp/api/v1/posts/{}"
    POST_URL = "https://fantia.jp/posts"
    POST_URL_RE = re.compile(r"href=['\"]\/posts\/([0-9]+)")

    MIMETYPES = {
        "image/jpeg" : ".jpg",
        "image/png" : ".png",
        "image/gif" : ".gif",
        "video/mp4" : ".mp4",
        "video/webm" : ".webm"
    }

    def __init__(self, email, password, chunk_size=1024*1024*5, dump_metadata=False, parse_for_external_links=False, autostart_crawljob=False, download_thumb=False, directory=None, quiet=True, continue_on_error=False):
        self.email = email
        self.password = password
        self.chunk_size = chunk_size
        self.dump_metadata = dump_metadata
        self.parse_for_external_links = parse_for_external_links
        self.autostart_crawljob = autostart_crawljob
        self.download_thumb = download_thumb
        self.directory = directory or ""
        self.quiet = quiet
        self.continue_on_error = continue_on_error
        self.session = requests.session()
        self.login()

    def output(self, output):
        if not self.quiet:
            sys.stdout.write(output)
            sys.stdout.flush()

    def login(self):
        login = self.session.get(self.LOGIN_URL)
        auth_url = login.url.replace("id.fantia.jp/auth/", "id.fantia.jp/authorize")

        login_json = {
            "Email": self.email,
            "Password": self.password
        }

        login_headers = {
            "X-Not-Redirection": "true"
        }

        auth_response = self.session.post(auth_url, json=login_json, headers=login_headers).json()
        if auth_response["status"] == "OK":
            auth_payload = auth_response["payload"]

            callback = self.session.get(self.LOGIN_CALLBACK_URL.format(auth_payload["code"], auth_payload["state"]))
            if not callback.cookies["_session_id"]:
                sys.exit("Error: Failed to retrieve session key from callback")

            check_user = self.session.get(self.ME_API)
            if not check_user.status_code == 200:
                sys.exit("Error: Invalid session")
        else:
            sys.exit("Error: Failed to login. Please verify your username and password")

    def download_fanclub_posts(self, fanclub, limit=0):
        post_ids = self.fetch_fanclub_posts(fanclub)
        for post_id in post_ids if limit == 0 else post_ids[:limit]:
            try:
                self.download_post(post_id)
            except KeyboardInterrupt:
                raise
            except:
                if self.continue_on_error:
                    self.output("Encountered an error downloading post. Skipping...\n")
                    traceback.print_exc()
                    continue
                else:
                    raise

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

    def perform_download(self, url, filename, server_filename=False):
        request = self.session.get(url, stream=True)
        request.raise_for_status()

        if server_filename:
            filename = os.path.join(os.path.dirname(filename), os.path.basename(unquote(request.url.split("?", 1)[0])))

        file_size = int(request.headers["Content-Length"])
        if os.path.isfile(filename):
            if os.stat(filename).st_size == file_size:
                self.output("File found (skipping): {}\n".format(filename))
                return

        self.output("File: {}\n".format(filename))

        downloaded = 0
        with open(filename, "wb") as file:
            for chunk in request.iter_content(self.chunk_size):
                downloaded += len(chunk)
                file.write(chunk)
                done = int(25 * downloaded / file_size)
                percent = int(100 * downloaded / file_size)
                self.output("\r|{0}{1}| {2}% ".format("\u2588" * done, " " * (25 - done), percent))
        self.output("\n")

    def download_photo(self, photo, photo_counter, gallery_directory):
        download_url = photo["url"]["original"]
        photo_header = self.session.head(download_url)
        mimetype = photo_header.headers["Content-Type"]
        extension = self.MIMETYPES.get(mimetype) or mimetypes.guess_extension(mimetype, strict=True)
        filename = os.path.join(gallery_directory, str(photo_counter) + extension) if gallery_directory else str()
        self.perform_download(download_url, filename)

    def download_video(self, post, post_directory):
        filename = os.path.join(post_directory, post["filename"])
        download_url = urljoin(self.POST_URL, post["download_uri"])
        self.perform_download(download_url, filename, server_filename=True)

    def download_post_content(self, post_json, post_directory):
        if post_json.get("category") == "photo_gallery":
            photo_gallery_title = post_json["title"]
            if not photo_gallery_title:
                photo_gallery_title = str(post_json["id"])
            photo_gallery = post_json["post_content_photos"]
            photo_counter = 0
            gallery_directory = os.path.join(post_directory, sanitize_for_path(photo_gallery_title))
            os.makedirs(gallery_directory, exist_ok=True)
            for photo in photo_gallery:
                self.download_photo(photo, photo_counter, gallery_directory)
                photo_counter += 1
        elif post_json.get("category") == "file":
            self.download_video(post_json, post_directory)

    def download_thumbnail(self, thumb_url, post_directory):
        thumb_header = self.session.head(thumb_url)
        extension = mimetypes.guess_extension(thumb_header.headers["Content-Type"], strict=True)
        filename = os.path.join(post_directory, "thumb" + extension)
        self.perform_download(thumb_url, filename)

    def download_post(self, post_id):
        response = self.session.get(self.POST_API.format(post_id))
        response.raise_for_status()
        post_json = json.loads(response.text)["post"]
        post_id = post_json["id"]
        post_creator = post_json["fanclub"]["creator_name"]
        self.output("Downloading post {}...\n".format(post_id))
        post_title = post_json["title"]
        post_contents = post_json["post_contents"]
        post_description = post_json["comment"] or ""
        post_directory = os.path.join(self.directory, sanitize_for_path(post_creator), sanitize_for_path(str(post_id) + " - " + post_title))

        os.makedirs(post_directory, exist_ok=True)
        if self.dump_metadata:
            save_metadata(post_json, post_directory)
        if self.download_thumb and post_json["thumb"]:
            self.download_thumbnail(post_json["thumb"]["original"], post_directory)
        if self.parse_for_external_links:
            self.parse_external_links(post_description, os.path.abspath(post_directory))
        for post in post_contents:
            self.download_post_content(post, post_directory)
        if not os.listdir(post_directory):
            self.output("No content downloaded for post {}. Deleting directory...\n".format(post_id))
            os.rmdir(post_directory)

    def parse_external_links(self, post_description, post_directory):
        link_matches = self.EXTERNAL_LINKS_RE.findall(post_description)
        if link_matches:
            self.output("Found {} external link(s) in post. Saving...\n".format(len(link_matches)))
            build_crawljob(link_matches, self.directory, post_directory, self.autostart_crawljob)


class FantiaClub:
    def __init__(self, fanclub_id):
        self.id = fanclub_id


def save_metadata(metadata, directory):
    filename = os.path.join(directory, "metadata.json")
    with open(filename, "w") as file:
        json.dump(metadata, file, sort_keys=True, indent=4)


def sanitize_for_path(value, replace=' '):
    """Remove potentially illegal characters from a path."""
    sanitized = re.sub(r'[<>\"\?\\\/\*:|]', replace, value)
    return re.sub(r'[\s.]+$', '', sanitized)


def build_crawljob(links, root_directory, post_directory, autostart_crawljob):
    filename = os.path.join(root_directory, "external_links.crawljob")
    with open(filename, "a", encoding="utf-8") as file:
        for link in links:
            crawl_dict = {
                    "packageName" : "Fantia",
                    "text" : link,
                    "downloadFolder" : post_directory,
                    "enabled" : "true",
                    "autoStart" : str(autostart_crawljob).lower(),
                    "forcedStart" : "true",
                    "autoConfirm" : "true",
                    "addOfflineLink" : "true",
                    "extractAfterDownload" : "false"
                }

            for key, value in crawl_dict.items():
                file.write(key + "=" + value + "\n")
            file.write("\n")
