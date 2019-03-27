# Description

`test_release_pages.py` will run some tests for the Download pages and the
Pre-Release pages of Python.

This code is for the release managers of Python

# Installation

```
pip install -r requirements.txt
```

# Usage

```
python test_release_pages.py 3.8.0a2 --pre-release
```

Several tests:
* http 200 on https://www.python.org/downloads/release/python-XYZ/
* right title
* has_changelog
* has_files_section
    * will check for the files, the size and the md5sum

`--pre-release` will check if the PreRelease page contains the right version of
Python

PreRelease check
* http 200
* has reference 3.x on https://www.python.org/downoad/pre-releases/
