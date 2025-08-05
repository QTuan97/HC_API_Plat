from flask import Blueprint, request, abort, jsonify, Response
import time
from .models import Project
from .crud import find_matching_rule, log_request
from .template_engine import render_handlebars
from .utils import normalize_project_name

mock_bp = Blueprint("mock", __name__)

@mock_bp.route("/<project_name>/", defaults={"mock_path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@mock_bp.route("/<project_name>/<path:mock_path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def dynamic_mock(project_name, mock_path):
    project_name = normalize_project_name(project_name)
    project = Project.query.filter_by(name=project_name).first()
    if not project:
        abort(404, "Project not found")

    full_path = "/" + mock_path
    method    = request.method
    headers   = dict(request.headers)
    query     = request.args.to_dict()
    raw_body  = request.get_data(as_text=True)
    try:
        body_json = request.get_json(force=True)
    except:
        body_json = {}

    rule = find_matching_rule(method, full_path, project.id)
    if not rule:
        abort(404, "No matching rule")

    # Delay if single mode or per-entry
    if not isinstance(rule.body_template, list) and rule.delay:
        time.sleep(rule.delay)

    context = {
        "body":      body_json,
        "query":     query,
        "headers":   headers,
        "path":      full_path,
        "method":    method,
        "raw_body":  raw_body,
    }

    bt = rule.body_template
    if isinstance(bt, list):
        import random
        choice = random.choices(
            bt,
            weights=[e.get("weight", 0) for e in bt],
            k=1
        )[0]
        tpl_str     = choice.get("template", "")
        status_code = choice.get("status_code", rule.status_code)
        headers_out = choice.get("headers", rule.headers)
    else:
        # Single‐response
        tpl_str     = bt.get("template", "")
        status_code = rule.status_code
        headers_out = rule.headers


    try:
        content = render_handlebars(tpl_str, context)
    except Exception as e:
        abort(500, f"Template error: {e}")

    resp = Response(content, status=status_code, headers=headers_out)

    log_request({
        "method":        method,
        "path":          full_path,
        "headers":       headers,
        "query":         query,
        "body":          raw_body,
        "matched_rule_id": rule.id,
        "status_code":   resp.status_code,
        "response_body": content
    })

    return resp