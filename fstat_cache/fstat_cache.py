from collections import OrderedDict
from os import stat
import os.path
import asyncio
import pyinotify
import time
import sys

__all__ = ["FStatCache"]


class FStatCache:
    """
    Simple caching mechanism using inotify functionality from linux to avoid expensive repeated
    os.stat call to get the size of a file. When a file is modified we listen for the event and
    update our cache.
    """
    def __init__(self, list_of_files):
        self.store = OrderedDict()
        for file in list_of_files:
            if os.path.isfile(file):
                self.__set_item__(file, self.__get_file_stats__(file))
        self.wm = pyinotify.WatchManager()
        self.loop = asyncio.get_event_loop()
        self.notifier = pyinotify.AsyncioNotifier(self.wm, self.loop, callback=self.handle_change_event)
        self.__watch_files__(list_of_files)

    def handle_change_event(self, notifier):
        """
        Just stop receiving IO read events after the first
        iteration (unrealistic example).
        """
        print('handle_read callback')
        # notifier.loop.stop()

    def get_file_stats(self, file) -> int:
        """
        fetches the last modification time and size of the given file, from the cache if present else by calling
        the os.stat function.
        :param file: absolute path to the file
        :return: time in unix timestamp and size in bytes
        """
        try:
            return self.__get_item__(file)
        except KeyError:
            # TODO: handle dynamically adding the file to watcher
            if not os.path.isfile(file):
                raise FileNotFoundError(file)
            print("file %s is not being watched, fetching details using os.stat instead" % file)
            return self.__get_file_stats__(file)

    def __get_item__(self, file) -> int:
        return self.store[file]

    def __set_item__(self, file, size) -> None:
        self.store[file] = size

    @staticmethod
    def __get_file_stats__(file):
        """
        fetches last modification time and size of of the given file by calling os.stat function.
        :param file: absolute path to the file
        :return: date in unix timestamp and size in bytes
        """
        file_info = stat(file)
        return file_info.st_mtime, file_info.st_size

    def __watch_files__(self, list_of_files):
        for file in list_of_files:
            try:
                print("file to watch " + file)
                self.wm.add_watch('/tmp', pyinotify.IN_MODIFY)
            except FileNotFoundError:
                print("no such file: , skipping it " + file)
        self.loop.run_forever()

    def stop(self):
        print("stopping now")
        self.notifier.stop()
        sys.exit(0)


if __name__ == '__main__':
    cache = FStatCache(["/tmp/test_file1", "/tmp/test_file2"])

    # print(cache.get_file_stats("/tmp/test_file2"))
    time.sleep(10)
    cache.stop()

