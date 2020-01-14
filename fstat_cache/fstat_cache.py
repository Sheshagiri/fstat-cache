from collections import OrderedDict
import os.path
from inotify_simple import INotify, masks, flags
import threading


class FStatCache:
    """

    """
    def __init__(self):
        """

        :rtype: object
        """
        self.store = OrderedDict()

        monitor_thread = threading.Thread(target=self.__watch_files__)
        monitor_thread.start()
    """
    
    :rtype bytes
    """
    def get_file_size(self, file):
        try:
            return self.__get_item__(file)
        except KeyError:
            file_info = os.stat(file)
            file_size = file_info.st_size
            self.store[file] = file_size
            return file_info.st_size

    def __get_item__(self, file):
        return self.store[file]

    def __set_item(self, file, size):
        self.store[file] = size

    def __files_to_watch(self, inotify, flags):
        """
        watch all the files present in the store and return inotify watchers
        """
        watches = {}
        for file in self.store:
            try:
                wd = inotify.add_watch(file, flags)
                watches[wd] = file
            except FileNotFoundError:
                pass
        return watches

    def __watch_files__(self):
        inotify = INotify()
        watches = self.__files_to_watch(inotify, masks.ALL_EVENTS)
        while True:
            for event in inotify.read():
                print(event)
                for flag in flags.from_mask(event.mask):
                    print('    ' + str(flag))


if __name__ == '__main__':
    cache = FStatCache()
    cache.get_file_size("/Users/sheshagiri/scalyr.log")
