import fstat_cache
import tempfile
import timeit
import functools
import time
import os


def create_temp_files(size):
    count = 0
    temp_files = []
    while count < size:
        _,temp_file = tempfile.mkstemp(prefix="benchmark_",suffix="_file_" + str(count))
        write_to_file(temp_file, str(count))
        count = count + 1
        temp_files.append(temp_file)

    return temp_files


def clean_up_temp_files(file_paths):
    for file_path in file_paths:
        os.remove(file_path)


def write_to_file(file_path: str, data: str, file_mode: str = 'a') -> None:
    with open(file_path, file_mode) as fp:
        fp.write(data)


def using_cache(cache: fstat_cache.FStatCache):
    stats = {}
    for file_path in random_files:
        stats[file_path] = cache.get_file_stats(file_path)["size"]
    # print(stats)


def using_stat(cache: fstat_cache.FStatCache):
    stats = {}
    for file_path in random_files:
        stats[file_path] = cache.get_file_stats_using_stat(file_path)["size"]

    # print(stats)


if __name__ == '__main__':
    start_time = time.time()
    print("creating %s temp files" % 10000)
    random_files = create_temp_files(10000)
    print("created temp files in %f seconds" % (time.time() - start_time))
    print("building cache")
    stat_time = time.time()
    fs_cache = fstat_cache.FStatCache()
    fs_cache.build(random_files)
    print("built cache in %f seconds" % (time.time() - start_time))
    print("starting benchmarks now")
    cache_timer = timeit.Timer(functools.partial(using_cache, fs_cache))
    print("using fstat-cache library: %f seconds" % cache_timer.timeit(100))
    stat_time = timeit.Timer(functools.partial(using_stat, fs_cache))
    print("using os.stat: %f seconds" % stat_time.timeit(100))
    fs_cache.invalidate()
    print("cleaning up tmp files")
    clean_up_temp_files(random_files)
