import unittest
import fstat_cache
import os
import tempfile


class FStatCacheTestCase(unittest.TestCase):
    file_paths = []

    def setUp(self) -> None:
        _, file_path_1 = tempfile.mkstemp()
        _, file_path_2 = tempfile.mkstemp()

        self.file_paths = [file_path_1, file_path_2]

        self._write_to_file(file_path_1, 'validate', 'a')
        self._write_to_file(file_path_2, 'validate again', 'a')

        self.cache = fstat_cache.FStatCache()
        self.cache.build([file_path_1])

    def test_get_file_size_from_cache(self) -> None:
        print("inside test_get_file_size_from_cache")
        expected_len = len('validate')
        file_path = self.file_paths[0]
        self.assertEqual(expected_len, self.cache.get_file_stats(file_path)['size'])

    def test_get_file_size_using_stat(self) -> None:
        print("inside test_get_file_size_using_stat")
        expected_len = len('validate again')
        file_path = self.file_paths[1]
        self.assertEqual(expected_len, self.cache.get_file_stats(file_path)['size'])

    def test_list_files_in_cache(self) -> None:
        self.assertEqual(self.file_paths[0], self.cache.list_files_in_cache()[0])

    def test_add_file_to_watch_and_remove(self) -> None:
        _, random_file = tempfile.mkstemp()
        self.cache.add_file_to_watch(random_file)
        self.assertIn(random_file, self.cache.list_files_in_cache())
        self._write_to_file(random_file, "some random data")
        self.cache.remove_from_watch(random_file)
        self.assertNotIn(random_file, self.cache.list_files_in_cache())
        self.assertRaises(KeyError, lambda: self.cache.remove_from_watch("validate"))

    def tearDown(self) -> None:
        self.cache.invalidate()

        for file_path in self.file_paths:
            if os.path.isfile(file_path):
                os.remove(file_path)

    def _write_to_file(self, file_path: str, data: str, file_mode: str = 'a') -> None:
        with open(file_path, file_mode) as fp:
            fp.write(data)


if __name__ == '__main__':
    unittest.main()
