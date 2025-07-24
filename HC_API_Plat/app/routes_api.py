# app/routes_api.py
from flask import Blueprint, request, jsonify, abort, Response
from flask_jwt_extended import create_access_token, jwt_required
import time
from .crud import (
    create_user,list_users, verify_user,
    create_rule, list_rules, update_rule, delete_rule,
    find_matching_rule, log_request, list_logs, clear_logs
)
from .template_engine import render_handlebars

api_bp = Blueprint("api", __name__, url_prefix="/api")

# ─── Auth (JWT) ───────────────────────────────────────────────────────────────
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
    username = data.get("username")
    password = data.get("password")
    user = verify_user(username, password)
    if not user:
        abort(401, "Invalid credentials")
    token = create_access_token(identity=user.id)
    return jsonify(access_token=token), 200

# ─── User management (protected) ─────────────────────────────────────────────
@api_bp.route("/users", methods=["GET"])
@jwt_required()
def api_users_list():
    users = list_users()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "created_at": u.created_at.isoformat()
    } for u in users])

# ─── Rules CRUD ───────────────────────────────────────────────────────────────
@api_bp.route("/rules", methods=["GET", "POST"])
def api_rules():
    if request.method == "POST":
        data = request.get_json(force=True)
        rule = create_rule(data)
        return jsonify({ "id":rule.id, **data, "created_at":rule.created_at.isoformat() }), 201
    return jsonify([{
        "id":r.id,
        "method":r.method,
        "path_regex":r.path_regex,
        "status_code":r.status_code,
        "headers":r.headers,
        "body_template":r.body_template,
        "delay":r.delay,
        "created_at":r.created_at.isoformat()
    } for r in list_rules()])

@api_bp.route("/rules/<int:rule_id>", methods=["PUT"])
def api_update_rule(rule_id):
    data = request.get_json(force=True)
    rule = update_rule(rule_id, data)
    if not rule:
        abort(404, "Rule not found")
    return jsonify({
        "id": rule.id,
        "method": rule.method,
        "path_regex": rule.path_regex,
        "status_code": rule.status_code,
        "headers": rule.headers,
        "body_template": rule.body_template,
        "delay": rule.delay,
        "created_at": rule.created_at.isoformat()
    })

@api_bp.route("/rules/<int:rule_id>", methods=["DELETE"])
def api_delete_rule(rule_id):
    if not delete_rule(rule_id):
        abort(404, "Rule not found")
    return ("", 204)

# ─── Logs CRUD ────────────────────────────────────────────────────────────────
@api_bp.route("/logs", methods=["GET"])
def api_logs():
    logs = list_logs(limit=200)
    return jsonify([{
        "id": l.id,
        "timestamp": l.timestamp.isoformat(),
        "method": l.method,
        "path": l.path,
        "headers": l.headers,
        "query": l.query_params,
        "body": l.body,
        "matched_rule_id": l.matched_rule_id
    } for l in logs])

@api_bp.route("/logs", methods=["DELETE"])
def api_clear_logs():
    deleted = clear_logs()
    return jsonify({"deleted": deleted}), 200

# ─── Catch-all mock endpoint ─────────────────────────────────────────────────
@api_bp.route("/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH"])
def mock_all(path):
    full_path = "/" + path
    method    = request.method
    body      = request.get_data(as_text=True)
    headers   = dict(request.headers)
    query     = request.args.to_dict()

    rule       = find_matching_rule(method, full_path)
    matched_id = rule.id if rule else None

    # logs
    log_request({
        "method": method,
        "path": full_path,
        "headers": headers,
        "query": query,
        "body": body,
        "matched_rule_id": matched_id
    })

    if not rule:
        abort(404, "No mock rule matched")

    if rule.delay:
        time.sleep(rule.delay)

    tpl_str = rule.body_template.get("template")
    if not tpl_str:
        abort(500, "Template field missing in stored JSONB data")

    ctx = {"request": {
        "method": method,
        "path":   full_path,
        "headers": headers,
        "query":  query,
        "body":   body
    }}
    try:
        content = render_handlebars(tpl_str, ctx)
    except Exception as e:
        abort(500, f"Template error: {e}")

    return Response(content, status=rule.status_code, headers=rule.headers)