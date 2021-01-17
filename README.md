# FantiaDL
Download media and other data from Fantia fanclubs and posts. A session cookie must be provided with the -c/--cookie argument directly or by passing the path to a legacy Netscape cookies file. Please see the [About Session Cookies](#about-session-cookies) section.

```
usage: fantiadl.py [options] url

positional arguments:
  url                   fanclub or post URL

optional arguments:
  -h, --help            show this help message and exit
  -c SESSION_COOKIE, --cookie SESSION_COOKIE
                        _session_id cookie or cookies.txt
  -q, --quiet           suppress output
  -v, --version         show program's version number and exit

download options:
  -i, --ignore-errors   continue on download errors
  -l N, --limit N       limit the number of posts to process per fanclub
  -o OUTPUT_PATH, --output-directory OUTPUT_PATH
                        directory to download to
  -s, --use-server-filenames
                        download using server defined filenames
  -r, --mark-incomplete-posts
                        add .incomplete file to post directories that are incomplete
  -m, --dump-metadata   store metadata to file (including fanclub icon, header, and background)
  -x, --parse-for-external-links
                        parse posts for external links
  -t, --download-thumbnail
                        download post thumbnails
  -f, --download-fanclubs
                        download posts from all followed fanclubs
  -p, --download-paid-fanclubs
                        download posts from all fanclubs backed on a paid plan
  -d %Y-%m, --download-month %Y-%m
                        download posts only from a specific month, e.g. 2007-08
  --exclude EXCLUDE_FILE
                        file containing a list of filenames to exclude from downloading
```

When parsing for external links using `-x`, a .crawljob file is created in your root directory (either the directory provided with `-o` or the directory the script is being run from) that can be parsed by [JDownloader](http://jdownloader.org/). As posts are parsed, links will be appended and assigned their appropriate post directories for download. You can import this file manually into JDownloader (File -> Load Linkcontainer) or setup the Folder Watch plugin to watch your root directory for .crawljob files.

## About Session Cookies
Due to recent changes imposed by Fantia, providing an email and password to login from the command line is no longer supported. In order to login, you will need to provide the `_session_id` cookie for your Fantia login session using -c/--cookie. After logging in normally on your browser, this value can then be extracted and used with FantiaDL. This value expires and may need to be updated with some regularity.

### Mozilla Firefox
1. On https://fantia.jp, press Ctrl + Shift + I to open Developer Tools.
2. Select the Storage tab at the top. In the sidebar, select https://fantia.jp under the Cookies heading.
3. Locate the `_session_id` cookie name. Click on the value to copy it.

### Google Chrome
1. On https://fantia.jp, press Ctrl + Shift + I to open DevTools.
2. Select the Application tab at the top. In the sidebar, expand Cookies under the Storage heading and select https://fantia.jp.
3. Locate the `_session_id` cookie name. Click on the value to copy it.

### Third-Party Extensions (cookies.txt)
You also have the option of passing the path to a legacy Netscape format cookies file with -c/--cookie, e.g. `-c ~/cookies.txt`. Using an extension like [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg), create a text file matching the accepted format:

```
# Netscape HTTP Cookie File
# https://curl.haxx.se/rfc/cookie_spec.html
# This is a generated file! Do not edit.

fantia.jp	FALSE	/	FALSE	1595755239	_session_id	a1b2c3d4...
```

Only the `_session_id` cookie is required.

## Download
Check the [releases page](https://github.com/bitbybyte/fantiadl/releases/latest) for the latest binaries.

## Build Requirements
 - Python 3.x
 - requests
 - beautifulsoup4

## Roadmap
 - More robust logging
