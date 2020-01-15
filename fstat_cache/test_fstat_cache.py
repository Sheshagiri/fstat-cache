import unittest
import fstat_cache
import os


class FStatCacheTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.system("echo \"validate\" >> /tmp/test_file_1")
        os.system("echo \"validate again\" >> /tmp/test_file_2")
        self.cache = fstat_cache.FStatCache(["/tmp/test_file_1"])

    def test_get_file_size_from_cache(self) -> None:
        print("inside test_get_file_size_from_cache")
        self.assertEqual(6, self.cache.get_file_size("/tmp/test_file_1"))

    def test_get_file_size_using_stat(self) -> None:
        print("inside test_get_file_size_using_stat")
        self.assertEqual(6, self.cache.get_file_size("/tmp/test_file_2"))

    def tearDown(self) -> None:
        os.system("rm -rf /tmp/test_file_1 /tmp/test_file_2")