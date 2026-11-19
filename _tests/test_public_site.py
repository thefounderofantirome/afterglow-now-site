from html.parser import HTMLParser
from pathlib import Path
import unittest
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
HOST = (ROOT / "CNAME").read_text().strip()


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.urls = []
        self.ids = set()
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if key in attrs:
                self.urls.append(attrs[key])


class PublicSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {p.name: Page(p) for p in ROOT.glob("*.html")}

    def test_links_assets_and_fragments_resolve(self):
        for name, page in self.pages.items():
            for url in page.urls:
                with self.subTest(page=name, url=url):
                    dest = urlsplit(urljoin(f"https://{HOST}/{name}", url))
                    if dest.hostname == HOST:
                        path = dest.path.strip("/") or "index.html"
                        self.assertTrue((ROOT / path).is_file(), path)
                        if dest.fragment:
                            self.assertIn(dest.fragment, self.pages[path].ids)

    def test_public_contact_on_each_page(self):
        for name, page in self.pages.items():
            with self.subTest(page=name):
                self.assertIn(f"mailto:support@{HOST}", page.urls)

    def test_company_details_link_to_official_registry(self):
        self.assertTrue(any(urlsplit(url).hostname in ("www.cr.gov.hk", "www.e-services.cr.gov.hk")
                            for url in self.pages["index.html"].urls),
                        "Company details should link to the public Companies Registry search")

    def test_sitemap_covers_public_pages(self):
        urls = ElementTree.parse(ROOT / "sitemap.xml").findall(".//{*}loc")
        self.assertEqual({url.text for url in urls},
                         {f"https://{HOST}/" + ("" if name == "index.html" else name)
                          for name in self.pages})


if __name__ == "__main__":
    unittest.main()
