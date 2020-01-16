from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
from threading import Thread
import time


__all__ = ['FStatCache']


class MonitorThread:
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self, inotify, store, watches, timeout):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        os.system("echo start=" + now + " GMT >> " + FStatCache.self_stats_file)
        store[FStatCache.self_stats_file] = FStatCache.get_file_stats_using_stat(FStatCache.self_stats_file)
        for file in store:
            try:
                # for now only monitor modification of files
                print("adding %s to watch list" % file)
                wd = inotify.add_watch(file, flags.MODIFY)
                watches[wd] = file
            except FileNotFoundError:
                pass

        print("watch list %s " % watches)
        while self._running:
            for event in inotify.read(timeout=10):
                for flag in flags.from_mask(event.mask):
                    if flag == flags.MODIFY:
                        file = watches[event.wd]
                        print("modify event received for %s " % file)
                        store[file] = FStatCache.get_file_stats_using_stat(file)
                    # don't know if its bug in inotify_simple but we get IGNORED event when a file is deleted
                    elif flag == flags.DELETE | flags.IGNORED:
                        print("received delete event, removing %s from watch list" % file)
                        inotify.rm_watch(FStatCache.__get_key__(watches, file))
                        print("watch list %s " % watches)


class FStatCache:
    """
    Simple caching mechanism using inotify functionality from linux to avoid expensive repeated
    os.stat call to get the size of a file. When a file is modified we listen for the event and
    update our cache.
    """
    self_stats_file = "/tmp/fstat-cache-stats"
    thread_name = "fstatcache"

    def __init__(self, timeout=None):
        # this could potentially be an LRU Cache
        self.store = OrderedDict()
        self.inotify = INotify()
        self.watches = {}
        self.monitor = MonitorThread()
        self.monitor_thread = Thread(target=self.monitor.run, args=(self.inotify, self.store, self.watches, timeout, ))

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
            return self.__add_file_to_watch__(file)

    @staticmethod
    def get_file_stats_using_stat(file):
        if os.path.isfile(file):
            file_info = os.stat(file)
            return {"ts": file_info.st_mtime, "size": file_info.st_size}

    def __get_item__(self, file):
        return self.store[file]

    def __set_item__(self, file, stats):
        self.store[file] = stats

    def build(self, files):
        """
        takes list of files and starts watching for changes using inotify from Linux.
        :param files: list of files to watch for changes, only absolute paths.
        """
        for file in files:
            # only if the file exists
            if os.path.isfile(file):
                self.store[file] = self.get_file_stats(file)
        self.monitor_thread.start()

    def invalidate(self):
        """
        will invalidate the current cache and remove all the files from the watcher.
        """
        self.monitor.terminate()
        self.monitor_thread.join()
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        os.system("echo stop=" + now + " GMT >> " + FStatCache.self_stats_file)
        self.__unwatch_all_files__()

    def __add_file_to_watch__(self, file):
        if os.path.isfile(file):
            wd = self.inotify.add_watch(file, flags.MODIFY)
            self.watches[wd] = file

        print("watch list %s " % self.watches)
        stats = self.get_file_stats_using_stat(file)
        self.__set_item__(file, stats)
        return stats

    def __unwatch_all_files__(self):
        for wd in self.watches:
            print("removing %s from watch list" % self.watches[wd])
            self.inotify.rm_watch(wd)

    def __remove_from_watch__(self, file):
        self.inotify.rm_watch(FStatCache.__get_key__(self.watches, file))

    @staticmethod
    def __get_key__(watches, value):
        return [key for key in watches if (watches[key] == value)]


if __name__ == '__main__':
    cache = FStatCache()
    cache.build(["/tmp/test_file1", "/tmp/test_file2"])
    print(cache.get_file_stats("/tmp/test_file1"))
    time.sleep(6)
    cache.invalidate()
'''
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
    time.sleep(10)
    print(cache.get_file_stats("/tmp/test_file3"))
'''
