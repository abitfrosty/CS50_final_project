from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, admin_required, db_execute, dict_factory, usd
from tests import generate_examples, calculate_weights
#from datetime import datetime
import re
import sqlite3
from contextlib import closing


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

"""
# Custom filter
app.jinja_env.filters["usd"] = usd
"""

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Global gender list for '/profile':
GENDER_LIST = ["male", "female", "other"]

# Global path to the main database for 'db_execute'
SQLITE_DB = "project.db"

"""
@app.template_filter('quoted')
def quoted(s):
    l = re.findall("'(.*)\.html'", str(s))
    if l:
        return l[0]
    return None
"""

@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure login was submitted
        if not request.form.get("login"):
            return apology("must provide login", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        row = db_execute(SQLITE_DB,
                         "SELECT user_temp.id AS id, user_temp.hash AS hash, user_temp.type AS type,profile.name AS name FROM (SELECT id, hash, type FROM user WHERE login = ?) AS user_temp LEFT JOIN profile ON user_temp.id = profile.user_id;",
                         (request.form.get("login"),))
            
        # Ensure login exists and password is correct
        if row is None or not check_password_hash(row["hash"], request.form.get("password")):
            return apology("invalid login and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row["id"]

        # Remember user's name
        session["user_name"] = row["name"]
        
        session["admin"] = "admin" in row["type"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


# Dynamic notification system
def dynamic_flash(message="", category="primary", closing=True):
    """
    XMLHttpRequest
    Renders template with alert and returns it as json
    Known categories: primary, secondary, danger, warning, info, light, dark
    Requirements: flask[flash, jsonify, render_template], JQuery, Bootstrap
    """
    flash(message, category)
    return jsonify(render_template(("notifications.html"), with_closing=closing))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """User's profile"""
    profile = db_execute(SQLITE_DB, "SELECT * FROM profile WHERE user_id = ?;", (session["user_id"],))
    profile["gender_list"] = GENDER_LIST
    return render_template("profile.html", profile=profile)


@app.route("/profile_update", methods=["POST"])
@login_required
def profile_update():
    if request.form.get("gender") is not None and request.form.get("gender") not in GENDER_LIST:
        return apology("Gender was not recognized!", 403)
        
    data = request.form.to_dict()
    params = []
    query = "UPDATE profile SET "
    for k, v in data.items():
        query += k + " = ?, "
        params.append(v)
    query = query[:-len(", ")]
    query += " WHERE user_id = ?;"
    params.append(session["user_id"])

    db_execute(SQLITE_DB, query, params)
    """ SQL Query sample
    row = db_execute(SQLITE_DB, 
                     "UPDATE profile SET gender = ?, birthdate = ?, education = ?, bio = ? WHERE user_id = ?;",
                     (request.form.get("gender"),request.form.get("birthdate"),request.form.get("education"),request.form.get("bio"),session["user_id"],))
    """
    
    return dynamic_flash(u"Profile update was successful!", "info")


@app.route("/name_update", methods=["POST"])
@login_required
def name_update():
    db_execute(SQLITE_DB, "UPDATE profile SET name = ? WHERE user_id = ?;", (request.form.get("name"), session["user_id"],))
    session["user_name"] = request.form.get("name")
    return dynamic_flash(u"Good to see you, {0}!".format(session["user_name"]),"primary")


@app.route("/password_update", methods=["POST"])
@login_required
def password_update():
    """Change password"""
    if request.form.get("password") == request.form.get("confirmation"):
        row = db_execute(SQLITE_DB, "UPDATE user SET hash = ? WHERE id = ?;", (generate_password_hash(request.form.get("password")), session["user_id"],))
        return dynamic_flash(u"Your password has been changed successfully!", "info")
    else:
        return dynamic_flash(u"Password and confirmation did not match!", "danger")


@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "GET":
        return render_template("register.html")

    apology_t = ""
    apology_c = 400

    if not len(request.form.get("login")):
        apology_t = "login field is empty"
    elif not len(request.form.get("password")):
        apology_t = "Password field is empty"
    elif not request.form.get("password") == request.form.get("confirmation"):
        apology_t = "Wrong password confirmation"

    if len(apology_t):
        return apology(apology_t, apology_c)

    row = db_execute(SQLITE_DB, "SELECT * FROM user WHERE login = ?", (request.form.get("login"),))
    if row is not None:
        apology_t = "login already exists"

    if len(apology_t):
        return apology(apology_t, apology_c)

    user_id = db_execute(SQLITE_DB, "INSERT INTO user (login, hash) VALUES (?, ?);", (request.form.get("login"), generate_password_hash(request.form.get("password")),))
    db_execute(SQLITE_DB, "INSERT INTO profile (user_id) VALUES (?);", (user_id,))
    session["user_id"] = user_id
    flash(u"New user's registration with id \"{0}\" was successful!".format(user_id), "info")
    return redirect("/")


@app.route("/tests", methods=["GET"])
def tests():
    levels = db_execute(SQLITE_DB, "SELECT DISTINCT level FROM example ORDER BY level;", "", False)
    operators = db_execute(SQLITE_DB, "SELECT DISTINCT operator FROM example ORDER BY id;", "", False)
    return render_template("tests.html", levels=levels, operators=operators)


@app.route("/test_start", methods=["GET"])
@login_required
def test_start():
    """
    Dynamic html (jsonify, jinja, jquery, ajax)
    https://stackoverflow.com/questions/40701973/create-dynamically-html-div-jinja2-and-ajax
    """
    
    request_args = request.args.to_dict(flat=False)
    operators = request_args.get("operator") # Need to check if none selected
    levels = request_args.get("level") # Need to check if none selected
    num = int(request_args.get("examples")[0]) if request_args.get("examples") else 20
    query = ""
    args = []
    weights = calculate_weights(num, levels)
    for idx, level in enumerate(levels, start=1):
        query += "SELECT * FROM (SELECT * FROM example WHERE level = ? AND operator IN (?operator?) ORDER BY random() LIMIT "
        query += str(weights[idx-1]) + ") AS level" + str(idx)
        query += " UNION ALL "
        args.append(level)
        for operator in operators:
            args.append(operator)
    query = query.replace("?operator?", ", ".join("?" * len(operators)))
    query = query[:-len(" UNION ALL ")] if len(query) else ""
    with closing(sqlite3.connect(SQLITE_DB)) as conn:
        conn.row_factory = dict_factory
        with closing(conn.cursor()) as cursor:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute(query, tuple(args))
            test = cursor.fetchall()
            cursor.execute("INSERT INTO test (user_id) VALUES (?);", (session["user_id"],))
            session["test_id"] = cursor.lastrowid
            for ex in test:
                ex.update({"test_id": session["test_id"]})
            cursor.executemany("INSERT INTO test_example (test_id, example_id) VALUES (:test_id, :id);", test)
            cursor.execute("COMMIT;")
            return jsonify(render_template("test_start.html", test=test))
    
    return apology("There are no available tests!", 404)


@app.route("/test_continue", methods=["GET"])
@login_required
def test_continue():
    if "test_id" in session:
        test = db_execute(SQLITE_DB,
                          "SELECT example_id, ROW_NUMBER() OVER (ORDER BY level, example_id) AS number, example, answer, timegiven, timespent FROM results WHERE user_id = ? AND test_id = ?;",
                          (session["user_id"], session["test_id"],),
                          False)
        if test is not None and len(test):
            
            return jsonify(render_template("test_start.html", test=test))
    return apology("No tests to continue!", 404)


@app.route("/test_generate", methods=["GET", "POST"])
@admin_required
def test_generate():
    if request.method == "GET":
        return render_template("test_generate.html")
    num = int(request.form.get("examples")) if request.form.get("examples") else 20
    examples = generate_examples(num)
    try:
        with closing(sqlite3.connect(SQLITE_DB)) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("BEGIN TRANSACTION;")
                query = "INSERT INTO example (example, level, operator, eval) VALUES (:example, :level, :operator, :eval);"
                cursor.executemany(query, examples)
                cursor.execute("COMMIT;")
                return dynamic_flash(u"Examples generated successfully!", "info")
    except:
        return dynamic_flash(u"Couldn't generate examples!", "danger")


@app.route("/example_answer", methods=["POST"])
def example_answer():
    db_execute(SQLITE_DB, 
               "INSERT INTO result (user_id, test_id, example_id, answer, timespent) VALUES (?, ?, ?, ?, ?);",
               (session["user_id"], session["test_id"], request.form.get("example_id"), request.form.get("answer"), request.form.get("timespent"),))
    example = db_execute(SQLITE_DB, 
                         "SELECT CAST(eval AS INT) AS eval FROM example WHERE example_id = ?;",
                         (request.form.get("example_id"),))
    return jsonify(example)


@app.route("/scores", methods=["GET"])
def scores():
    scores = db_execute(SQLITE_DB, "SELECT * FROM result JOIN example ON result.example_id = example.id JOIN test ON result.test_id = test.id LIMIT 100;")
    return render_template("scores.html", scores=scores)


@app.route("/results", methods=["GET"])
@login_required
def results():
    results = db_execute(SQLITE_DB, "SELECT * FROM result JOIN example ON result.example_id = example.id JOIN test ON result.test_id = test.id WHERE result.user_id = ?;", (session["user_id"],))
    return render_template("results.html", results=results)


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/_add_numbers")
def add_numbers():
    a = request.args.get("a", 0, type=int)
    b = request.args.get("b", 0, type=int)
    return jsonify(result=a + b)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

