"""
test_app.py
=================================================
Test suite for BreachAlert API with database persistence.
Uses an in-memory SQLite database for fast, isolated tests.

Run:
    python -m unittest test_app.py -v
"""

import unittest

from app import app, db, User, Scan, _request_log


class BreachAlertDatabaseTests(unittest.TestCase):

    def setUp(self):
        """Create a test database in memory for each test."""
        # Use in-memory SQLite for fast, isolated tests
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_ECHO'] = False

        self.client = app.test_client()

        # Reset rate limiter between tests
        _request_log.clear()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up test database."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    # -----------------------------------------------------------
    # Health check
    # -----------------------------------------------------------
    def test_health_check_returns_200(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")
        self.assertIn("database", response.get_json())

    # -----------------------------------------------------------
    # POST /api/v1/scans with persistence
    # -----------------------------------------------------------
    def test_create_scan_persists_to_database(self):
        response = self.client.post("/api/v1/scans", json={"email": "test@example.com"})
        self.assertEqual(response.status_code, 201)

        scan_id = response.get_json()["id"]

        # Verify it's in the database
        with app.app_context():
            scan = Scan.query.filter_by(id=scan_id).first()
            self.assertIsNotNone(scan)
            self.assertEqual(scan.email_checked, "test@example.com")

    def test_create_scan_creates_user_record(self):
        response = self.client.post("/api/v1/scans", json={"email": "newuser@example.com"})
        self.assertEqual(response.status_code, 201)

        with app.app_context():
            user = User.query.filter_by(email="newuser@example.com").first()
            self.assertIsNotNone(user)
            self.assertEqual(len(user.scans), 1)

    def test_multiple_scans_same_user_creates_one_user_record(self):
        email = "recurring@example.com"

        # Scan 1
        self.client.post("/api/v1/scans", json={"email": email})
        # Scan 2
        self.client.post("/api/v1/scans", json={"email": email})

        with app.app_context():
            user = User.query.filter_by(email=email.lower()).first()
            self.assertIsNotNone(user)
            self.assertEqual(len(user.scans), 2)

    def test_create_scan_with_breach_persists_breach_data(self):
        response = self.client.post("/api/v1/scans", json={"email": "demo@breachalert.app"})
        body = response.get_json()

        self.assertTrue(body["breach"]["breach_found"])

        with app.app_context():
            scan = Scan.query.filter_by(id=body["id"]).first()
            self.assertTrue(scan.breach_found)
            self.assertGreater(scan.breach_count, 0)
            self.assertIsNotNone(scan.breach_data)

    def test_create_scan_with_password_persists_analysis(self):
        response = self.client.post(
            "/api/v1/scans",
            json={"email": "test@example.com", "password": "Str0ng!Password123"}
        )
        body = response.get_json()

        self.assertIsNotNone(body["password_analysis"])

        with app.app_context():
            scan = Scan.query.filter_by(id=body["id"]).first()
            self.assertIsNotNone(scan.password_strength_score)
            self.assertIsNotNone(scan.password_strength_label)
            self.assertIsNotNone(scan.password_flags)

    # -----------------------------------------------------------
    # GET /api/v1/scans/<id>
    # -----------------------------------------------------------
    def test_get_scan_from_database(self):
        create_response = self.client.post("/api/v1/scans", json={"email": "test@example.com"})
        scan_id = create_response.get_json()["id"]

        get_response = self.client.get(f"/api/v1/scans/{scan_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.get_json()["id"], scan_id)

    def test_get_nonexistent_scan_returns_404(self):
        response = self.client.get("/api/v1/scans/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # -----------------------------------------------------------
    # GET /api/v1/users/<email>/scans
    # -----------------------------------------------------------
    def test_get_user_scans_returns_all_scans(self):
        email = "multiuser@example.com"

        # Create 3 scans for the same user
        for i in range(3):
            self.client.post("/api/v1/scans", json={"email": email})

        response = self.client.get(f"/api/v1/users/{email}/scans")
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["scans_count"], 3)
        self.assertEqual(len(body["scans"]), 3)

    def test_get_user_scans_nonexistent_user_returns_empty(self):
        response = self.client.get("/api/v1/users/nonexistent@example.com/scans")
        body = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(body["scans_count"], 0)
        self.assertEqual(len(body["scans"]), 0)

    # -----------------------------------------------------------
    # GET /api/v1/stats (now from database)
    # -----------------------------------------------------------
    def test_stats_reflect_database_state(self):
        # Create scans
        self.client.post("/api/v1/scans", json={"email": "user1@example.com"})
        self.client.post("/api/v1/scans", json={"email": "user2@example.com"})
        self.client.post("/api/v1/scans", json={"email": "demo@breachalert.app"})

        response = self.client.get("/api/v1/stats")
        body = response.get_json()

        self.assertEqual(body["total_scans"], 3)
        self.assertEqual(body["unique_users"], 3)
        self.assertEqual(body["breaches_found"], 1)  # only demo@breachalert.app has a breach
        self.assertIsNotNone(body["average_score"])

    def test_stats_empty_database(self):
        response = self.client.get("/api/v1/stats")
        body = response.get_json()

        self.assertEqual(body["total_scans"], 0)
        self.assertEqual(body["unique_users"], 0)
        self.assertEqual(body["breaches_found"], 0)
        self.assertIsNone(body["average_score"])

    # -----------------------------------------------------------
    # POST /api/v1/passwords/analyze (stateless, no persistence)
    # -----------------------------------------------------------
    def test_analyze_password_does_not_persist(self):
        self.client.post("/api/v1/passwords/analyze", json={"password": "test123"})

        with app.app_context():
            scan_count = Scan.query.count()
            self.assertEqual(scan_count, 0)  # No scan was created

    # -----------------------------------------------------------
    # Error handling and validation
    # -----------------------------------------------------------
    def test_invalid_email_returns_400(self):
        response = self.client.post("/api/v1/scans", json={"email": "not-an-email"})
        self.assertEqual(response.status_code, 400)

    def test_missing_email_returns_400(self):
        response = self.client.post("/api/v1/scans", json={})
        self.assertEqual(response.status_code, 400)

    def test_unknown_endpoint_returns_404(self):
        response = self.client.get("/api/v1/nonexistent")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
