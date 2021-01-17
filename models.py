#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests

from datetime import datetime as dt
from urllib.parse import unquote
from urllib.parse import urljoin
from urllib.parse import urlparse
import http.cookiejar
import json
import mimetypes
import os
import re
import sys
import time
import traceback


FANTIA_URL_RE = re.compile(r"(?:https?://(?:(?:www\.)?(?:fantia\.jp/(fanclubs|posts)/)))([0-9]+)")
EXTERNAL_LINKS_RE = re.compile(r"(?:[\s]+)?((?:(?:https?://)?(?:(?:www\.)?(?:mega\.nz|mediafire\.com|(?:drive|docs)\.google\.com|youtube.com)\/))[^\s]+)")

DOMAIN = "fantia.jp"
BASE_URL = "https://fantia.jp/"

LOGIN_SIGNIN_URL = "https://fantia.jp/sessions/signin"
LOGIN_SESSION_URL = "https://fantia.jp/sessions"

ME_API = "https://fantia.jp/api/v1/me"

FANCLUB_API = "https://fantia.jp/api/v1/fanclubs/{}"
FANCLUBS_FOLLOWING_API = "https://fantia.jp/api/v1/me/fanclubs"
FANCLUBS_PAID_HTML = "https://fantia.jp/mypage/users/plans?type=not_free"
FANCLUB_POSTS_HTML = "https://fantia.jp/fanclubs/{}/posts?page={}"

POST_API = "https://fantia.jp/api/v1/posts/{}"
POST_URL = "https://fantia.jp/posts"
POST_RELATIVE_URL = "/posts/"
RENEW_STR = "更新"

CRAWLJOB_FILENAME = "external_links.crawljob"

MIMETYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm"
}


class FantiaClub:
    def __init__(self, fanclub_id):
        self.id = fanclub_id


