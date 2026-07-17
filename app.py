"""
app.py
=================================================
BreachAlert API — Project 3: Database Integration

Full-stack application with SQLite persistence. Routes are identical
to Project 2, but storage is now real and durable — every scan is
saved to the database.

Run:
    python app.py
Then the API is live at:
    http://localhost:5000
"""

import os
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS

from models import db, User, Scan
from validators import (
    require_json_fields,
    validate_email,
    validate_password_field,
    validate_password_required,
)
from security_utils import analyze_password, calculate_security_score, check_breach

# ---------------------------------------------------------------
# Flask app initialization
# ---------------------------------------------------------------
app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "breachalert.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---------------------------------------------------------------
# Rate limiter (same as Project 2)
# ---------------------------------------------------------------
RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60
_request_log = defaultdict(deque)


def is_rate_limited(client_ip):
    now = time.time()
    log = _request_log[client_ip]

    while log and now - log[0] > RATE_LIMIT_WINDOW_SECONDS:
        log.popleft()

    if len(log) >= RATE_LIMIT_MAX_REQUESTS:
        return True

    log.append(now)
    return False


def error_response(status_code, error_code, message):
    """Consistent error shape across every endpoint."""
    response = jsonify({
        "error": {
            "code": error_code,
            "message": message,
        }
    })
    response.status_code = status_code
    return response


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------
def init_db():
    """Create all tables if they don't exist."""
    with app.app_context():
        db.create_all()
        print("✓ Database initialized")


# ---------------------------------------------------------------
# Rate limit gate
# ---------------------------------------------------------------
@app.before_request
def enforce_rate_limit():
    if request.method != "POST":
        return None

    client_ip = request.remote_addr or "unknown"
    if is_rate_limited(client_ip):
        response = error_response(
            429,
            "rate_limited",
            f"Too many requests. Limit is {RATE_LIMIT_MAX_REQUESTS} per {RATE_LIMIT_WINDOW_SECONDS} seconds.",
        )
        response.headers["Retry-After"] = str(RATE_LIMIT_WINDOW_SECONDS)
        return response

    return None


# =================================================================
# GET /api/v1/health
# =================================================================
@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok",
        "service": "BreachAlert API",
        "version": "2.0.0",
        "database": "SQLite",
        "time": utc_now_iso(),
    }), 200


# =================================================================
# POST /api/v1/scans
# Creates a new scan and persists it to the database.
# =================================================================
@app.route("/api/v1/scans", methods=["POST"])
def create_scan():
    payload = request.get_json(silent=True)

    is_valid, error = require_json_fields(payload, required_fields=["email"])
    if not is_valid:
        return error_response(400, "invalid_request", error)

    email = payload.get("email")
    password = payload.get("password")

    is_valid, error = validate_email(email)
    if not is_valid:
        return error_response(400, "invalid_email", error)

    is_valid, error = validate_password_field(password)
    if not is_valid:
        return error_response(400, "invalid_password", error)

    # Get or create user
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        user = User(email=email.strip().lower())
        db.session.add(user)
        db.session.flush()  # flush to get the user id without committing

    # Run security checks
    breach_result = check_breach(email)
    password_analysis = analyze_password(password) if password else None
    score = calculate_security_score(breach_result, password_analysis)

    # Create and save scan
    scan_id = str(uuid.uuid4())
    scan = Scan(
        id=scan_id,
        user_id=user.id,
        email_checked=breach_result["email_checked"],
        security_score=score,
        breach_found=breach_result["breach_found"],
        breach_count=breach_result["breach_count"],
        breach_data=breach_result["breaches"],
    )

    if password_analysis:
        scan.password_strength_score = password_analysis["score"]
        scan.password_strength_label = password_analysis["strength_label"]
        scan.password_entropy_bits = password_analysis["entropy_bits"]
        scan.password_flags = password_analysis["flags"]

    db.session.add(scan)
    db.session.commit()

    response = jsonify(scan.to_dict())
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/scans/{scan_id}"
    return response


