# fstat-cache is a cache built using inotify from Linux.

## Problem Statement/Background
A typical log monitoring tool has to monitor log files to be able to determine if there were any changes
to be able to copy/stream those changes to a central server for housekeeping/analytics. One way of doing this
is to periodically perform `os.stat` on each log file and determine if there were any changes from the last visit.
If so then copy/stream those changes. If a customer has 100's/1000's of logs files being monitored then performing those
`os.stat` calls serially are quite expensive especially when only few logs files are actively being updated.

## Solution
One way of solving the above mentioned problem is to write a cache layer which will listen to file system events
using a library called `inotify` present in the Linux kernel and building a cache only when a event is received 
about a file change. This will abstract away the `os.stat` call and the cache layer will serve as a point of contact.
Further more LRU(Least Recently Used) kind of cache implementation can be used to build a cache layer of certain number
of files. Where the least recently used files will be replaced with a new file who details were requested. This way 
we can manage resources efficiently on low powered devices as well.

## An Example

```python
from fstat_cache import FStatCache
import time

if __name__ == '__main__':
    cache = FStatCache()
    cache.build(["/tmp/test_file1"])
    print(cache.get_file_stats("/tmp/test_file1"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file1"))
    cache.invalidate()
```

## [Another Example](fstat_cache/example_flask_app.py) of consuming this library in a flask app and following are
the steps to run it.
```bash
pip install -r requirements.txt
python fstat_cache/example_flask_app.py
# in another terminal or a browser
# will fetch the file size and last modification timestamp from cache
curl <ip:port>/cache/<path-to-a-file-in-/tmp-dir>
# eg: curl http://127.0.0.1:5000/cache/test_file_1
# will fetch the file size and last modification timestamp directly using os.stat
curl <ip:port>/stat/<path-to-a-file-in-/tmp-dir>
# eg: curl http://127.0.0.1:5000/stat/test_file_1
```

## Limitations

Works only on Linux. Doesn't work on Windows and MacOS.

## Running tests
```bash
cd fstat-cache/tests
nosetests -v
```
### Tests with coverage
```bash
nosetests -v --with-coverage --cover-package=fstat_cache
```
sample output 
```bash
$ nosetests -v --with-coverage --cover-package=fstat_cache
test_add_file_to_watch_and_remove (tests.test_fstat_cache.FStatCacheTestCase) ... ok
test_get_file_size_from_cache (tests.test_fstat_cache.FStatCacheTestCase) ... ok
test_get_file_size_using_stat (tests.test_fstat_cache.FStatCacheTestCase) ... ok
test_list_files_in_cache (tests.test_fstat_cache.FStatCacheTestCase) ... ok

Name                         Stmts   Miss  Cover
------------------------------------------------
fstat_cache/__init__.py          2      0   100%
fstat_cache/fstat_cache.py     108     20    81%
------------------------------------------------
TOTAL                          110     20    82%
----------------------------------------------------------------------
Ran 4 tests in 0.025s

OK
```

## Benchmarks

TBD

## Demo

TBD
