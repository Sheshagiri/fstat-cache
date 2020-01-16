import unittest
import fstat_cache
import os


class FStatCacheTestCase(unittest.TestCase):
    def setUpClass(self) -> None:
        print("inside setUp")
        os.system("echo \"validate\" >> /tmp/test_file_1")
        os.system("echo \"validate again\" >> /tmp/test_file_2")
        self.cache = fstat_cache.FStatCache()
        self.cache.start(["/tmp/test_file_1"])

    def test_get_file_size_from_cache(self) -> None:
        print("inside test_get_file_size_from_cache")
        self.assertEqual(9, self.cache.get_file_stats("/tmp/test_file_1")['size'])

    def test_get_file_size_using_stat(self) -> None:
        print("inside test_get_file_size_using_stat")
        self.assertEqual(15, self.cache.get_file_stats("/tmp/test_file_2")['size'])

    def tearDownClass(self) -> None:
        print("inside teardown")
        os.system("rm -rf /tmp/test_file_1 /tmp/test_file_2")
        self.cache.stop()


if __name__ == '__main__':
        unittest.main()