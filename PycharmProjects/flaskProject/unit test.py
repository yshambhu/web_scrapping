import unittest
import os
from app import (extract_content, write_to_csv, crawl, extract_links_from_url)

class TestWebScraper(unittest.TestCase):
    def setUp(self):

       pass

    def tearDown(self):

        pass

    def test_extract_content(self):
        url = 'https://www.chester.ac.uk/'
        extracted_data = extract_content(url, extract_links=True, extract_images=True)
        self.assertIsInstance(extracted_data, list)


    def test_write_to_csv(self):
        data = [('Title', 'Description'), ('Item 1', 'Description 1'), ('Item 2', 'Description 2')]
        filename = 'test_output.csv'
        write_to_csv(data, filename)
        self.assertTrue(os.path.exists(filename))


    def test_crawl(self):
        # example of website of url for testing
        url = 'https://www.chester.ac.uk/'
        max_depth = 2
        crawl(url, max_depth)


    def test_extract_links_from_url(self):
        # Test if extract_links_from_url function extracts links from a webpage
        # example of url
        url = 'https://www.chester.ac.uk/'
        links = extract_links_from_url(url)
        self.assertIsInstance(links, list)


if __name__ == '__main__':
    unittest.main()
