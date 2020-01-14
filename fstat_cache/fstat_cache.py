from collections import OrderedDict
import inotify.adapters
import inotify.constants
from os import stat
import os.path


class FStatCache:
    def __init__(self, list_of_files):
        self.store = OrderedDict()
        self.watcher = inotify.adapters.Inotify()
        self.__watch_files__(list_of_files)

    def get_file_size(self, file):
        """
        fetches the size of the given file, from the cache if present else by calling
        the os.stat function.
        :param file: absolute path to the file
        :return: size of the file in bytes
        """
        try:
            return self.__get_item__(file)
        except KeyError:
            if not os.path.isfile(file):
                raise FileNotFoundError(file)
            print("file %s is not being watched, fetching details using os.stat instead" % file)
            return self.__get_file_using_stat(file)

    def __get_item__(self, file):
        return self.store[file]

    def __set_item(self, file, size):
        self.store[file] = size

    @staticmethod
    def __get_file_using_stat(file):
        """
        fetches size of the given file in bytes by calling os.stat function.
        :param file: absolute path to the file
        :return: size of the file in bytes
        """
        return stat(file).st_size

    def __watch_files__(self, list_of_files):
        for file in list_of_files:
            try:
                print("file to watch " + file)
                self.watcher.add_watch(file)
            except FileNotFoundError:
                print("no such file: , skipping it " + file)

        for event in self.watcher.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format(path, filename, type_names))
            if type_names[0] == "IN_CLOSE_WRITE":
                file_size = self.__get_file_using_stat(path)
                print("update the size of %s to %s" % (path, file_size))
                self.store[path] = file_size


if __name__ == '__main__':
    cache = FStatCache(["/tmp/test_file1","/tmp/test_file2"])
    print(cache.get_file_size("/tmp/test_file2"))
