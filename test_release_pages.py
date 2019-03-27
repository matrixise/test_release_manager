#!/usr/bin/env python
import argparse
import hashlib
import re
import unittest
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class PreReleasePageTestCase(unittest.TestCase):
    URL = "https://www.python.org/download/pre-releases/"

    def test_01_has_status_200(self):
        response = requests.get(self.URL)
        self.assertEqual(response.status_code, 200)

    def test_has_reference_to_pre_release(self):
        response = requests.get(self.URL)

        soup = BeautifulSoup(response.content, "html.parser")

        links = soup.select("ul.simple > li> a.reference.external")

        self.assertTrue(
            self._has_link_with_pre_release(links, self.options['version']),
            f"There is no link to the pre-release version {self.options['version']}",
        )

    def _has_link_with_pre_release(self, links, version):
        download_url = f"/downloads/release/python-{self.options['compact_version']}/"
        return any(link.get("href") == download_url for link in links)


class DownloadPageTestCase(unittest.TestCase):
    URL = "https://www.python.org/downloads/release"

    @classmethod
    def setUpClass(cls):
        url = f"{cls.URL}/python-{cls.options['compact_version']}/"
        cls.response = requests.get(url)
        cls.soup = BeautifulSoup(cls.response.content, "html.parser")

    def test_01_has_status_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_has_right_title(self):
        page_title = self.soup.select_one("h1.page-title")
        self.assertIsNotNone(page_title)
        self.assertEqual(page_title.text, f"Python {self.options['version']}")

    def test_has_changelog_link(self):
        node = self.soup.find(string="Full Changelog")
        self.assertIsNotNone(node)
        link = node.parent

        self.assertTrue(link.has_attr("href"))

        url = urlparse(link.get("href"))
        self.assertEqual(url.scheme, "https")
        self.assertEqual(url.netloc, "docs.python.org")
        self.assertEqual(
            url.path,
            f"/{'.'.join(self.options['major_version'])}/whatsnew/changelog.html",
        )

        self.assertEqual(url.fragment, f"python-{self.options['expected_version']}")

    def test_files_section(self):
        node = self.soup.find(string="Files")
        self.assertIsNotNone(node)

        header = node.parent.parent
        table = header.parent.find("table")

        table_rows = table.select("tbody > tr")
        self.assertGreater(len(table_rows), 0)
        for line in table_rows:
            version_node = line.select_one("td:nth-of-type(1)")
            md5_sum = line.select_one("td:nth-of-type(4)").text.strip()
            file_size = int(line.select_one("td:nth-of-type(5)").text)

            resource_url = version_node.a.get("href")
            with self.subTest(
                msg=f"Downloading of {version_node.text} at {resource_url}",
                name=version_node.text,
                md5_sum=md5_sum,
                file_size=file_size,
            ):
                response = requests.get(version_node.a.get("href"))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(int(response.headers["content-length"]), file_size)

                signature = hashlib.md5()
                signature.update(response.content)
                self.assertEqual(md5_sum, signature.hexdigest())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=str, help="Version of Python: 3.8.0a3")
    parser.add_argument(
        "--pre-release",
        default=False,
        help="Test if the pre-release page has the right version",
        action="store_true",
    )

    args = parser.parse_args()

    result = "-".join(re.split(r"(\.|[a-b])", args.version))
    expected_version = (
        result.replace(".-", "").replace("a", "alpha").replace("b", "beta")
    )

    if not any(x in expected_version for x in ("alpha", "beta")):
        expected_version += "-final"

    return {
        "version": args.version,
        "pre_release": args.pre_release,
        "compact_version": args.version.replace(".", ""),
        "major_version": tuple(args.version.split(".")[:2]),
        "expected_version": expected_version,
    }


def suite(options):
    suite = unittest.TestSuite()
    test_cases = (DownloadPageTestCase, PreReleasePageTestCase)
    for test_case in test_cases:
        test_case.options = options

    loader = unittest.TestLoader()
    if options["pre_release"]:
        suite.addTest(loader.loadTestsFromTestCase(PreReleasePageTestCase))
    suite.addTest(loader.loadTestsFromTestCase(DownloadPageTestCase))
    return suite


def main():  # noqa
    args = parse_args()
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite(args))


__name__ == "__main__" and main()
