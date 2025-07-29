from email.policy import default

from .db import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import validates
from .utils import normalize_project_name

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.now())

class Project(db.Model):
    __tablename__  = "projects"
    id             = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    description    = db.Column(db.Text)
    created_at     = db.Column(db.DateTime,  default=datetime.utcnow)
    rules          = db.relationship("MockRule", back_populates="project")

    @validates('name')
    def _normalize_name(self, key, value):
        return normalize_project_name(value)

class MockRule(db.Model):
    __tablename__   = "rules"
    id              = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
                           db.Integer,
                              db.ForeignKey("projects.id", ondelete="CASCADE"),
                              nullable = False)
    project = db.relationship("Project", back_populates="rules")
    method          = db.Column(db.String, nullable=False)
    path_regex      = db.Column(db.String, nullable=False)
    status_code     = db.Column(db.Integer, default=200)
    headers         = db.Column(JSONB, default={})
    body_template   = db.Column(JSONB, default={})
    delay = db.Column(db.Integer, default=0)
    enabled = db.Column(db.Boolean, default=True)
    created_at      = db.Column(db.DateTime, default=datetime.now())

class LoggedRequest(db.Model):
    __tablename__      = "logs"
    id                 = db.Column(db.Integer, primary_key=True)
    timestamp          = db.Column(db.DateTime, default=datetime.now())
    method             = db.Column(db.String, nullable=False)
    path               = db.Column(db.String, nullable=False)
    headers            = db.Column(JSONB)
    query_params       = db.Column(JSONB)
    body               = db.Column(JSONB, nullable=True)
    raw_body           = db.Column(db.Text, nullable=True)
    matched_rule_id    = db.Column(
                           db.Integer,
                           db.ForeignKey("rules.id", ondelete="SET NULL"),
                           nullable=True)
    status_code = db.Column(db.Integer, nullable=False)
    response_status = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)