# =================================================================
# GET /api/v1/scans/<scan_id>
# Retrieves a previously created scan from the database.
# =================================================================
@app.route("/api/v1/scans/<scan_id>", methods=["GET"])
def get_scan(scan_id):
    scan = Scan.query.filter_by(id=scan_id).first()

    if not scan:
        return error_response(404, "scan_not_found", f"No scan found with id '{scan_id}'.")

    return jsonify(scan.to_dict()), 200


# =================================================================
# GET /api/v1/users/<email>/scans
# Returns all scans for a given email address.
# =================================================================
@app.route("/api/v1/users/<email>/scans", methods=["GET"])
def get_user_scans(email):
    user = User.query.filter_by(email=email.strip().lower()).first()

    if not user:
        return jsonify({
            "email": email.strip().lower(),
            "scans_count": 0,
            "scans": [],
        }), 200

    scans = Scan.query.filter_by(user_id=user.id).order_by(Scan.created_at.desc()).all()

    return jsonify({
        "email": user.email,
        "scans_count": len(scans),
        "scans": [scan.to_dict() for scan in scans],
        "user_created_at": user.created_at.isoformat(),
    }), 200


# =================================================================
# POST /api/v1/passwords/analyze
# Stateless password strength check.
# =================================================================
@app.route("/api/v1/passwords/analyze", methods=["POST"])
def analyze_password_endpoint():
    payload = request.get_json(silent=True)

    is_valid, error = require_json_fields(payload, required_fields=["password"])
    if not is_valid:
        return error_response(400, "invalid_request", error)

    password = payload.get("password")

    is_valid, error = validate_password_required(password)
    if not is_valid:
        return error_response(400, "invalid_password", error)

    result = analyze_password(password)
    return jsonify(result), 200


# =================================================================
# GET /api/v1/stats
# Aggregate statistics from the database.
# =================================================================
@app.route("/api/v1/stats", methods=["GET"])
def get_stats():
    try:
        total_scans = Scan.query.count()
        breaches_found = Scan.query.filter_by(breach_found=True).count()
        unique_users = User.query.count()

        # Average score
        avg_score_result = db.session.query(db.func.avg(Scan.security_score)).scalar()
        average_score = round(avg_score_result, 1) if avg_score_result else None

        return jsonify({
            "total_scans": total_scans,
            "breaches_found": breaches_found,
            "unique_users": unique_users,
            "average_score": average_score,
            "timestamp": utc_now_iso(),
        }), 200
    except Exception as e:
        return error_response(500, "stats_error", str(e))


# =================================================================
# Error handlers
# =================================================================
@app.errorhandler(404)
def handle_404(e):
    return error_response(404, "not_found", "This endpoint doesn't exist.")


@app.errorhandler(405)
def handle_405(e):
    return error_response(405, "method_not_allowed", "This HTTP method isn't supported on this endpoint.")


@app.errorhandler(500)
def handle_500(e):
    db.session.rollback()
    return error_response(500, "internal_error", "Something went wrong on our end. Please try again.")


# =================================================================
# CLI commands for database management
# =================================================================
@app.cli.command()
def reset_db():
    """Drop all tables and recreate them."""
    if os.path.exists(os.path.join(basedir, 'breachalert.db')):
        os.remove(os.path.join(basedir, 'breachalert.db'))
    db.create_all()
    print("✓ Database reset")


@app.cli.command()
def seed_demo():
    """Seed the database with demo data."""
    with app.app_context():
        # Create demo users if they don't exist
        for demo_email in ["demo@breachalert.app", "exposed@example.com", "clean@example.com"]:
            user = User.query.filter_by(email=demo_email).first()
            if not user:
                user = User(email=demo_email)
                db.session.add(user)

        db.session.commit()
        print("✓ Demo data seeded")


if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("  BreachAlert API (Project 3: Database Integration)")
    print("  → http://localhost:5000/api/v1/health")
    print("  → SQLite database: breachalert.db")
    print("  → Press Ctrl+C to stop")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=True)
