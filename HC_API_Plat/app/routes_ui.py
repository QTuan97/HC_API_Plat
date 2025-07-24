from functools import wraps
from flask import (
    Blueprint, render_template, request,
    session, redirect, url_for, flash
)
from .crud import create_user, get_user_by_username, verify_user, get_project

ui_bp = Blueprint("ui", __name__)
# UI Routes

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("ui.index"))
        return f(*args, **kwargs)
    return decorated

@ui_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if get_user_by_username(username):
            flash("Username already taken")
            return redirect(url_for("ui.register"))
        user = create_user(username, password)
        session["user_id"]  = user.id
        session["username"] = user.username
        return redirect(url_for("ui.index"))
    return render_template("register.html")

@ui_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = verify_user(username, password)
        if not user:
            flash("Invalid credentials")
            return redirect(url_for("ui.login"))
        session["user_id"]  = user.id
        session["username"] = user.username
        return redirect(url_for("ui.index"))
    return render_template("login.html")

@ui_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("ui.index"))

@ui_bp.route("/")
def index():
    return render_template("index.html")

@ui_bp.route("/projects")
@login_required
def projects_page():
    return render_template("projects.html")

@ui_bp.route("/projects/<int:pid>/rules")
@login_required
def project_rules_page(pid):
    proj = get_project(pid) or abort(404)
    return render_template("rules.html", project=proj)

@ui_bp.route("/logs")
@login_required
def logs_page():
    return render_template("logs.html")