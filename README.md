# fstat-cache is a cache implemented using inotify from Linux.

## An Example

```python
import FStatCache

if __name__ == '__main__':
    cache = FStatCache()
    cache.start(["/tmp/test_file1"])
    print(cache.get_file_stats("/tmp/test_file1"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file1"))
```