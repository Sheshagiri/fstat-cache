import unittest
import fstat_cache
import os
# TODO
# I seem to have messed up the package nosetests is not able to find the class
# instead using this command to run the tests python -m unittest test_fstat_cache.FStatCacheTestCase


class FStatCacheTestCase(unittest.TestCase):
    def setUp(self) -> None:
        os.system("echo \"validate\" >> /tmp/test_file_1")
        os.system("echo \"validate again\" >> /tmp/test_file_2")
        self.cache = fstat_cache.FStatCache()
        self.cache.start(["/tmp/test_file_1"])

    def test_get_file_size_from_cache(self) -> None:
        print("inside test_get_file_size_from_cache")
        # "validate" is 9 bytes
        self.assertEqual(9, self.cache.get_file_stats("/tmp/test_file_1")['size'])

    def test_get_file_size_using_stat(self) -> None:
        print("inside test_get_file_size_using_stat")
        # "validate \n validate again" is 15 bytes
        self.assertEqual(15, self.cache.get_file_stats("/tmp/test_file_2")['size'])

    def tearDown(self) -> None:
        self.cache.stop()
        os.system("rm -rf /tmp/test_file_1 /tmp/test_file_2")


if __name__ == '__main__':
    unittest.main()
