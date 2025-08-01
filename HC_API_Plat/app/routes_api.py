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

api_bp = Blueprint("api", __name__, url_prefix="/api")

# — Auth (JWT) —
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

# — Users —
@api_bp.route("/users", methods=["GET"])
@jwt_required()
def api_users_list():
    return jsonify([
        {"id": u.id, "username": u.username, "created_at": u.created_at.isoformat()}
        for u in list_users()
    ])

# — Projects —
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

# — Rules —
@api_bp.route("/projects/<int:pid>/rules", methods=["GET", "POST"])
def api_rules(pid):
    # ensure project exists
    get_project(pid) or abort(404, "Project not found")

    if request.method == "POST":
        raw = request.get_json(force=True)

        if "path_regex" in raw:
            raw["path_regex"] = raw["path_regex"].replace("\\\\", "\\")
        # extract and remove response_type so we don't set it on the model
        resp_type = raw.pop("response_type", "single")

        # always record the project_id
        raw["project_id"] = pid

        # --- normalize single vs weighted into raw["body_template"] ---
        if resp_type == "weighted":
            bt = raw.get("body_template")
            # if the incoming body_template is a JSON string, parse it
            if isinstance(bt, str):
                try:
                    entries = json.loads(bt)
                except ValueError:
                    abort(400, "Invalid JSON for weighted responses")
            elif isinstance(bt, list):
                entries = bt
            else:
                abort(400, "body_template must be a JSON array for weighted responses")

            # validate entries
            total = 0
            for e in entries:
                if not isinstance(e, dict):
                    abort(400, "Each weighted entry must be an object")
                w = e.get("weight")
                if w is None:
                    abort(400, "Each weighted entry requires a weight")
                try:
                    total += int(w)
                except (TypeError, ValueError):
                    abort(400, "Weight must be an integer")
            if total != 100:
                abort(400, f"Total weight must equal 100% (got {total}%)")

            # store the array
            raw["body_template"] = entries

            # clear single‐response fields
            raw["delay"]       = 0
            raw["status_code"] = 200
            raw["headers"]     = {}
        else:
            # single response mode
            # expect raw["delay"], raw["status_code"], raw["headers"], raw["body_template"]["template"]
            raw["body_template"] = {
                "delay":       raw.get("delay", 0),
                "status_code": raw.get("status_code", 200),
                "headers":     raw.get("headers", {}),
                "template":    raw.get("body_template", {}).get("template", "")
            }

        # check unique
        existing = MockRule.query.filter_by(
            project_id=pid,
            method=raw.get("method"),
            path_regex=raw.get("path_regex")
        ).first()
        if existing:
            abort(400, "A rule for that method + path already exists")

        # create and return
        rule = create_rule(raw)
        return jsonify({
            "id":            rule.id,
            "project_id":    rule.project_id,
            "method":        rule.method,
            "path_regex":    rule.path_regex,
            "response_type": resp_type,
            "body_template": rule.body_template,
            "enabled":       rule.enabled,
            "created_at":    rule.created_at.isoformat()
        }), 201

    # GET list
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

    raw = request.get_json(force=True)
    resp_type = raw.pop("response_type", "single")

    # normalize exactly as in POST
    if resp_type == "weighted":
        bt = raw.get("body_template")
        if isinstance(bt, str):
            try:
                entries = json.loads(bt)
            except ValueError:
                abort(400, "Invalid JSON for weighted responses")
        elif isinstance(bt, list):
            entries = bt
        else:
            abort(400, "body_template must be a JSON array for weighted responses")

        total = 0
        for e in entries:
            if not isinstance(e, dict):
                abort(400, "Each weighted entry must be an object")
            w = e.get("weight")
            if w is None:
                abort(400, "Each weighted entry requires a weight")
            try:
                total += int(w)
            except (TypeError, ValueError):
                abort(400, "Weight must be an integer")
        if total != 100:
            abort(400, f"Total weight must equal 100% (got {total}%)")

        raw["body_template"] = entries
        raw["delay"]       = 0
        raw["status_code"] = 200
        raw["headers"]     = {}
    else:
        raw["body_template"] = {
            "delay":       raw.get("delay", 0),
            "status_code": raw.get("status_code", 200),
            "headers":     raw.get("headers", {}),
            "template":    raw.get("body_template", {}).get("template", "")
        }

    rule = update_rule(rule_id, raw)
    if not rule:
        abort(404, "Rule not found")

    return jsonify({
        "id":            rule.id,
        "project_id":    rule.project_id,
        "method":        rule.method,
        "path_regex":    rule.path_regex,
        "response_type": resp_type,
        "body_template": rule.body_template,
        "enabled":       rule.enabled,
        "created_at":    rule.created_at.isoformat()
    })

@api_bp.route("/projects/<int:pid>/rules/<int:rule_id>", methods=["DELETE"])
def api_delete_rule(pid, rule_id):
    get_project(pid) or abort(404, "Project not found")
    if not delete_rule(rule_id):
        abort(404, "Rule not found")
    return "", 204

@api_bp.route("/projects/<int:pid>/rules/<int:rule_id>/toggle", methods=["POST"])
def api_toggle_rule(pid, rule_id):
    get_project(pid) or abort(404, "Project not found")
    rule = toggle_rule(rule_id)
    if not rule:
        abort(404, "Rule not found")
    return jsonify({
        "id":      rule.id,
        "enabled": rule.enabled
    })

# — Logs —
@api_bp.route("/logs", methods=["GET"])
def api_logs():
    page  = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    total = db.session.query(db.func.count(LoggedRequest.id)).scalar()
    logs  = LoggedRequest.query.order_by(LoggedRequest.id.desc())\
                .offset(offset).limit(limit).all()

    return jsonify({
        "logs": [{
            "id":             l.id,
            "timestamp":      l.timestamp.isoformat(),
            "method":         l.method,
            "path":           l.path,
            "headers":        l.headers,
            "query":          l.query_params,
            "body":           l.body,
            "raw_body":       l.raw_body,
            "matched_rule_id":l.matched_rule_id,
            "response": {
                "status": l.response_status,
                "body":   l.response_body
            },
            "status_code":    l.status_code
        } for l in logs],
        "total": total
    })

@api_bp.route("/logs", methods=["DELETE"])
def api_clear_logs():
    deleted = clear_logs()
    return jsonify({"deleted": deleted}), 200