class FantiaDownloader:
    def __init__(self, session_arg, chunk_size=1024 * 1024 * 5, dump_metadata=False, parse_for_external_links=False, download_thumb=False, directory=None, quiet=True, continue_on_error=False, use_server_filenames=False, mark_incomplete_posts=False, month_limit=None, exclude_file=None):
        # self.email = email
        # self.password = password
        self.session_arg = session_arg
        self.chunk_size = chunk_size
        self.dump_metadata = dump_metadata
        self.parse_for_external_links = parse_for_external_links
        self.download_thumb = download_thumb
        self.directory = directory or ""
        self.quiet = quiet
        self.continue_on_error = continue_on_error
        self.use_server_filenames = use_server_filenames
        self.mark_incomplete_posts = mark_incomplete_posts
        self.month_limit = dt.strptime(month_limit, "%Y-%m") if month_limit else None
        self.exclude_file = exclude_file
        self.exclusions = []
        self.session = requests.session()
        self.login()
        self.create_exclusions()

    def output(self, output):
        """Write output to the console."""
        if not self.quiet:
            try:
                sys.stdout.write(output.encode(sys.stdout.encoding, errors="backslashreplace").decode(sys.stdout.encoding))
                sys.stdout.flush()
            except (UnicodeEncodeError, UnicodeDecodeError):
                sys.stdout.buffer.write(output.encode("utf-8"))
                sys.stdout.flush()

    def login(self):
        """Login to Fantia using the provided email and password."""

        try:
            with open(self.session_arg, "r") as cookies_file:
                cookies = http.cookiejar.MozillaCookieJar(self.session_arg)
                cookies.load()
                self.session.cookies = cookies
        except FileNotFoundError:
            login_cookie = requests.cookies.create_cookie(domain=DOMAIN, name="_session_id", value=self.session_arg)
            self.session.cookies.set_cookie(login_cookie)

        check_user = self.session.get(ME_API)
        if not (check_user.ok or check_user.status_code == 304):
            sys.exit("Error: Invalid session. Please verify your session cookie")

        # Login flow, requires reCAPTCHA token

        # login_json = {
        #     "utf8": "✓",
        #     "button": "",
        #     "user[email]": self.email,
        #     "user[password]": self.password,
        # }

        # login_session = self.session.get(LOGIN_SIGNIN_URL)
        # login_page = BeautifulSoup(login_session.text, "html.parser")
        # authenticity_token = login_page.select_one("input[name=\"authenticity_token\"]")["value"]
        # print(login_page.select_one("input[name=\"recaptcha_response\"]"))
        # login_json["authenticity_token"] = authenticity_token
        # login_json["recaptcha_response"] = ...

        # create_session = self.session.post(LOGIN_SESSION_URL, data=login_json)
        # if not create_session.headers.get("Location"):
        #     sys.exit("Error: Bad login form data")
        # elif create_session.headers["Location"] == LOGIN_SIGNIN_URL:
        #     sys.exit("Error: Failed to login. Please verify your username and password")

        # check_user = self.session.get(ME_API)
        # if not (check_user.ok or check_user.status_code == 304):
        #     sys.exit("Error: Invalid session")

    def create_exclusions(self):
        """Read files to exclude from downloading."""
        if self.exclude_file:
            with open(self.exclude_file, "r") as file:
                self.exclusions = [line.rstrip("\n") for line in file]

    def process_content_type(self, url):
        """Process the Content-Type from a request header and use it to build a filename."""
        url_header = self.session.head(url)
        mimetype = url_header.headers["Content-Type"]
        extension = guess_extension(mimetype, url)
        return extension

    def download_fanclub_metadata(self, fanclub):
        """Download fanclub header, icon, and custom background."""
        response = self.session.get(FANCLUB_API.format(fanclub.id))
        response.raise_for_status()
        fanclub_json = json.loads(response.text)

        fanclub_creator = fanclub_json["fanclub"]["creator_name"]
        fanclub_directory = os.path.join(self.directory, sanitize_for_path(fanclub_creator))
        os.makedirs(fanclub_directory, exist_ok=True)

        self.save_metadata(fanclub_json, fanclub_directory)

        header_url = fanclub_json["fanclub"]["cover"]["original"]
        if header_url:
            header_filename = os.path.join(fanclub_directory, "header" + self.process_content_type(header_url))
            self.output("Downloading fanclub header...\n")
            self.perform_download(header_url, header_filename, use_server_filename=self.use_server_filenames)

        fanclub_icon_url = fanclub_json["fanclub"]["icon"]["original"]
        if fanclub_icon_url:
            fanclub_icon_filename = os.path.join(fanclub_directory, "icon" + self.process_content_type(fanclub_icon_url))
            self.output("Downloading fanclub icon...\n")
            self.perform_download(fanclub_icon_url, fanclub_icon_filename, use_server_filename=self.use_server_filenames)

        background_url = fanclub_json["fanclub"]["background"]
        if background_url:
            background_filename = os.path.join(fanclub_directory, "background" + self.process_content_type(background_url))
            self.output("Downloading fanclub background...\n")
            self.perform_download(background_url, background_filename, use_server_filename=self.use_server_filenames)

    def download_fanclub(self, fanclub, limit=0):
        """Download a fanclub."""
        self.output("Downloading fanclub {}...\n".format(fanclub.id))
        post_ids = self.fetch_fanclub_posts(fanclub)

        if self.dump_metadata:
            self.download_fanclub_metadata(fanclub)

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

    def download_followed_fanclubs(self, limit=0):
        """Download all followed fanclubs."""
        response = self.session.get(FANCLUBS_FOLLOWING_API)
        response.raise_for_status()
        fanclub_ids = json.loads(response.text)["fanclub_ids"]

        for fanclub_id in fanclub_ids:
            try:
                fanclub = FantiaClub(fanclub_id)
                self.download_fanclub(fanclub, limit)
            except KeyboardInterrupt:
                raise
            except:
                if self.continue_on_error:
                    self.output("Encountered an error downloading fanclub. Skipping...\n")
                    traceback.print_exc()
                    continue
                else:
                    raise

    def download_paid_fanclubs(self, limit=0):
        """Download all fanclubs backed on a paid plan."""
        response = self.session.get(FANCLUBS_PAID_HTML)
        response.raise_for_status()
        response_page = BeautifulSoup(response.text, "html.parser")
        fanclub_links = response_page.select("div.mb-5-children > div:nth-of-type(1) a[href^=\"/fanclubs\"]")

        for fanclub_link in fanclub_links:
            try:
                fanclub_id = fanclub_link["href"].lstrip("/fanclubs/")
                fanclub = FantiaClub(fanclub_id)
                self.download_fanclub(fanclub, limit)
            except KeyboardInterrupt:
                raise
            except:
                if self.continue_on_error:
                    self.output("Encountered an error downloading fanclub. Skipping...\n")
                    traceback.print_exc()
                    continue
                else:
                    raise

    def fetch_fanclub_posts(self, fanclub):
        """Iterate over a fanclub's HTML pages to fetch all post IDs."""
        all_posts = []
        post_found = False
        page_number = 1
        self.output("Collecting fanclub posts...\n")
        while True:
            response = self.session.get(FANCLUB_POSTS_HTML.format(fanclub.id, page_number))
            response.raise_for_status()
            response_page = BeautifulSoup(response.text, "html.parser")
            posts = response_page.select("div.post")
            new_post_ids = []
            for post in posts:
                link = post.select_one("a.link-block")["href"]
                post_id = link.lstrip(POST_RELATIVE_URL)
                date_string = post.select_one("span.post-date").text.rstrip(RENEW_STR)
                parsed_date = dt.strptime(date_string, "%Y-%m-%d %H:%M")
                if not self.month_limit or (parsed_date.year == self.month_limit.year and parsed_date.month == self.month_limit.month):
                    post_found = True
                    new_post_ids.append(post_id)
            all_posts += new_post_ids
            if not posts or (not new_post_ids and post_found): # No new posts found and we've already collected a post
                self.output("Collected {} posts.\n".format(len(all_posts)))
                return all_posts
            else:
                page_number += 1

    def perform_download(self, url, filepath, use_server_filename=False):
        """Perform a download for the specified URL while showing progress."""
        request = self.session.get(url, stream=True)

        if request.status_code == 404:
            self.output("Download URL returned 404. Skipping...\n")
            return

        request.raise_for_status()

        url_path = unquote(request.url.split("?", 1)[0])
        server_filename = os.path.basename(url_path)
        filename = os.path.basename(filepath)
        if use_server_filename:
            filepath = os.path.join(os.path.dirname(filepath), server_filename)

        # Check if filename is in exclusion list
        if server_filename in self.exclusions:
            self.output("Server filename in exclusion list (skipping): {}\n".format(server_filename))
            return
        elif filename in self.exclusions:
            self.output("Filename in exclusion list (skipping): {}\n".format(filename))
            return

        file_size = int(request.headers["Content-Length"])
        if os.path.isfile(filepath) and os.stat(filepath).st_size == file_size:
            self.output("File found (skipping): {}\n".format(filepath))
            return

        self.output("File: {}\n".format(filepath))
        base_filename, original_extension = os.path.splitext(filepath)
        incomplete_filename = base_filename + ".incomplete"

        downloaded = 0
        with open(incomplete_filename, "wb") as file:
            for chunk in request.iter_content(self.chunk_size):
                downloaded += len(chunk)
                file.write(chunk)
                done = int(25 * downloaded / file_size)
                percent = int(100 * downloaded / file_size)
                self.output("\r|{0}{1}| {2}% ".format("\u2588" * done, " " * (25 - done), percent))
        self.output("\n")
        os.rename(incomplete_filename, filepath)

        modification_time_string = request.headers["Last-Modified"]
        modification_time = int(dt.strptime(modification_time_string, "%a, %d %b %Y %H:%M:%S %Z").timestamp())
        if modification_time:
            access_time = int(time.time())
            os.utime(filepath, times=(access_time, modification_time))

    def download_photo(self, photo_url, photo_counter, gallery_directory):
        """Download a photo to the post's directory."""
        extension = self.process_content_type(photo_url)
        filename = os.path.join(gallery_directory, str(photo_counter) + extension) if gallery_directory else str()
        self.perform_download(photo_url, filename, use_server_filename=self.use_server_filenames)

    def download_file(self, download_url, filename, post_directory):
        """Download a file to the post's directory."""
        self.perform_download(download_url, filename, use_server_filename=True) # Force serve filenames to prevent duplicate collision

    def download_post_content(self, post_json, post_directory):
        """Parse the post's content to determine whether to save the content as a photo gallery or file."""
        if post_json.get("visible_status") == "visible":
            if post_json.get("category") == "photo_gallery":
                photo_gallery_title = post_json["title"]
                if not photo_gallery_title:
                    photo_gallery_title = str(post_json["id"])
                photo_gallery = post_json["post_content_photos"]
                photo_counter = 0
                gallery_directory = os.path.join(post_directory, sanitize_for_path(photo_gallery_title))
                os.makedirs(gallery_directory, exist_ok=True)
                for photo in photo_gallery:
                    photo_url = photo["url"]["original"]
                    self.download_photo(photo_url, photo_counter, gallery_directory)
                    photo_counter += 1
            elif post_json.get("category") == "file":
                filename = os.path.join(post_directory, post_json["filename"])
                download_url = urljoin(POST_URL, post_json["download_uri"])
                self.download_file(download_url, filename, post_directory)
            elif post_json.get("category") == "embed":
                if self.parse_for_external_links:
                    # TODO: Check what URLs are allowed as embeds
                    link_as_list = [post_json["embed_url"]]
                    self.output("Adding embedded link {0} to {1}.\n".format(post_json["embed_url"], CRAWLJOB_FILENAME))
                    build_crawljob(link_as_list, self.directory, post_directory)
            elif post_json.get("category") == "blog":
                blog_gallery_title = post_json["parent_post"]["title"]
                if not blog_gallery_title:
                    blog_gallery_title = str(post_json["id"])
                blog_comment = post_json["comment"]
                blog_json = json.loads(blog_comment)
                photo_counter = 0
                gallery_directory = os.path.join(post_directory, sanitize_for_path(blog_gallery_title))
                os.makedirs(gallery_directory, exist_ok=True)
                for op in blog_json["ops"]:
                    if type(op["insert"]) is dict and op["insert"].get("fantiaImage"):
                        photo_url = op["insert"]["fantiaImage"]["url"]
                        self.download_photo(photo_url, photo_counter, gallery_directory)
                        photo_counter += 1
            else:
                self.output("Post content category \"{}\" is not supported. Skipping...\n".format(post_json.get("category")))

            if self.parse_for_external_links:
                post_description = post_json["comment"] or ""
                self.parse_external_links(post_description, os.path.abspath(post_directory))
        else:
            self.output("Post content not available on current plan. Skipping...\n")

    def download_thumbnail(self, thumb_url, post_directory):
        """Download a thumbnail to the post's directory."""
        extension = self.process_content_type(thumb_url)
        filename = os.path.join(post_directory, "thumb" + extension)
        self.perform_download(thumb_url, filename, use_server_filename=self.use_server_filenames)

    def download_post(self, post_id):
        """Download a post to its own directory."""
        self.output("Downloading post {}...\n".format(post_id))

        response = self.session.get(POST_API.format(post_id))
        response.raise_for_status()
        post_json = json.loads(response.text)["post"]

        post_id = post_json["id"]
        post_creator = post_json["fanclub"]["creator_name"]
        post_title = post_json["title"]
        post_contents = post_json["post_contents"]

        post_directory_title = sanitize_for_path(str(post_id))

        post_directory = os.path.join(self.directory, sanitize_for_path(post_creator), post_directory_title)
        os.makedirs(post_directory, exist_ok=True)

        if self.dump_metadata:
            self.save_metadata(post_json, post_directory)
        if self.mark_incomplete_posts:
            self.mark_incomplete_post(post_json, post_directory)
        if self.download_thumb and post_json["thumb"]:
            self.download_thumbnail(post_json["thumb"]["original"], post_directory)
        if self.parse_for_external_links:
            # Main post
            post_description = post_json["comment"] or ""
            self.parse_external_links(post_description, os.path.abspath(post_directory))
        for post in post_contents:
            self.download_post_content(post, post_directory)
        if not os.listdir(post_directory):
            self.output("No content downloaded for post {}. Deleting directory.\n".format(post_id))
            os.rmdir(post_directory)

    def parse_external_links(self, post_description, post_directory):
        """Parse the post description for external links, e.g. Mega and Google Drive links."""
        link_matches = EXTERNAL_LINKS_RE.findall(post_description)
        if link_matches:
            self.output("Found {} external link(s) in post. Saving...\n".format(len(link_matches)))
            build_crawljob(link_matches, self.directory, post_directory)

    def save_metadata(self, metadata, directory):
        """Save the metadata for a post to the post's directory."""
        filename = os.path.join(directory, "metadata.json")
        with open(filename, "w") as file:
            json.dump(metadata, file, sort_keys=True, indent=4)

    def mark_incomplete_post(self, post_metadata, post_directory):
        """Mark incomplete posts with a .incomplete file."""
        is_incomplete = False
        incomplete_filename = os.path.join(post_directory, ".incomplete")
        for post in post_metadata["post_contents"]:
            if post["visible_status"] != "visible":
                is_incomplete = True
                break
        if is_incomplete:
            if not os.path.exists(incomplete_filename):
                open(incomplete_filename, 'a').close()
        else:
            if os.path.exists(incomplete_filename):
                os.remove(incomplete_filename)


