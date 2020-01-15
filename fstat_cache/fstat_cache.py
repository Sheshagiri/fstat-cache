from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
import threading
import time

__all__ = ['FStatCache']


class FStatCache:
    """
    Simple caching mechanism using inotify functionality from linux to avoid expensive repeated
    os.stat call to get the size of a file. When a file is modified we listen for the event and
    update our cache.
    """

    def __init__(self):
        # this could potentially be an LRU Cache
        self.store = OrderedDict()
        self.inotify = INotify()
        self.watches = {}

    def get_file_stats(self, file):
        """
        takes absolute path to a file and returns the last modification time in unix timestamp and size
        in bytes.
        :param file: absolute path to a file
        :return: { timestamp, size}
        """
        try:
            return self.__get_item__(file)
        except KeyError:
            print("file %s is not present in the cache adding it "
                  "now and fetching the details using os.stat" % file)
            self.__add_file_to_watch__(file)
            return self.get_file_stats_using_stat(file)

    @staticmethod
    def get_file_stats_using_stat(file):
        if os.path.isfile(file):
            file_info = os.stat(file)
            return {"ts": file_info.st_mtime, "size": file_info.st_size}

    def __get_item__(self, file):
        return self.store[file]

    def start(self, files, timeout=None):
        """
        takes list of files and starts watching for changes using inotify from Linux.
        :param files: list of files to watch for changes, only absolute paths.
        :param timeout: timeout in seconds, default is forever :)
        """
        for file in files:
            # only if the file exists
            if os.path.isfile(file):
                self.store[file] = self.get_file_stats(file)
        thread = threading.Thread(target=self.__watch_files__, args=[timeout])
        thread.start()
        # self.__watch_files__(timeout)

    def stop(self):
        """
        will invalidate the current cache.
        """
        # TODO figure out a way to implement stopping the file watcher, timeout ?
        print("stop/invalidate the cache")

    def __watch_files__(self, timeout=None):
        for file in self.store:
            try:
                # for now only monitor modification of files
                print("adding %s to watch list" % file)
                wd = self.inotify.add_watch(file, flags.MODIFY)
                self.watches[wd] = file
            except FileNotFoundError:
                pass
        print("watch list %s " % self.watches)
        while True:
            for event in self.inotify.read(timeout):
                for flag in flags.from_mask(event.mask):
                    print(str(flag))
                    if flag == flags.MODIFY:
                        file = self.watches[event.wd]
                        print("modify event received for %s " % file)
                        self.store[file] = self.get_file_stats_using_stat(file)

                    elif flag == flags.DELETE | flags.IGNORED:
                        print("received delete event, removing %s from watch list" % file)
                        self.inotify.rm_watch(self.__get_key__(self.watches, file))
                        print("watch list %s " % self.watches)

    def __add_file_to_watch__(self, file):
        if os.path.isfile(file):
            wd = self.inotify.add_watch(file, flags.MODIFY)
            self.watches[wd] = file
        print("watch list %s " % self.watches)

    def __get_key__(self, watches, value):
        return [key for key in watches if (watches[key] == value)]


if __name__ == '__main__':
    cache = FStatCache()
    cache.start(["/tmp/test_file1","/tmp/test_file2"])
    print(cache.get_file_stats("/tmp/test_file1"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))