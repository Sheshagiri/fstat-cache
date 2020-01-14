from collections import OrderedDict
import os.path
import inotify.adapters


class FStatCache:
    def __init__(self, list_of_files):
        self.store = OrderedDict()
        self.watcher = inotify.adapters.Inotify()
        self.__watch_files__(list_of_files)

    def get_file_size(self, file):
        print(self.store)
        try:
            return self.__get_item__(file)
        except KeyError:
            raise ValueError(file + " is not being monitored currently")

    def __get_item__(self, file):
        return self.store[file]

    def __set_item(self, file, size):
        self.store[file] = size

    def __watch_files__(self, list_of_files):
        for file in list_of_files:
            print("file to watch " + file)
            self.watcher.add_watch(file)

        for event in self.watcher.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_names))


if __name__ == '__main__':
    cache = FStatCache(["/tmp/test_file1","/tmp/test_file2"])
    print(cache.get_file_size("/tmp/test_file2"))
