```python
# Exif stuff
# https://en.wikipedia.org/wiki/Exif
# https://stackoverflow.com/questions/9542359/does-png-contain-exif-data-like-jpg

# Go over add_exif_comment in the yield_local_media_files.py module
```

```python
cd sync_test_poc/

import logging
from yield_local_media_files import *

logging.getLogger().setLevel(logging.INFO)

yield_files_from_config(
    config_file_path='./test.csv', 
    root_folder='./local-test-files')
```

```bash
# Current test solution has same MD5 digest for 
# each file (media asset)
cd test/resources/test_sync
find . -type f -exec md5 {} \;
```