#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download media and other data from Fantia"""

import argparse
import getpass
import netrc
import sys
import traceback

import models

__author__ = "bitbybyte"
__copyright__ = "Copyright 2020 bitbybyte"

__license__ = "MIT"
__version__ = "1.7"

BASE_HOST = "fantia.jp"

if __name__ == "__main__":
    cmdl_usage = "%(prog)s [options] url"
    cmdl_version = __version__
    cmdl_parser = argparse.ArgumentParser(usage=cmdl_usage, conflict_handler="resolve")

    cmdl_parser.add_argument("-c", "--cookie", dest="session_arg", metavar="SESSION_COOKIE", help="_session_id cookie or cookies.txt")
    cmdl_parser.add_argument("-e", "--email", dest="email", metavar="EMAIL", help=argparse.SUPPRESS)
    cmdl_parser.add_argument("-p", "--password", dest="password", metavar="PASSWORD", help=argparse.SUPPRESS)
    cmdl_parser.add_argument("-n", "--netrc", action="store_true", dest="netrc", help=argparse.SUPPRESS)
    cmdl_parser.add_argument("-q", "--quiet", action="store_true", dest="quiet", help="suppress output")
    cmdl_parser.add_argument("-v", "--version", action="version", version=cmdl_version)
    cmdl_parser.add_argument("url", action="store", nargs="*", help="fanclub or post URL")

    dl_group = cmdl_parser.add_argument_group("download options")
    dl_group.add_argument("-i", "--ignore-errors", action="store_true", dest="continue_on_error", help="continue on download errors")
    dl_group.add_argument("-l", "--limit", dest="limit", metavar='N', type=int, default=0, help="limit the number of posts to process per fanclub")
    dl_group.add_argument("-o", "--output-directory", dest="output_path", help="directory to download to")
    dl_group.add_argument("-s", "--use-server-filenames", action="store_true", dest="use_server_filenames", help="download using server defined filenames")
    dl_group.add_argument("-r", "--mark-incomplete-posts", action="store_true", dest="mark_incomplete_posts", help="add .incomplete file to post directories that are incomplete")
    dl_group.add_argument("-m", "--dump-metadata", action="store_true", dest="dump_metadata", help="store metadata to file (including fanclub icon, header, and background)")
    dl_group.add_argument("-x", "--parse-for-external-links", action="store_true", dest="parse_for_external_links", help="parse posts for external links")
    dl_group.add_argument("-t", "--download-thumbnail", action="store_true", dest="download_thumb", help="download post thumbnails")
    dl_group.add_argument("-f", "--download-fanclubs", action="store_true", dest="download_fanclubs", help="download posts from all followed fanclubs")
    dl_group.add_argument("-p", "--download-paid-fanclubs", action="store_true", dest="download_paid_fanclubs", help="download posts from all fanclubs backed on a paid plan")
    dl_group.add_argument("-d", "--download-month", dest="month_limit", metavar="%Y-%m", help="download posts only from a specific month, e.g. 2007-08")
    dl_group.add_argument("--exclude", dest="exclude_file", metavar="EXCLUDE_FILE", help="file containing a list of filenames to exclude from downloading")


    cmdl_opts = cmdl_parser.parse_args()

    session_arg = cmdl_opts.session_arg
    email = cmdl_opts.email
    password = cmdl_opts.password

    if (email or password or cmdl_opts.netrc) and not session_arg:
        sys.exit("Logging in from the command line is no longer supported. Please provide a session cookie using -c/--cookie. See the README for more information.")

    if not (cmdl_opts.download_fanclubs or cmdl_opts.download_paid_fanclubs) and not cmdl_opts.url:
        sys.exit("Error: No valid input provided")

    if not session_arg:
        session_arg = input("Fantia session cookie (_session_id or cookies.txt path): ")

    # if cmdl_opts.netrc:
    #     login = netrc.netrc().authenticators(BASE_HOST)
    #     if login:
    #         email = login[0]
    #         password = login[2]
    #     else:
    #         sys.exit("Error: No Fantia login found in .netrc")
    # else:
    #     if not email:
    #         email = input("Email: ")
    #     if not password:
    #         password = getpass.getpass("Password: ")

    try:
        downloader = models.FantiaDownloader(session_arg=session_arg, dump_metadata=cmdl_opts.dump_metadata, parse_for_external_links=cmdl_opts.parse_for_external_links, download_thumb=cmdl_opts.download_thumb, directory=cmdl_opts.output_path, quiet=cmdl_opts.quiet, continue_on_error=cmdl_opts.continue_on_error, use_server_filenames=cmdl_opts.use_server_filenames, mark_incomplete_posts=cmdl_opts.mark_incomplete_posts, month_limit=cmdl_opts.month_limit, exclude_file=cmdl_opts.exclude_file)
        if cmdl_opts.download_fanclubs:
            try:
                downloader.download_followed_fanclubs(limit=cmdl_opts.limit)
            except KeyboardInterrupt:
                raise
            except:
                if cmdl_opts.continue_on_error:
                    downloader.output("Encountered an error downloading followed fanclubs. Skipping...\n")
                    traceback.print_exc()
                    pass
                else:
                    raise
        elif cmdl_opts.download_paid_fanclubs:
            try:
                downloader.download_paid_fanclubs(limit=cmdl_opts.limit)
            except:
                if cmdl_opts.continue_on_error:
                    downloader.output("Encountered an error downloading paid fanclubs. Skipping...\n")
                    traceback.print_exc()
                    pass
                else:
                    raise
        if cmdl_opts.url:
            for url in cmdl_opts.url:
                    url_match = models.FANTIA_URL_RE.match(url)
                    if url_match:
                        try:
                            url_groups = url_match.groups()
                            if url_groups[0] == "fanclubs":
                                fanclub = models.FantiaClub(url_groups[1])
                                downloader.download_fanclub(fanclub, cmdl_opts.limit)
                            elif url_groups[0] == "posts":
                                downloader.download_post(url_groups[1])
                        except KeyboardInterrupt:
                            raise
                        except:
                            if cmdl_opts.continue_on_error:
                                downloader.output("Encountered an error downloading URL. Skipping...\n")
                                traceback.print_exc()
                                continue
                            else:
                                raise
                    else:
                        sys.stderr.write("Error: {} is not a valid URL. Please provide a fully qualified Fantia URL (https://fantia.jp/posts/[id], https://fantia.jp/fanclubs/[id])\n".format(url))
    except KeyboardInterrupt:
        sys.exit("Interrupted by user. Exiting...")
