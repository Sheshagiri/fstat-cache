from collections import OrderedDict
from inotify_simple import INotify, flags
import os.path
from threading import Thread
import time


__all__ = ['FStatCache']


class MonitorThread(Thread):
    def __init__(self):
        self._running = True

    def terminate(self):
        self._running = False

    def run(self, inotify, store, watches, timeout):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        os.system("echo start=" + now + " GMT >> " + FStatCache.self_stats_file)
        store[FStatCache.self_stats_file] = FStatCache.get_file_stats_using_stat(FStatCache.self_stats_file)
        for file_path in store:
            try:
                # for now only monitor modification of files
                print("adding %s to watch list" % file_path)
                wd = inotify.add_watch(file_path, flags.MODIFY)
                watches[wd] = file_path
            except FileNotFoundError:
                pass

        print("watch list %s " % watches)
        while self._running:
            for event in inotify.read(timeout=timeout):
                for flag in flags.from_mask(event.mask):
                    if flag == flags.MODIFY:
                        file_path = watches[event.wd]
                        print("modify event received for %s " % file_path)
                        store[file_path] = FStatCache.get_file_stats_using_stat(file_path)
                    # don't know if its bug in inotify_simple but we get IGNORED event when a file is deleted
                    elif flag == flags.DELETE | flags.IGNORED:
                        print("received delete event, removing %s from watch list" % file_path)
                        # NOTE: inoitfy already delets a watch on file delete so
                        # we don't need to call rm_watch outselves
                        # inotify.rm_watch(event.wd)
                        del watches[event.wd]
                        print("watch list: %s " % watches)


class FStatCache(object):
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

    def get_file_stats(self, file_path):
        """
        takes absolute path to a file and returns the last modification time in unix timestamp and size
        in bytes.
        :param file_path: absolute path to a file
        :return: { timestamp, size}
        """
        try:
            return self.__get_item__(file_path)
        except KeyError:
            print("file %s is not present in the cache adding it "
                  "now and fetching the details using os.stat" % file_path)
            return self.__add_file_to_watch__(file_path)

    @staticmethod
    def get_file_stats_using_stat(file_path):
        if os.path.isfile(file_path):
            file_info = os.stat(file_path)
            return {"ts": file_info.st_mtime, "size": file_info.st_size}

    def __get_item__(self, file_path):
        return self.store[file_path]

    def __set_item__(self, file_path, stats):
        self.store[file_path] = stats

    def build(self, file_paths):
        """
        takes list of files and starts watching for changes using inotify from Linux.
        :param file_paths: list of files to watch for changes, only absolute paths.
        """
        for file_path in file_paths:
            # only if the file exists
            if os.path.isfile(file_path):
                self.store[file_path] = self.get_file_stats(file_path)
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

    def __add_file_to_watch__(self, file_path):
        if os.path.isfile(file_path):
            wd = self.inotify.add_watch(file_path, flags.MODIFY)
            self.watches[wd] = file_path

        print("watch list: %s " % self.watches)
        stats = self.get_file_stats_using_stat(file_path)
        self.__set_item__(file_path, stats)
        return stats

    def __unwatch_all_files__(self):
        for wd in self.watches:
            print("removing %s from watch list" % self.watches[wd])
            self.inotify.rm_watch(wd)

    def __remove_from_watch__(self, file_path):
        self.inotify.rm_watch(FStatCache.__get_key__(self.watches, file_path))

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