def guess_extension(mimetype, download_url):
    """
    Guess the file extension from the mimetype or force a specific extension for certain mimetypes.
    If the mimetype returns no found extension, guess based on the download URL.
    """
    extension = MIMETYPES.get(mimetype) or mimetypes.guess_extension(mimetype, strict=True)
    if not extension:
        try:
            path = urlparse(download_url).path
            extension = os.path.splitext(path)[1]
        except IndexError:
            extension = ".unknown"
    return extension

def sanitize_for_path(value, replace=' '):
    """Remove potentially illegal characters from a path."""
    sanitized = re.sub(r'[<>\"\?\\\/\*:|]', replace, value)
    return re.sub(r'[\s.]+$', '', sanitized)

def build_crawljob(links, root_directory, post_directory):
    """Append to a root .crawljob file with external links gathered from a post."""
    filename = os.path.join(root_directory, CRAWLJOB_FILENAME)
    with open(filename, "a", encoding="utf-8") as file:
        for link in links:
            crawl_dict = {
                "packageName": "Fantia",
                "text": link,
                "downloadFolder": post_directory,
                "enabled": "true",
                "autoStart": "true",
                "forcedStart": "true",
                "autoConfirm": "true",
                "addOfflineLink": "true",
                "extractAfterDownload": "false"
            }

            for key, value in crawl_dict.items():
                file.write(key + "=" + value + "\n")
            file.write("\n")
