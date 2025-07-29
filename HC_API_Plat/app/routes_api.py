import time
from flask import Blueprint, request, jsonify, abort, Response
from flask_jwt_extended import create_access_token, jwt_required
from .crud import (
    create_user, verify_user, list_users,
    create_project, list_projects, get_project,
    update_project, delete_project,
    create_rule, list_rules, update_rule, delete_rule,
    find_matching_rule, toggle_rule,
    log_request, list_logs, clear_logs
)
from .models import MockRule, LoggedRequest
from .db import db
from .template_engine import render_handlebars

api_bp = Blueprint("api", __name__,url_prefix="/api")

# Auth ( JWT )
@api_bp.route("/auth/register", methods=["POST"])
def api_auth_register():
    data = request.get_json(force=True)
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        abort(400, "username and password required")
    if any(u.username == username for u in list_users()):
        abort(400, "username already exists")
    user = create_user(username, password)
    token = create_access_token(identity=user.id)
    return jsonify(access_token=token), 201

@api_bp.route("/auth/login", methods=["POST"])
def api_auth_login():
    data = request.get_json(force=True)
    user = verify_user(data.get("username"), data.get("password"))
    if not user:
        abort(401, "Invalid credentials")
    token = create_access_token(identity=user.id)
    return jsonify(access_token=token), 200

# Users
@api_bp.route("/users", methods=["GET"])
@jwt_required()
def api_users_list():
    return jsonify([
        {"id":u.id, "username":u.username, "created_at":u.created_at.isoformat()}
        for u in list_users()
    ])

# Projects
@api_bp.route("/projects", methods=["GET", "POST"])
def api_projects():
    if request.method == "POST":
        data = request.get_json(force=True)
        data["name"] = data["name"].strip().lower()
        proj = create_project(data)
        return jsonify({
            "id": proj.id,
            **data,
            "created_at": proj.created_at.isoformat()
        }), 201

    return jsonify([{
        "id": p.id,
        "name": p.name.lower(),
        "description": p.description,
        "created_at": p.created_at.isoformat()
    } for p in list_projects()])

@api_bp.route("/projects/<int:pid>", methods=["PUT", "DELETE"])
def update_delete_project_api(pid):
    project = get_project(pid)
    if not project:
        return "Not Found", 404

    if request.method == "DELETE":
        delete_project(pid)
        return "", 204

    data = request.get_json(force=True)
    update_project(pid, data)
    return jsonify({
        "id": project.id,
        **data,
        "created_at": project.created_at.isoformat()
    })

# Rules
@api_bp.route("/projects/<int:pid>/rules", methods=["GET","POST"])
def api_rules(pid):
    proj = get_project(pid) or abort(404, "Project not found")
    if request.method == "POST":
        data = request.get_json(force=True)
        data["project_id"] = pid
        rule = create_rule(data)
        return jsonify({
            "id":         rule.id,
            **data,
            "created_at": rule.created_at.isoformat()
        }), 201
    rules = MockRule.query.filter_by(project_id=pid).all()
    return jsonify([{
        "id":            r.id,
        "project_id":    r.project_id,
        "method":        r.method,
        "path_regex":    r.path_regex,
        "status_code":   r.status_code,
        "headers":       r.headers,
        "body_template": r.body_template,
        "enabled":       r.enabled,
        "delay":         r.delay,
        "created_at":    r.created_at.isoformat()
    } for r in rules])

@api_bp.route("/projects/<int:pid>/rules/<int:rule_id>", methods=["PUT"])
def api_update_rule(pid, rule_id):
    get_project(pid) or abort(404, "Project not found")
    data = request.get_json(force=True)
    rule = update_rule(rule_id, data)
    if not rule:
        abort(404, "Rule not found")
    return jsonify({
        "id":         rule.id,
        **data,
        "created_at": rule.created_at.isoformat()
    })

@api_bp.route("/projects/<int:pid>/rules/<int:rule_id>", methods=["DELETE"])
def api_delete_rule(pid, rule_id):
    get_project(pid) or abort(404, "Project not found")
    if not delete_rule(rule_id):
        abort(404, "Rule not found")
    return ("", 204)

@api_bp.route("/projects/<int:pid>/rules/<int:rule_id>/toggle", methods=["POST"])
def api_toggle_rule(pid, rule_id):
    get_project(pid) or abort(404, "Project not found")
    rule = toggle_rule(rule_id)
    if not rule:
        abort(404, "Rule not found")
    return jsonify({"id": rule.id, "enabled": rule.enabled})

# Logs
@api_bp.route("/logs", methods=["GET"])
def api_logs():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    total = db.session.query(db.func.count(LoggedRequest.id)).scalar()
    logs = LoggedRequest.query.order_by(LoggedRequest.id.desc()).offset(offset).limit(limit).all()

    return jsonify({
        "logs": [{
            "id": l.id,
            "timestamp": l.timestamp.isoformat(),
            "method": l.method,
            "path": l.path,
            "headers": l.headers,
            "query": l.query_params,
            "body": l.body,
            "raw_body": l.raw_body,
            "response": {
                "status": l.response_status,
                "body": l.response_body
            },
            "matched_rule_id": l.matched_rule_id,
            "status_code": l.status_code
        } for l in logs],
        "total": total
    })

@api_bp.route("/logs", methods=["DELETE"])
def api_clear_logs():
    deleted = clear_logs()
    return jsonify({"deleted": deleted}), 200
