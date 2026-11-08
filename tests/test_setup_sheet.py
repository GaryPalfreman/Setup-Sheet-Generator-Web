import io
import json
import unittest

from PIL import Image
from setup_sheet import (
    TOOL_FIELDS, blank_tool, encode_image, export_json,
    generate_pdf_bytes, image_bytes, load_json_bytes,
)


def sample_image():
    image = Image.new("RGB", (400, 240), "white")
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class SetupSheetTests(unittest.TestCase):
    def setUp(self):
        self.inputs = {
            "Machine": "Test machine",
            "Program Name": "P100",
            "Drawing No + Revision": "D001-A",
            "Jaws/Fixture Name": "Soft jaws",
        }
        self.tools = [
            {"Tool No + Offset No": "T01", "Tool Type": "Drill", "Company Ref No": "REF-01"},
            {"Tool No + Offset No": "T02", "Tool Type": "End mill", "Company Ref No": "REF-02"},
        ]
        self.image = encode_image(sample_image())

    def test_company_reference_field(self):
        self.assertIn("Company Ref No", TOOL_FIELDS)
        self.assertNotIn("GE REF No", TOOL_FIELDS)
        self.assertIn("Company Ref No", blank_tool())

    def test_legacy_json_migrates(self):
        legacy = json.dumps({"user_inputs": self.inputs, "tool_inputs": [{"GE REF No": "OLD-001"}]}).encode()
        inputs, tools, images, holding = load_json_bytes(legacy)
        self.assertEqual(tools[0]["Company Ref No"], "OLD-001")
        self.assertEqual(images, [None])
        self.assertIsNone(holding)

    def test_images_round_trip(self):
        payload = export_json(self.inputs, self.tools, [self.image, None], self.image)
        inputs, tools, images, holding = load_json_bytes(payload)
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0], self.image)
        self.assertIsNone(images[1])
        self.assertEqual(holding, self.image)
        self.assertTrue(image_bytes(images[0]).startswith(b"\\xff\\xd8"))

    def test_pdf_with_all_images(self):
        pdf = generate_pdf_bytes(self.inputs, self.tools, tool_images=[self.image, self.image], work_holding_image=self.image)
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 1000)

    def test_pdf_without_images(self):
        pdf = generate_pdf_bytes(self.inputs, self.tools)
        self.assertTrue(pdf.startswith(b"%PDF-"))


if __name__ == "__main__":
    unittest.main()
