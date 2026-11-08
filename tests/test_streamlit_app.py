import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class StreamlitAppTests(unittest.TestCase):
    def test_app_starts_and_renders(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception, [str(e.message) for e in app.exception])
        headings = [item.value for item in app.subheader]
        self.assertIn("2. Tool data", headings)
        self.assertIn("3. Tool Images", headings)
        self.assertIn("4. Work Holding Image", headings)
        self.assertIn("5. Generate files", headings)


if __name__ == "__main__":
    unittest.main()
