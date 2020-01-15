from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
import threading
import time


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
            # TODO stop gap until I figure out the actual way of dynamically updating the watch list
            print("file is not being watched, fetching details using os.stat")
            file_info = os.stat(file)
            return {file_info.st_mtime, file_info.st_size}

    def __get_item__(self, file):
        return self.store[file]

    def __set_item__(self, file, ts, size):
        self.store[file] = {ts, size}

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
        watches = {}
        for file in self.store:
            try:
                # for now only monitor modification of files
                print("adding %s to watch list" % file)
                wd = self.inotify.add_watch(file, flags.MODIFY)
                watches[wd] = file
            except FileNotFoundError:
                pass
        while True:
            for event in self.inotify.read(timeout):
                for flag in flags.from_mask(event.mask):
                    if flag == flags.CLOSE_WRITE:
                        file = watches[event.wd]
                        print("modify event received for %s " % file)
                        ts, size = self.get_file_stats(file)
                        self.__set_item__(file, ts, size)
                        print(self.get_file_stats(file))
                        print(self.store[file])


if __name__ == '__main__':
    cache = FStatCache()
    cache.start(["/tmp/test_file1"])
    print(cache.get_file_stats("/tmp/test_file1"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file1"))