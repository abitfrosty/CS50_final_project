from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, db_execute, usd
from tests import generate_test, prepare_test_for_sql
#from datetime import datetime
import re
import sqlite3


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


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Global gender list for '/profile':
GENDER_LIST = ["male", "female", "other"]

# Global path to the main database for 'db_execute'
SQLITE_DB = "project.db"


@app.template_filter('quoted')
def quoted(s):
    l = re.findall("'(.*)\.html'", str(s))
    if l:
        return l[0]
    return None


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
                         "SELECT users_temp.id AS id, users_temp.hash AS hash, profiles.name AS name FROM (SELECT id, hash FROM users WHERE login = ?) AS users_temp LEFT JOIN profiles ON users_temp.id = profiles.users_id;",
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


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    """User's profile"""
    row = db_execute(SQLITE_DB, "SELECT * FROM profiles WHERE users_id = ?;", (session["user_id"],))
    row["gender_list"] = GENDER_LIST
    return render_template("profile.html", profile=row)


@app.route("/update_name", methods=["POST"])
@login_required
def update_name():
    try:
        db_execute(SQLITE_DB, "UPDATE profiles SET name = ? WHERE users_id = ?;", (request.form.get("name"), session["user_id"],))
        session["user_name"] = request.form.get("name")
        return jsonify(name=session["user_name"])
    except:
        return None


@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    if request.form.get("gender") is not None and request.form.get("gender") not in GENDER_LIST:
        return apology("Gender was not recognized!", 403)
        
    data = request.form.to_dict()
    params = []
    query = "UPDATE profiles SET "
    for k, v in data.items():
        query += k + " = ?, "
        params.append(v)
    params.append(session["user_id"])
    query = query[:-2]
    query += " WHERE users_id = ?;"

    db_execute(SQLITE_DB, query, params)
    """ SQL Query sample
    row = db_execute(SQLITE_DB, 
                     "UPDATE profiles SET gender = ?, birthdate = ?, education = ?, bio = ? WHERE users_id = ?;",
                     (request.form.get("gender"),request.form.get("birthdate"),request.form.get("education"),request.form.get("bio"),session["user_id"],))
    """
    flash("Profile update was successful!")
    return redirect("/profile")


@app.route("/update_password", methods=["POST"])
@login_required
def update_password():
    """Change password"""
    row = db_execute(SQLITE_DB, "UPDATE users SET hash = ? WHERE id = ?;", (generate_password_hash(request.form.get("password")), session["user_id"],))
    flash("Your password has been changed successfully!")
    return redirect("/profile")


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

    row = db_execute(SQLITE_DB, "SELECT * FROM users WHERE login = ?", (request.form.get("login"),))
    if row is not None:
        apology_t = "login already exists"

    if len(apology_t):
        return apology(apology_t, apology_c)

    user_id = db_execute(SQLITE_DB, "INSERT INTO users (login, hash) VALUES (?, ?)", (request.form.get("login"), generate_password_hash(request.form.get("password")),))
    db_execute(SQLITE_DB, "INSERT INTO profiles (users_id) VALUES (?);", (user_id,))
    session["user_id"] = user_id
    flash("New user's registration with id \"{0}\" was successful!".format(user_id))
    return redirect("/")


@app.route("/tests", methods=["GET"])
def tests():
    return render_template("tests.html")


@app.route("/generate_test", methods=["GET"])
@login_required
def generate_test():
    with closing(sqlite3.connect(SQLITE_DB)) as conn: # auto-closes
        with closing(conn.cursor()) as cursor: # auto-closes
            query = "INSERT INTO tests (users_id, level) VALUES (?, ?)"
            args = (session["user_id"], request.args.get("level"),)
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(query, args)
            rowid = cursor.lastrowid
            test = generate_test(level=request.args.get("level"), n=request.args.get("questions"))
            query = "INSERT INTO tests (users_id, level) VALUES (?, ?)"
            args = prepare_test_for_sql(test, users_id=session["user_id"], tests_id=rowid, timegiven=request.args.get("time"))
            cursor.executemany(query, args)
            cursor.execute("COMMIT")
            return render_template("generate_test.html", test=test)
            #return jsonify(test)
    
    return False
    """
    rowid = db_execute(SQLITE_DB, "INSERT INTO tests (users_id, level) VALUES (?, ?)", (session["user_id"], request.args.get("level"),))
    test = generate_test(level=request.args.get("level"), n=request.args.get("questions"))
    test_sql = prepare_test_for_sql(test, users_id=session["user_id"], tests_id=rowid, request.args.get("time"))
    db_executemany(SQLITE_DB, "INSERT INTO examples (users_id, tests_id, level, number, example, eval, timegiven) VALUES (?, ?, ?, ?, ?, ?)", test_sql)
    return jsonify(test)
    """


@app.route("/example_answer", methods=["POST"])
def example_answer():
    # SQL insert and return true
    return True


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

