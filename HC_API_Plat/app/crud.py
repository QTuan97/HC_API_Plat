import re
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional
from .db import db
from .models import User, MockRule, LoggedRequest

# User CRUD
def create_user(username: str, password: str) -> User:
    pw_hash = generate_password_hash(password)
    user = User(username=username, password_hash=pw_hash)
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_username(username: str):
    return User.query.filter_by(username=username).first()

def list_users() -> list[User]:
    return User.query.order_by(User.id.desc()).all()

def verify_user(username: str, password: str):
    user = get_user_by_username(username)
    return user if user and check_password_hash(user.password_hash, password) else None

# MockRule CRUD
def create_rule(data: dict) -> MockRule:
    rule = MockRule(**data)
    db.session.add(rule)
    db.session.commit()
    return rule

def list_rules() -> list[MockRule]:
    return MockRule.query.order_by(MockRule.id.desc()).all()

def find_matching_rule(method: str, path: str) -> Optional[MockRule]:
    for rule in MockRule.query.filter_by(method=method).all():
        if re.match(rule.path_regex, path):
            return rule
    return None

def update_rule(rule_id: int, data: dict) -> Optional[MockRule]:
    rule = MockRule.query.get(rule_id)
    if not rule:
        return None
    # update fields
    rule.method = data.get("method", rule.method)
    rule.path_regex = data.get("path_regex", rule.path_regex)
    rule.status_code = data.get("status_code", rule.status_code)
    rule.headers = data.get("headers", rule.headers)
    rule.body_template = data.get("body_template", rule.body_template)
    rule.delay = data.get("delay", rule.delay)
    db.session.commit()
    return rule

def delete_rule(rule_id: int) -> bool:
    rule = MockRule.query.get(rule_id)
    if not rule:
        return False
    db.session.delete(rule)
    db.session.commit()
    return True

# Logs CRUD
def log_request(record: dict) -> LoggedRequest:
    log = LoggedRequest(
        method = record["method"],
        path = record["path"],
        headers = record["headers"],
        query_params = record["query"],
        body = record["body"],
        matched_rule_id = record["matched_rule_id"])

    db.session.add(log)
    db.session.commit()
    return log

def list_logs(limit: int = 100) -> list[LoggedRequest]:
    return LoggedRequest.query.order_by(LoggedRequest.id.desc()).limit(limit).all()

def clear_logs() -> int:
    count = LoggedRequest.query.delete()
    db.session.commit()
    return count