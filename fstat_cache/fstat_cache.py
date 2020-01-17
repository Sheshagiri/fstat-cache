from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
from threading import Thread
import logging


__all__ = ['FStatCache']
logging.basicConfig(filename="fstat-cache.log", format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
watches = {}


class MonitorThread(Thread):
    """
    Thread that runs inotify.read() on all the files that we want to watch for change events.
    For now we are only interested in MODIFY and DELETE events. When a MODIFY event is received, we eagerly go and fetch
    the updated timestamp and the size of the file and save them in our cache. This kind of fetch mechanism will help us
    keep the latest details for a file in our cache. Please note that the events them self are returned in a serial
    fashion from the inotify_simple library. If this becomes a bottleneck we could start using a queue and push the
    fetch events(os.stat) to that queue. We could potentially have multiple threads consuming from that queue which will
    fetch the details of the file using os.stat.
    """
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self, inotify: INotify, store: OrderedDict, timeout: int):
        for file_path in list(store):
            try:
                # for now only monitor modification of files
                logger.info("adding %s to watch list" % file_path)
                wd = inotify.add_watch(file_path, flags.MODIFY)
                watches[wd] = file_path
            except FileNotFoundError:
                pass

        # print("watch list %s " % watches)
        while self._running:
            for event in inotify.read(timeout=timeout):
                # print(str(event))
                for flag in flags.from_mask(event.mask):
                    # we only watch files for modification events
                    if flag == flags.MODIFY:
                        # only if the event is for a file that we are watching for
                        if event.wd in watches:
                            file_path = watches[event.wd]
                            logger.debug("modify event received for %s " % file_path)
                            store[file_path] = FStatCache.get_file_stats_using_stat(file_path)


class FStatCache(object):
    """
    Simple caching mechanism using inotify functionality from linux to avoid expensive repeated
    os.stat calls to the latest details of a file. When a file is modified we listen for the event and update our cache.
    """
    self_stats_file = "/tmp/fstat-cache-stats"

    def __init__(self, timeout=None):
        # this could potentially be an LRU Cache
        self._store = OrderedDict()
        self._inotify = INotify()
        self._monitor = MonitorThread()
        self._monitor_thread = Thread(target=self._monitor.run, args=(self._inotify, self._store, timeout, ))

    def get_file_stats(self, file_path: str):
        """
        takes absolute path to a file and returns the last modification time and size in bytes.
        :param file_path: absolute path to a file
        :return: { timestamp, size}
        """
        try:
            return self._get_item(file_path)
        except KeyError:
            logger.info("file %s is not present in the cache adding it "
                        "now and fetching the details using os.stat" % file_path)
            return self._add_file_to_watch(file_path)

    @staticmethod
    def get_file_stats_using_stat(file_path: str):
        """
        takes absolute path to a file and returns the last modification time and size
        in bytes by using os.stat function. This is available here only to get some benchmarks to compare
        with this cache implementation.
        :param file_path:
        :return: { timestamp, size}
        """
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            return {"ts": file_info.st_mtime, "size": file_info.st_size}

    def _get_item(self, file_path: str):
        return self._store[file_path]

    def _set_item(self, file_path: str, stats: dict):
        self._store[file_path] = stats

    def build(self, file_paths: list):
        """
        takes list of files and starts watching for changes using inotify from Linux.
        :param file_paths: list of files to watch for changes, only absolute paths.
        """
        for file_path in file_paths:
            # only if the file exists
            if os.path.isfile(file_path):
                self._store[file_path] = self.get_file_stats(file_path)
        self._monitor_thread.start()

    def invalidate(self):
        """
        will invalidate the current cache and remove all the files from the watcher.
        """
        self._unwatch_all_files()
        self._monitor.terminate()

    def _add_file_to_watch(self, file_path: str):
        if os.path.isfile(file_path):
            wd = self._inotify.add_watch(file_path, flags.MODIFY)
            watches[wd] = file_path

        stats = self.get_file_stats_using_stat(file_path)
        self._set_item(file_path, stats)
        return stats

    def _remove_from_watch(self, file_path: str):
        wd = FStatCache._get_key(watches, file_path)
        self._inotify.rm_watch(wd)
        del watches[wd]

    def _unwatch_all_files(self):
        for wd in list(watches):
            logger.debug("removing %s from watch list" % watches[wd])
            self._inotify.rm_watch(wd)
            del watches[wd]

    @staticmethod
    def list_files_in_cache():
        return list(watches.values())

    def add_file_to_watch(self, file_path: str):
        """
        will add the given file to watch list, stats in cache will be updated when
        a file modification event is received
        :param file_path: absolute path to the file to monitor
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError("given file doesn't exist")
        wd = self._inotify.add_watch(file_path, flags.MODIFY)
        watches[wd] = file_path

    def remove_from_watch(self, file_path: str):
        """
        will remove the file from watcher, will raise an error if the file is not
        being watched
        :param file_path: absolute path to the file to remove from watcher
        """
        if file_path not in list(watches.values()):
            # define a custom exception class here
            raise KeyError("file is not being watched")

        self._remove_from_watch(file_path)

    @staticmethod
    def _get_key(watches: dict, value: str):
        for item in watches:
            if watches[item] == value:
                return item


if __name__ == '__main__':
    """
    for testing purposes only, run the following command
    $ python fstat_cache.py
    """
    cache = FStatCache()
    cache.build(["/tmp/test_file1", "/tmp/test_file2"])
    print("stats for /tmp/test_file1 = %s " % cache.get_file_stats("/tmp/test_file1"))
    print("stats for /tmp/test_file2 = %s " % cache.get_file_stats("/tmp/test_file2"))
    print("list of files in the cache = %s " % cache.list_files_in_cache())
    os.system("echo validate >> /tmp/test_file1")
    os.system("echo validate >> /tmp/test_file2")
    print("stats for /tmp/test_file1 = %s " % cache.get_file_stats("/tmp/test_file1"))
    print("stats for /tmp/test_file2 = %s " % cache.get_file_stats("/tmp/test_file2"))
    cache.invalidate()
