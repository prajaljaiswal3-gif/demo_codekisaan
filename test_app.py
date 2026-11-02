import io
import sys
import unittest
from PIL import Image

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app
from app.services.weather_service import get_weather_data
from app.services.ai_detector import analyze_leaf_image
from app.config import Config

class CodeKisaanTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.uploaded_files_before = set(Config.UPLOAD_FOLDER.glob("*")) if Config.UPLOAD_FOLDER.exists() else set()

    def tearDown(self):
        # Clean up any files created during tests
        if Config.UPLOAD_FOLDER.exists():
            for f in Config.UPLOAD_FOLDER.glob("*"):
                if f not in self.uploaded_files_before and f.name.startswith(("scan_", "sample_1")):
                    try:
                        f.unlink()
                    except Exception:
                        pass

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CodeKisaan", response.data)

    def test_dashboard(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"cropHealthChart", response.data)

    def test_disease_scan_page(self):
        response = self.client.get("/disease/scan")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"leafDropzone", response.data)

    def test_weather_page(self):
        response = self.client.get("/weather?district=Nashik")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Nashik", response.data)

    def test_weather_page_case_insensitive(self):
        response = self.client.get("/weather?district=pune")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Pune", response.data)

    def test_advisory_page(self):
        response = self.client.get("/advisory?crop=Cotton")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cotton", response.data)

    def test_advisory_page_case_insensitive(self):
        response = self.client.get("/advisory?crop=cotton")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Cotton", response.data)

    def test_about_page(self):
        response = self.client.get("/about")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Seva Innovation Challenge", response.data)

    def test_contact_page(self):
        response = self.client.get("/contact")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1800-180-1551", response.data)

    def test_404_error_page(self):
        response = self.client.get("/non-existent-page-url")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404", response.data)

    def test_language_switch(self):
        response = self.client.get("/set-language/en?next=/about")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/about")

    def test_language_switch_open_redirect_protection(self):
        response = self.client.get("/set-language/hi?next=https://malicious-site.com")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, "/")

    def test_feedback_submission(self):
        response = self.client.post("/feedback", data={
            "farmer_name": "Test Farmer",
            "contact_number": "9876543210",
            "district": "Pune",
            "crop_type": "Cotton",
            "message": "Testing farm inquiry submission."
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_feedback_validation_missing_fields(self):
        response = self.client.post("/feedback", data={
            "farmer_name": "",
            "message": ""
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_disease_analyze_sample(self):
        response = self.client.post("/disease/analyze", data={
            "crop_name": "Cotton",
            "sample_image_name": "sample_cotton_leaf.jpg"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_disease_analyze_file_upload(self):
        # Create an in-memory test image
        img_io = io.BytesIO()
        img = Image.new("RGB", (120, 120), color=(40, 160, 40))
        img.save(img_io, "JPEG")
        img_io.seek(0)

        response = self.client.post("/disease/analyze", data={
            "crop_name": "Cotton",
            "leaf_image": (img_io, "test_leaf.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_disease_result_view(self):
        # Valid ID 1 (seeded scan)
        response = self.client.get("/disease/result/1")
        self.assertEqual(response.status_code, 200)
        # Invalid ID redirects to scan page
        response_invalid = self.client.get("/disease/result/999999")
        self.assertEqual(response_invalid.status_code, 302)

    def test_weather_service_live(self):
        data = get_weather_data("Pune")
        self.assertIsNotNone(data)
        self.assertIn("temperature", data)
        self.assertIn("humidity", data)
        self.assertIn("risk", data)
        print(f"\n[Test] Live Weather Data: {data['district']} Temp={data['temperature']}C Humidity={data['humidity']}%")

    def test_ai_disease_analysis(self):
        sample_path = Config.BASE_DIR / "app" / "static" / "img" / "samples" / "sample_cotton_leaf.jpg"
        self.assertTrue(sample_path.exists())
        result = analyze_leaf_image(sample_path, crop_hint="Cotton")
        self.assertEqual(result["crop"], "Cotton")
        self.assertGreater(result["confidence"], 50.0)
        self.assertIn("organic_remedy", result)
        self.assertIn("chemical_remedy", result)
        self.assertIn("model_mode", result)
        print(f"[Test] AI Analysis Result: {result['disease_en']} (Confidence: {result['confidence']}%, Mode: {result['model_mode']})")

if __name__ == "__main__":
    unittest.main()
