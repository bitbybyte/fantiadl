# FantiaDL
Download media and other data from Fantia fanclubs and posts. An email and password must be provided using the -e and -p arguments.

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
  -o OUTPUT_PATH, --output-directory OUTPUT_PATH
                        directory to download to
  -m, --dump-metadata   store metadata to file
```
## Download
Check the [releases page](/releases/latest) for the latest binaries.

## Build Requirements
 - Python 3.x
 - requests

## Roadmap
 - Custom filename templating
 - More robust logging
