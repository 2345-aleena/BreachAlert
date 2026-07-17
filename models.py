"""
models.py
=================================================
Database models for BreachAlert using SQLAlchemy.
Represents the persistent layer: Scans and Users.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    A user who has run scans. Minimal record — we don't store passwords,
    but we do track email and scan history.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationship: one user has many scans
    scans = db.relationship('Scan', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'scans_count': len(self.scans),
            'created_at': self.created_at.isoformat(),
        }


class Scan(db.Model):
    """
    A single security scan result. Stores breach info, password analysis,
    and the computed security score. The raw password is never stored —
    only the analysis result.
    """
    __tablename__ = 'scans'

    id = db.Column(db.String(36), primary_key=True)  # UUID string
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    email_checked = db.Column(db.String(254), nullable=False, index=True)
    security_score = db.Column(db.Integer, nullable=False)

    # Breach data (JSON blob)
    breach_found = db.Column(db.Boolean, nullable=False)
    breach_count = db.Column(db.Integer, default=0)
    breach_data = db.Column(db.JSON, default=None)  # Full breach details array

    # Password analysis (JSON blob) — only if password was provided
    password_strength_score = db.Column(db.Integer, default=None)
    password_strength_label = db.Column(db.String(20), default=None)
    password_entropy_bits = db.Column(db.Float, default=None)
    password_flags = db.Column(db.JSON, default=None)  # Array of flag strings

    # Metadata
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        """Serialize a scan for JSON response."""
        result = {
            'id': self.id,
            'email_checked': self.email_checked,
            'score': self.security_score,
            'breach': {
                'email_checked': self.email_checked,
                'breach_found': self.breach_found,
                'breach_count': self.breach_count,
                'breaches': self.breach_data or [],
            },
            'password_analysis': None,
            'created_at': self.created_at.isoformat(),
        }

        if self.password_strength_score is not None:
            result['password_analysis'] = {
                'score': self.password_strength_score,
                'strength_label': self.password_strength_label,
                'entropy_bits': self.password_entropy_bits,
                'flags': self.password_flags or [],
            }

        return result
