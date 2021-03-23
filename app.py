from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, db_execute, usd
#from tests import generate_tests, prepare_test_for_sql
from tests import Test
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
                         "SELECT user_temp.id AS id, user_temp.hash AS hash, profile.name AS name FROM (SELECT id, hash FROM user WHERE login = ?) AS user_temp LEFT JOIN profile ON user_temp.id = profile.user_id;",
                         (request.form.get("login"),))
            
        # Ensure login exists and password is correct
        if row is None or not check_password_hash(row["hash"], request.form.get("password")):
            return apology("invalid login and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row["id"]

        # Remember user's name
        session["user_name"] = row["name"]

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
    params.append(session["user_id"])
    query = query[:-2]
    query += " WHERE user_id = ?;"

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
    return render_template("tests.html")


@app.route("/test_start", methods=["GET"])
@login_required
def test_start():
    """
    Dynamic html (jsonify, jinja, jquery, ajax)
    https://stackoverflow.com/questions/40701973/create-dynamically-html-div-jinja2-and-ajax
    """
    # Can be soon moved to /test_continue
    if "test_id" in session:
        test = db_execute(SQLITE_DB,
                          "SELECT example_id, ROW_NUMBER() OVER (ORDER BY example_id) AS number, example, answer, timegiven, timespent FROM results WHERE user_id = ? AND test_id = ?;",
                          (session["user_id"], session["test_id"],),
                          False)
        if test is not None and len(test):
            return jsonify(render_template("test_start.html", test=test))
    
    # Part /test_start
    with closing(sqlite3.connect(SQLITE_DB)) as conn: # auto-closes
        with closing(conn.cursor()) as cursor: # auto-closes
            query = "INSERT INTO test (user_id, level) VALUES (?, ?);"
            args = (session["user_id"], int(request.args.get("level")),)
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute(query, args)
            test_id = cursor.lastrowid
            test = ""#generate_tests(int(request.args.get("level")), int(request.args.get("example")))
            query = "INSERT INTO example (user_id, test_id, number, example, eval, timegiven) VALUES (:user_id, :test_id, :number, :example, :eval, :timegiven);"
            args = ""#prepare_test_for_sql(test, session["user_id"], test_id, int(request.args.get("time")))
            cursor.executemany(query, args)
            cursor.execute("COMMIT;")
            session["test_id"] = test_id
            return jsonify(render_template("test_start.html", test=args))


"""
@app.route("/test_generate", methods=["GET"])
@login_required
def test_generate():
"""
    #Dynamic html (jsonify, jinja, jquery, ajax)
    #https://stackoverflow.com/questions/40701973/create-dynamically-html-div-jinja2-and-ajax
"""
    if "test_id" in session:
        test = db_execute(SQLITE_DB,
                          "SELECT user_id, test_id, number, example, timegiven FROM example WHERE user_id = ? AND test_id = ? AND timespent = 0;",
                          (session["user_id"], session["test_id"],),
                          False)
        if test is not None and len(test):
            return jsonify(render_template("test_generate.html", test=test))

    with closing(sqlite3.connect(SQLITE_DB)) as conn: # auto-closes
        with closing(conn.cursor()) as cursor: # auto-closes
            query = "INSERT INTO tests (user_id, level) VALUES (?, ?);"
            args = (session["user_id"], int(request.args.get("level")),)
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute(query, args)
            test_id = cursor.lastrowid
            test = generate_tests(int(request.args.get("level")), int(request.args.get("example")))
            query = "INSERT INTO example (user_id, test_id, number, example, eval, timegiven) VALUES (:user_id, :test_id, :number, :example, :eval, :timegiven);"
            args = prepare_test_for_sql(test, session["user_id"], test_id, int(request.args.get("time")))
            cursor.executemany(query, args)
            cursor.execute("COMMIT;")
            session["test_id"] = test_id
            return jsonify(render_template("test_generate.html", test=args))
"""


@app.route("/example_answer", methods=["POST"])
def example_answer():
    # SQL UPDATE and return (eval-answer) difference
    db_execute(SQLITE_DB, 
               "UPDATE example SET answer = ?, timespent = ? WHERE user_id = ? AND test_id = ? AND number = ?;--AND timespent = 0;",
               (request.form.get("answer"), request.form.get("timespent"), session["user_id"], session["test_id"], request.form.get("number"),))
    example = db_execute(SQLITE_DB, "SELECT CAST(eval AS INT) AS eval, CAST(answer AS INT) AS answer FROM example WHERE user_id = ? AND test_id = ? AND number = ?;", (session["user_id"], session["test_id"], request.form.get("number"),))
    return jsonify(example)


@app.route("/scores", methods=["GET"])
def scores():
    
    return render_template("scores.html")


@app.route("/results", methods=["GET"])
@login_required
def results():
    return render_template("results.html")


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/_add_numbers")
def add_numbers():
    a = request.args.get("a", 0, type=int)
    b = request.args.get("b", 0, type=int)
    return jsonify(result=a + b)


def collect_errors(*args, **kwargs):
    pass


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

