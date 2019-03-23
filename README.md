# FantiaDL
Download media and other data from Fantia fanclubs and posts. An email and password must be provided using the -e and -p arguments or with a .netrc file.

```
usage: fantiadl.py [options] url

positional arguments:
  url                   fanclub or post URL

optional arguments:
  -h, --help            show this help message and exit
  -e EMAIL, --email EMAIL
                        fantia email
  -p PASSWORD, --password PASSWORD
                        fantia password
  -n, --netrc           login with .netrc
  -q, --quiet           suppress output
  -v, --version         show program's version number and exit

download options:
  -l N, --limit N       limit the number of posts to process
  -o OUTPUT_PATH, --output-directory OUTPUT_PATH
                        root directory to download to
  -m, --dump-metadata   store metadata to file
  -x, --parse-for-external-links
                        parse post descriptions for external links
  -t, --download-thumbnail
                        download post thumbnail
```

When parsing for external links using `-x`, a `.crawljob` file is created in your root directory (either the directory provided with `-o` or the directory the script is being run from) that can be parsed by [JDownloader](http://jdownloader.org/). As posts are parsed, links will be appended and assigned their appropriate post directories for download. You can import this file manually into JDownloader (File -> Load Linkcontainer) or setup the Folder Watch plugin to watch your root directory for `.crawljob` files.

## Download
Check the [releases page](https://github.com/bitbybyte/fantiadl/releases/latest) for the latest binaries.

## Build Requirements
 - Python 3.x
 - requests

## Roadmap
 - More robust logging