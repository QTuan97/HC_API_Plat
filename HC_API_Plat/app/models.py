from .db import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

class User(db.Model):
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.now())

class MockRule(db.Model):
    __tablename__   = "rules"
    id              = db.Column(db.Integer, primary_key=True)
    method          = db.Column(db.String, nullable=False)
    path_regex      = db.Column(db.String, nullable=False)
    status_code     = db.Column(db.Integer, default=200)
    headers         = db.Column(JSONB, default={})
    body_template   = db.Column(JSONB, nullable=False)
    delay = db.Column(db.Integer, default=0)
    created_at      = db.Column(db.DateTime, default=datetime.now())

class LoggedRequest(db.Model):
    __tablename__      = "logs"
    id                 = db.Column(db.Integer, primary_key=True)
    timestamp          = db.Column(db.DateTime, default=datetime.now())
    method             = db.Column(db.String, nullable=False)
    path               = db.Column(db.String, nullable=False)
    headers            = db.Column(JSONB)
    query_params       = db.Column(JSONB)
    body               = db.Column(db.Text)
    matched_rule_id    = db.Column(
                           db.Integer,
                           db.ForeignKey("rules.id", ondelete="SET NULL"),
                           nullable=True
                         )