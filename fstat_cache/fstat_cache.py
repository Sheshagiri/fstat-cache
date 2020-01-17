from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
from threading import Thread
import time
import logging


__all__ = ['FStatCache']
logging.basicConfig(filename="fstat-cache.log", format='%(asctime)s %(message)s', filemode='w')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MonitorThread(Thread):
    """

    """
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self, inotify: INotify, store: OrderedDict, watches: dict, timeout: int):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        os.system("echo start=" + now + " GMT >> " + FStatCache.self_stats_file)
        store[FStatCache.self_stats_file] = FStatCache.get_file_stats_using_stat(FStatCache.self_stats_file)
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
                for flag in flags.from_mask(event.mask):
                    if flag == flags.MODIFY:
                        file_path = watches[event.wd]
                        logger.info("modify event received for %s " % file_path)
                        store[file_path] = FStatCache.get_file_stats_using_stat(file_path)
                    # don't know if its bug in inotify_simple but we get IGNORED event when a file is deleted
                    elif flag == flags.DELETE | flags.IGNORED:
                        logger.info("received delete event, removing %s from watch list" % file_path)
                        # NOTE: inoitfy already deletes a watch on file delete so
                        # we don't need to call rm_watch ourselves
                        # inotify.rm_watch(event.wd)
                        del watches[event.wd]
                        del store[watches[wd]]
                        logger.info("watch list: %s " % watches)


class FStatCache(object):
    """
    Simple caching mechanism using inotify functionality from linux to avoid expensive repeated
    os.stat call to get the size of a file. When a file is modified we listen for the event and
    update our cache.
    """
    self_stats_file = "/tmp/fstat-cache-stats"

    def __init__(self, timeout=None):
        # this could potentially be an LRU Cache
        self._store = OrderedDict()
        self._inotify = INotify()
        self._watches = {}
        self._monitor = MonitorThread()
        self._monitor_thread = Thread(target=self._monitor.run, args=(self._inotify, self._store,
                                                                      self._watches, timeout, ))

    def get_file_stats(self, file_path: str):
        """
        takes absolute path to a file and returns the last modification time in unix timestamp and size
        in bytes.
        :param file_path: absolute path to a file
        :return: { timestamp, size}
        """
        try:
            return self.__get_item(file_path)
        except KeyError:
            logger.info("file %s is not present in the cache adding it "
                        "now and fetching the details using os.stat" % file_path)
            return self.__add_file_to_watch(file_path)

    @staticmethod
    def get_file_stats_using_stat(file_path: str):
        """
        takes absolute path to a file and returns the last modification time in unix timestamp and size
        in bytes by using os.stat function. This is available here only to get some benchmarks to compare
        with this cache implementation.
        :param file_path:
        :return: { timestamp, size}
        """
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            return {"ts": file_info.st_mtime, "size": file_info.st_size}

    def __get_item(self, file_path: str):
        return self._store[file_path]

    def __set_item(self, file_path: str, stats: dict):
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
        self._monitor.terminate()
        # self._monitor_thread.join()
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        os.system("echo stop=" + now + " GMT >> " + FStatCache.self_stats_file)
        self.__unwatch_all_files()

    def __add_file_to_watch(self, file_path: str):
        if os.path.isfile(file_path):
            wd = self._inotify.add_watch(file_path, flags.MODIFY)
            self._watches[wd] = file_path

        logger.info("watch list: %s " % self._watches)
        stats = self.get_file_stats_using_stat(file_path)
        self.__set_item(file_path, stats)
        return stats

    def __remove_from_watch(self, file_path: str):
        wd = FStatCache.__get_key(self._watches, file_path)
        self._inotify.rm_watch(wd)
        del self._watches[wd]

    def __unwatch_all_files(self):
        for wd in list(self._watches):
            logger.info("removing %s from watch list" % self._watches[wd])
            self._inotify.rm_watch(wd)
            del self._watches[wd]

    def list_files_in_cache(self):
        return list(self._watches.values())

    def add_file_to_watch(self, file_path: str):
        """
        will add the given file to watch list, stats in cache will be updated when
        a file modification event is received
        :param file_path: absolute path to the file to monitor
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError("given file doesn't exist")
        wd = self._inotify.add_watch(file_path, flags.MODIFY)
        self._watches[wd] = file_path

    def remove_from_watch(self, file_path: str):
        """
        will remove the file from watcher, will raise an error if the file is not
        being watched
        :param file_path: absolute path to the file to remove from watcher
        """
        if file_path not in list(self._watches.values()):
            # define a custom exception class here
            raise KeyError("file is not being watched")

        self.__remove_from_watch(file_path)

    @staticmethod
    def __get_key(watches: dict, value: str):
        for item in watches:
            if watches[item] == value:
                return item


if __name__ == '__main__':
    cache = FStatCache()
    cache.build(["/tmp/test_file1", "/tmp/test_file2"])
    print(cache.get_file_stats("/tmp/test_file1"))
    print(cache.list_files_in_cache())
    time.sleep(6)
    cache.invalidate()
'''
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
'''
