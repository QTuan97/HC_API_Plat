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
from .models import MockRule
from .template_engine import render_handlebars

api_bp = Blueprint("api", __name__, url_prefix="/api")

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
        proj = create_project(data)
        return jsonify({
            "id": proj.id,
            **data,
            "created_at": proj.created_at.isoformat()
        }), 201
    return jsonify([{
        "id":          p.id,
        "name":        p.name,
        "base_url":    p.base_url,
        "description": p.description,
        "created_at":  p.created_at.isoformat()
    } for p in list_projects()])

@api_bp.route("/projects/<int:project_id>", methods=["PUT"])
def api_update_project(project_id):
    data = request.get_json(force=True)
    proj = update_project(project_id, data)
    if not proj:
        abort(404, "Project not found")
    return jsonify({
        "id":          proj.id,
        "name":        proj.name,
        "base_url":    proj.base_url,
        "description": proj.description,
        "created_at":  proj.created_at.isoformat()
    })

@api_bp.route("/projects/<int:project_id>", methods=["DELETE"])
def api_delete_project(project_id):
    if not delete_project(project_id):
        abort(404, "Project not found")
    return ("", 204)

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
    return jsonify([{
        "id":              l.id,
        "timestamp":       l.timestamp.isoformat(),
        "method":          l.method,
        "path":            l.path,
        "headers":         l.headers,
        "query":           l.query_params,
        "body":            l.body,
        "matched_rule_id": l.matched_rule_id,
        "status_code":     l.status_code
    } for l in list_logs(limit=200)])

@api_bp.route("/logs", methods=["DELETE"])
def api_clear_logs():
    deleted = clear_logs()
    return jsonify({"deleted": deleted}), 200

# Catch-all Mock Endpoint
@api_bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def mock_all(path):
    full_path = "/" + path
    method = request.method
    headers = dict(request.headers)
    query = request.args.to_dict()
    try:
        body_json = request.get_json(force=True)
    except:
        body_json = {}
    raw_body = request.get_data(as_text=True)

    # 1. Find matching rule
    rule = find_matching_rule(method, full_path)
    if not rule:
        abort(404, "No mock rule matched")

    # 2. Apply delay if needed
    if rule.delay:
        time.sleep(rule.delay)

    # 3. Build dynamic context for template engine
    context = {
        "body": body_json,
        "query": query,
        "headers": headers,
        "path": full_path,
        "method": method,
        "raw_body": raw_body
    }

    # DB lookup support ( if needed )
    if "{{db." in (rule.body_template.get("template") or ""):
        from .models import User  # adjust if you have other models
        # Simple example: try to fetch first user by username from body or query
        username = body_json.get("username") or query.get("username")
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                context["db"] = {c.name: getattr(user, c.name) for c in user.__table__.columns}

    # 4. Render template with extended context
    tpl_str = rule.body_template.get("template")
    try:
        content = render_handlebars(tpl_str, context)
    except Exception as e:
        abort(500, f"Template error: {e}")

    # 5. Return response
    resp = Response(content, status=rule.status_code, headers=rule.headers)

    # 6. Log request
    log_request({
        "method": method,
        "path": full_path,
        "headers": headers,
        "query": query,
        "body": raw_body,
        "matched_rule_id": rule.id,
        "status_code": rule.status_code
    })

    return resp