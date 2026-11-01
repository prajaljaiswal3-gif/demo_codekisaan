import unittest
from app import create_app
from app.services.weather_service import get_weather_data
from app.services.ai_detector import analyze_leaf_image
from app.config import Config

class CodeKisaanTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

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

    def test_advisory_page(self):
        response = self.client.get("/advisory?crop=Cotton")
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
        print(f"[Test] AI Analysis Result: {result['disease_en'].encode('ascii', 'replace').decode('ascii')} (Confidence: {result['confidence']}%, Mode: {result['model_mode']})")

if __name__ == "__main__":
    unittest.main()
