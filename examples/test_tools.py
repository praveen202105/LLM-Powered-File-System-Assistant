"""
Unit tests for fs_tools module.
Tests all file system operations: read, write, list, and search.
"""

import unittest
import tempfile
import os
from pathlib import Path

from backend.fs_tools import read_file, list_files, write_file, search_in_file


class TestReadFile(unittest.TestCase):
    """Test cases for read_file function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_txt_file(self):
        """Test reading a plain text file."""
        test_file = Path(self.test_dir) / "test.txt"
        test_content = "Hello World\nThis is a test file"
        test_file.write_text(test_content)

        result = read_file(str(test_file))

        self.assertTrue(result["success"])
        self.assertEqual(result["content"], test_content)
        self.assertEqual(result["metadata"]["word_count"], 7)
        self.assertEqual(result["metadata"]["file_type"], ".txt")

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        result = read_file("/nonexistent/path/file.txt")

        self.assertFalse(result["success"])
        self.assertIn("File not found", result["error"])

    def test_read_directory_as_file(self):
        """Test reading a directory (should fail)."""
        result = read_file(self.test_dir)

        self.assertFalse(result["success"])
        self.assertIn("not a file", result["error"])

    def test_read_file_metadata(self):
        """Test that metadata is correctly extracted."""
        test_file = Path(self.test_dir) / "metadata_test.txt"
        content = "Test content for metadata"
        test_file.write_text(content)

        result = read_file(str(test_file))

        self.assertTrue(result["success"])
        self.assertIn("size_bytes", result["metadata"])
        self.assertIn("modified_date", result["metadata"])
        self.assertIn("word_count", result["metadata"])
        self.assertEqual(result["metadata"]["word_count"], 4)


class TestListFiles(unittest.TestCase):
    """Test cases for list_files function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

        Path(self.test_dir, "file1.txt").write_text("content1")
        Path(self.test_dir, "file2.txt").write_text("content2")
        Path(self.test_dir, "file3.pdf").write_text("pdf content")
        Path(self.test_dir, "subdir").mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_list_all_files(self):
        """Test listing all files in a directory."""
        result = list_files(self.test_dir)

        self.assertEqual(len(result), 3)
        filenames = {f["filename"] for f in result}
        self.assertEqual(filenames, {"file1.txt", "file2.txt", "file3.pdf"})

    def test_list_files_by_extension(self):
        """Test listing files filtered by extension."""
        result = list_files(self.test_dir, ".txt")

        self.assertEqual(len(result), 2)
        for file in result:
            self.assertEqual(file["file_type"], ".txt")

    def test_list_files_different_extension(self):
        """Test filtering by different extension."""
        result = list_files(self.test_dir, ".pdf")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["filename"], "file3.pdf")

    def test_list_files_nonexistent_directory(self):
        """Test listing files in nonexistent directory."""
        result = list_files("/nonexistent/path")

        self.assertEqual(result, [])

    def test_list_files_empty_directory(self):
        """Test listing files in empty directory."""
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir()

        result = list_files(str(empty_dir))

        self.assertEqual(result, [])

    def test_list_files_sorting(self):
        """Test that files are sorted by modified date (newest first)."""
        result = list_files(self.test_dir)

        if len(result) > 1:
            for i in range(len(result) - 1):
                self.assertGreaterEqual(
                    result[i]["modified_date"],
                    result[i + 1]["modified_date"]
                )


class TestWriteFile(unittest.TestCase):
    """Test cases for write_file function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_new_file(self):
        """Test writing a new file."""
        filepath = Path(self.test_dir) / "newfile.txt"
        content = "This is new content"

        result = write_file(str(filepath), content)

        self.assertTrue(result["success"])
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.read_text(), content)

    def test_write_file_creates_directories(self):
        """Test that write_file creates parent directories."""
        filepath = Path(self.test_dir) / "subdir1" / "subdir2" / "file.txt"
        content = "nested file content"

        result = write_file(str(filepath), content)

        self.assertTrue(result["success"])
        self.assertTrue(filepath.exists())
        self.assertEqual(filepath.read_text(), content)

    def test_overwrite_existing_file(self):
        """Test overwriting an existing file."""
        filepath = Path(self.test_dir) / "existing.txt"
        filepath.write_text("old content")

        new_content = "new content"
        result = write_file(str(filepath), new_content)

        self.assertTrue(result["success"])
        self.assertIn("Overwriting", result["message"])
        self.assertEqual(filepath.read_text(), new_content)

    def test_write_file_size_tracking(self):
        """Test that written file size is tracked."""
        filepath = Path(self.test_dir) / "sized.txt"
        content = "content"

        result = write_file(str(filepath), content)

        self.assertTrue(result["success"])
        self.assertEqual(result["size_bytes"], len(content))


class TestSearchInFile(unittest.TestCase):
    """Test cases for search_in_file function."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

        self.test_file = Path(self.test_dir) / "search_test.txt"
        content = """Python is a great language.
I love Python programming.
Java is also popular.
Let's learn Python together.
Go is fast and efficient."""
        self.test_file.write_text(content)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_search_keyword_found(self):
        """Test searching for a keyword that exists."""
        result = search_in_file(str(self.test_file), "Python")

        self.assertTrue(result["success"])
        self.assertEqual(result["match_count"], 3)
        self.assertEqual(len(result["matches"]), 3)

    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        result = search_in_file(str(self.test_file), "python")

        self.assertTrue(result["success"])
        self.assertEqual(result["match_count"], 3)

    def test_search_keyword_not_found(self):
        """Test searching for a keyword that doesn't exist."""
        result = search_in_file(str(self.test_file), "Rust")

        self.assertTrue(result["success"])
        self.assertEqual(result["match_count"], 0)
        self.assertEqual(len(result["matches"]), 0)

    def test_search_returns_context(self):
        """Test that search results include context lines."""
        result = search_in_file(str(self.test_file), "programming")

        self.assertTrue(result["success"])
        self.assertEqual(result["match_count"], 1)
        match = result["matches"][0]

        self.assertIn("context_before", match)
        self.assertIn("context_after", match)
        self.assertEqual(match["line_number"], 2)

    def test_search_nonexistent_file(self):
        """Test searching in a file that doesn't exist."""
        result = search_in_file("/nonexistent/file.txt", "keyword")

        self.assertFalse(result["success"])
        self.assertEqual(result["match_count"], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple operations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_and_read(self):
        """Test writing a file and reading it back."""
        filepath = Path(self.test_dir) / "integration.txt"
        original_content = "Integration test content"

        write_result = write_file(str(filepath), original_content)
        self.assertTrue(write_result["success"])

        read_result = read_file(str(filepath))
        self.assertTrue(read_result["success"])
        self.assertEqual(read_result["content"], original_content)

    def test_write_read_and_search(self):
        """Test write, read, and search operations together."""
        filepath = Path(self.test_dir) / "workflow.txt"
        content = "Python is great. I love Python. Python programming is fun."

        write_file(str(filepath), content)
        search_result = search_in_file(str(filepath), "Python")

        self.assertTrue(search_result["success"])
        self.assertEqual(search_result["match_count"], 3)

    def test_list_write_and_list(self):
        """Test listing files before and after writing."""
        initial_files = list_files(self.test_dir)
        self.assertEqual(len(initial_files), 0)

        write_file(Path(self.test_dir) / "new.txt", "content")
        after_write = list_files(self.test_dir)

        self.assertEqual(len(after_write), 1)


if __name__ == "__main__":
    unittest.main()
