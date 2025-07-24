import re
from typing import Optional, List
from werkzeug.security import generate_password_hash, check_password_hash
from .db import db
from .models import User, Project, MockRule, LoggedRequest

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
    proj = Project(**data)
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
    proj.base_url    = data.get("base_url", proj.base_url)
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

def find_matching_rule(method: str, path: str) -> Optional[MockRule]:
    # only match enabled rules
    for rule in MockRule.query.filter_by(method=method, enabled=True).all():
        if re.match(rule.path_regex, path):
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
def log_request(record: dict) -> LoggedRequest:
    log = LoggedRequest(
        method=record["method"],
        path=record["path"],
        headers=record["headers"],
        query_params=record.get("query", {}),
        body=record.get("body", ""),
        matched_rule_id=record.get("matched_rule_id")
    )
    db.session.add(log)
    db.session.commit()
    return log

def list_logs(limit: int = 100) -> List[LoggedRequest]:
    return LoggedRequest.query.order_by(LoggedRequest.id.desc()).limit(limit).all()

def clear_logs() -> int:
    count = LoggedRequest.query.delete()
    db.session.commit()
    return count