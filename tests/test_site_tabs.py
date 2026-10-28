from pathlib import Path
import unittest


class SiteTabRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (Path(__file__).parents[1] / "index.html").read_text()

    def test_removed_tabs_and_views_are_absent(self):
        for view in ("shop", "photos", "list"):
            self.assertNotIn(f'data-go="{view}"', self.html)
            self.assertNotIn(f'data-view="{view}"', self.html)

    def test_removed_tab_code_is_absent(self):
        for marker in (
            "const MERCH",
            "renderShop",
            "renderAlbums",
            "fillPhotoSelect",
            'id="shop"',
            'id="photoForm"',
            'id="listForm"',
        ):
            self.assertNotIn(marker, self.html)

    def test_core_tabs_remain(self):
        for view in ("home", "events", "contact"):
            self.assertIn(f'data-go="{view}"', self.html)
            self.assertIn(f'data-view="{view}"', self.html)


if __name__ == "__main__":
    unittest.main()
