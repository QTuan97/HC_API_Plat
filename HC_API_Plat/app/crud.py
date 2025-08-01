import re, json
from typing import Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from .db import db
from .models import User, Project, MockRule, LoggedRequest
from .utils import normalize_project_name

# User CRUD
def create_user(username: str, password: str) -> User:
    pw_hash = generate_password_hash(password)
    user = User(username=username, password_hash=pw_hash)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_username(username: str) -> Optional[User]:
    return User.query.filter_by(username=username).first()

def list_users() -> List[User]:
    return User.query.order_by(User.id.desc()).all()

def verify_user(username: str, password: str) -> Optional[User]:
    user = get_user_by_username(username)
    return user if user and check_password_hash(user.password_hash, password) else None

# Project CRUD
def create_project(data: dict) -> Project:
    raw_name = data.get("name", "")
    normalized_name = normalize_project_name(raw_name)
    payload = {**data, "name": normalized_name}
    proj = Project(**payload)
    db.session.add(proj)
    db.session.commit()
    return proj

def list_projects() -> List[Project]:
    return Project.query.order_by(Project.id.desc()).all()

def get_project(project_id: int) -> Optional[Project]:
    return Project.query.get(project_id)

def update_project(project_id: int, data: dict) -> Optional[Project]:
    proj = Project.query.get(project_id)
    if not proj:
        return None
    proj.name        = data.get("name", proj.name)
    proj.description = data.get("description", proj.description)
    db.session.commit()
    return proj

def delete_project(project_id: int) -> bool:
    proj = Project.query.get(project_id)
    if not proj:
        return False
    db.session.delete(proj)
    db.session.commit()
    return True

# MockRule CRUD
def create_rule(data: dict) -> MockRule:
    rule = MockRule(**data)
    db.session.add(rule)
    db.session.commit()
    return rule

def list_rules() -> List[MockRule]:
    return MockRule.query.order_by(MockRule.id.desc()).all()

def find_matching_rule(method: str, path: str, project_id: int):
    rules = MockRule.query.filter_by(
        project_id=project_id, enabled=True
    ).order_by(MockRule.created_at.asc()).all()

    for rule in rules:
        if rule.method.upper() != method.upper():
            continue

        try:
            pattern = re.compile(rule.path_regex)
        except re.error:
            current_app.logger.warning(
                "Invalid regex in rule %s: %r",
                rule.id, rule.path_regex
            )
            continue

        if pattern.fullmatch(path):
            return rule

    return None

def update_rule(rule_id: int, data: dict) -> Optional[MockRule]:
    rule = MockRule.query.get(rule_id)
    if not rule:
        return None
    rule.method        = data.get("method", rule.method)
    rule.path_regex    = data.get("path_regex", rule.path_regex)
    rule.status_code   = data.get("status_code", rule.status_code)
    rule.headers       = data.get("headers", rule.headers)
    rule.body_template = data.get("body_template", rule.body_template)
    rule.delay         = data.get("delay", rule.delay)
    rule.enabled       = data.get("enabled", rule.enabled)
    db.session.commit()
    return rule

def delete_rule(rule_id: int) -> bool:
    rule = MockRule.query.get(rule_id)
    if not rule:
        return False
    db.session.delete(rule)
    db.session.commit()
    return True

def toggle_rule(rule_id: int) -> Optional[MockRule]:
    rule = MockRule.query.get(rule_id)
    if not rule:
        return None
    rule.enabled = not rule.enabled
    db.session.commit()
    return rule

# Logs CRUD
def parse_body(raw_body: str, headers: dict):
    ctype = headers.get("Content-Type", "")
    if "application/json" in ctype:
        try:
            return json.loads(raw_body)
        except:
            return raw_body
    elif "application/x-www-form-urlencoded" in ctype:
        from urllib.parse import parse_qs
        return parse_qs(raw_body)
    return raw_body

def log_request(record: dict) -> LoggedRequest:
    headers = record.get("headers", {})
    raw_body = record.get("body", "")

    log = LoggedRequest(
        method=record.get("method"),
        path=record.get("path"),
        headers=headers,
        query_params=record.get("query"),
        body=parse_body(raw_body, headers),
        raw_body=raw_body,
        response_status=record.get("status_code"),
        response_body=record.get("response_body"),
        matched_rule_id=record.get("matched_rule_id"),
        status_code=record.get("status_code")
    )
    db.session.add(log)
    db.session.commit()

    # Set the limit 1000 logs in database
    excess = LoggedRequest.query.order_by(LoggedRequest.id.desc()).offset(1000).all()
    if excess:
        for old in excess:
            db.session.delete(old)
        db.session.commit()

    return log

def list_logs(limit: int = 100) -> List[LoggedRequest]:
    return LoggedRequest.query.order_by(LoggedRequest.id.desc()).limit(limit).all()

def clear_logs() -> int:
    count = LoggedRequest.query.delete()
    db.session.commit()
    return count