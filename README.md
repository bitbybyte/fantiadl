# FantiaDL
Download media and other data from Fantia. A session key value must be provided by the user from the `_session_id` cookie stored when logged in to Fantia.

```
usage: fantiadl.py session_key url

positional arguments:
  session_key           session key
  url                   fanclub or post URL

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           suppress output
  -v, --version         show program's version number and exit

download options:
  -o OUTPUT_PATH, --output-directory OUTPUT_PATH
                        directory to download to
  -m, --dump-metadata   store metadata to file
```

## Requirements
 - Python 3.x
 - requests

## Roadmap
 - Custom filename templating
 - Download a single post by ID
 - Login from CLI or .netrc
 - Progress and ETA during downloading
