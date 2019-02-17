#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download media and other data from Fantia"""

import argparse
import getpass
import netrc
import sys

from models import FantiaDownloader, FantiaClub

__author__ = "bitbybyte"
__copyright__ = "Copyright 2019 bitbybyte"

__license__ = "MIT"
__version__ = "1.0"

BASE_HOST = "fantia.jp"

if __name__ == "__main__":
    cmdl_usage = "%(prog)s [options] url"
    cmdl_version = __version__
    cmdl_parser = argparse.ArgumentParser(usage=cmdl_usage, conflict_handler="resolve")

    cmdl_parser.add_argument("-e", "--email", dest="email", metavar="EMAIL", help="fantia email")
    cmdl_parser.add_argument("-p", "--password", dest="password", metavar="PASSWORD", help="fantia password")
    cmdl_parser.add_argument("-n", "--netrc", action="store_true", dest="netrc", help="login with .netrc")
    cmdl_parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", help="suppress output")
    cmdl_parser.add_argument("-v", "--version", action="version", version=cmdl_version)
    cmdl_parser.add_argument("url", help="fanclub or post URL")

    dl_group = cmdl_parser.add_argument_group("download options")
    dl_group.add_argument("-o", "--output-directory", dest="output_path", help="directory to download to")
    dl_group.add_argument("-m", "--dump-metadata", action="store_true", dest="dump_metadata", help="store metadata to file")

    cmdl_opts = cmdl_parser.parse_args()

    email = cmdl_opts.email
    password = cmdl_opts.password

    if cmdl_opts.netrc:
        login = netrc.netrc().authenticators(BASE_HOST)
        if login:
            email = login[0]
            password = login[2]
        else:
            sys.exit("No Fantia login found in .netrc")
    else:
        if not email:
            email = input("Email: ")
        if not password:
            password = getpass.getpass("Password: ")

    downloader = FantiaDownloader(email=email, password=password, dump_metadata=cmdl_opts.dump_metadata, directory=cmdl_opts.output_path, quiet=cmdl_opts.quiet)

    url_groups = downloader.FANTIA_URL_RE.match(cmdl_opts.url).groups()
    if url_groups:
        if url_groups[0] == "fanclubs":
            fanclub = FantiaClub(url_groups[1])
            downloader.download_fanclub_posts(fanclub)
        elif url_groups[0] == "posts":
            downloader.download_post(url_groups[1])
    else:
        sys.exit("Please provide a valid Fantia URL (/posts/[id], /fanclubs/[id])")
