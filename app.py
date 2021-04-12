from os import getenv
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from flask_mail import Mail, Message
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from contextlib import closing

from webApp.helpers import apology, login_required, admin_required
from webApp.tests import generate_examples, calculate_weights, duplicate_examples
from webApp.app_config import app_config

import json
import sqlite3
#import re

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

# Configure session to use redis
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "redis"
Session(app)

# Configure mail
app.config["MAIL_DEFAULT_SENDER"] = app_config["MAIL_DEFAULT_SENDER"]
app.config["MAIL_USERNAME"] = app_config["MAIL_USERNAME"]
app.config["MAIL_PASSWORD"] = app_config["MAIL_PASSWORD"]
app.config["MAIL_PORT"] = app_config["MAIL_PORT"]
app.config["MAIL_SERVER"] = app_config["MAIL_SERVER"]
app.config["MAIL_USE_TLS"] = app_config["MAIL_USE_TLS"]
mail = Mail(app)

# Global gender list for '/profile':
GENDER_LIST = ["male", "female", "other"]

# Global path to the main database for 'db_execute'
SQLITE_DB = app_config["SQL_DB"]

TIMEFRAME = {"today": 0, "day": 1, "week": 7, "month": 30, "year": 365, "alltime": 9999}

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
                         "SELECT user_temp.id AS id, user_temp.hash AS hash, user_temp.type AS type, profile.name AS name, profile.email FROM (SELECT id, hash, type FROM user WHERE login = ?) AS user_temp LEFT JOIN profile ON user_temp.id = profile.user_id;",
                         (request.form.get("login"),))
            
        # Ensure login exists and password is correct
        if row is None or not check_password_hash(row["hash"], request.form.get("password")):
            return apology("invalid login and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = row["id"]

        # Remember user's name
        session["user_name"] = row["name"]

        session["admin"] = True if (row["type"] and "admin" in row["type"]) else False

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
    return dynamic_flash(u"Profile update was successful!", "info")


@app.route("/name_update", methods=["POST"])
@login_required
def name_update():
    db_execute(SQLITE_DB, "UPDATE profile SET name = ? WHERE user_id = ?;", (request.form.get("name"), session["user_id"],))
    session["user_name"] = request.form.get("name")
    return dynamic_flash(u"Good to see you, {0}!".format(session["user_name"]),"primary")


@app.route("/email_update", methods=["POST"])
@login_required
def email_update():
    db_execute(SQLITE_DB, "UPDATE profile SET email = ? WHERE user_id = ?;", (request.form.get("email"), session["user_id"],))
    return dynamic_flash(u"Email was successfully updated!", "primary")


@app.route("/password_update", methods=["POST"])
@login_required
def password_update():
    """Change password"""
    if request.form.get("password") == request.form.get("confirmation"):
        row = db_execute(SQLITE_DB, "UPDATE user SET hash = ? WHERE id = ?;", (generate_password_hash(request.form.get("password")), session["user_id"],))
        row = db_execute(SQLITE_DB, "SELECT name, email FROM profile WHERE user_id = ?", (session["user_id"],))
        if row["email"]:
            message = Message("Hello, {}!".format(row['name']), recipients=[row["email"]])
            message.body = "This is 45.138.96.189!\nYou received this email because your password has been changed to '{}'".format(request.form.get("password"))
            mail.send(message)
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
    test_continue = None
    if "user_id" in session:
        query = """
        SELECT 
          operators.test_id AS id, 
          test.date, 
          operators.operators, 
          levels.levels, 
          operators.examples 
        FROM 
          (
            SELECT 
              test_id, 
              GROUP_CONCAT(operator) AS operators, 
              SUM(examples) AS examples 
            FROM 
              (
                SELECT 
                  test_id, 
                  operator, 
                  COUNT(*) AS examples 
                FROM 
                  example 
                  JOIN (
                    SELECT 
                      test_example.test_id, 
                      test_example.example_id 
                    FROM 
                      test_example 
                      LEFT JOIN result ON test_example.test_id = result.test_id 
                      AND test_example.example_id = result.example_id 
                    WHERE 
                      test_example.test_id IN (
                        SELECT 
                          id 
                        FROM 
                          test 
                        WHERE 
                          user_id = :user_id
                      ) 
                      AND answer IS NULL
                  ) AS test ON example.id = test.example_id 
                GROUP BY 
                  test_id, 
                  operator 
                ORDER BY 
                  example.id
              ) 
            GROUP BY 
              test_id
          ) AS operators 
          JOIN (
            SELECT 
              test_id, 
              GROUP_CONCAT(level) AS levels 
            FROM 
              (
                SELECT 
                  DISTINCT test_id, 
                  level 
                FROM 
                  example 
                  JOIN (
                    SELECT 
                      test_example.test_id, 
                      test_example.example_id 
                    FROM 
                      test_example 
                      LEFT JOIN result ON test_example.test_id = result.test_id 
                      AND test_example.example_id = result.example_id 
                    WHERE 
                      test_example.test_id IN (
                        SELECT 
                          id 
                        FROM 
                          test 
                        WHERE 
                          user_id = :user_id
                      ) 
                      AND answer IS NULL
                  ) AS test ON example.id = test.example_id 
                ORDER BY 
                  level, 
                  example.id
              ) 
            GROUP BY 
              test_id
          ) AS levels ON operators.test_id = levels.test_id 
          JOIN test ON operators.test_id = test.id;"""
        test_continue = db_execute(SQLITE_DB, query, dict(session), False)
    levels = db_execute(SQLITE_DB, "SELECT DISTINCT level FROM example ORDER BY level;", "", False)
    operators = db_execute(SQLITE_DB, "SELECT DISTINCT operator FROM example ORDER BY id;", "", False)
    return render_template("tests.html", levels=levels, operators=operators, test_continue=test_continue)


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
    n_examples = int(request_args.get("examples")[0]) if request_args.get("examples") else 10
    query = ""
    args = []
    weights = calculate_weights(n_examples, levels)
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
            #if len(test) < n_examples:
            #    test = duplicate_examples(test, n_examples - len(test))
            cursor.execute("INSERT INTO test (user_id) VALUES (?);", (session["user_id"],))
            session["test_id"] = cursor.lastrowid
            for idx, ex in enumerate(test, start=1):
                ex.update({"test_id": session["test_id"], "number": idx})
            cursor.executemany("INSERT INTO test_example (test_id, example_id) VALUES (:test_id, :id);", test)
            cursor.execute("COMMIT;")
            return jsonify(render_template("test_start.html", test=test))
    
    return apology("There are no available tests!", 404)


@app.route("/test_continue", methods=["GET"])
@login_required
def test_continue():
    try:
        session["test_id"] = request.args.get("test_id")
        test = db_execute(SQLITE_DB,
                          "SELECT test.id AS test_id, test_example.example_id AS id, example.example, example.level, example.operator, ROW_NUMBER() OVER (ORDER BY example.id) AS number FROM test JOIN test_example ON test.id = test_example.test_id JOIN example ON test_example.example_id = example.id LEFT JOIN result ON test_example.test_id = result.test_id AND test_example.example_id = result.example_id WHERE test.id = :test_id AND test.user_id = :user_id AND answer IS NULL;",
                          dict(session),
                          False)
            
        return jsonify(render_template("test_start.html", test=test))
    except:
        return apology("No tests to continue!", 404)


@app.route("/test_generate", methods=["GET", "POST"])
@admin_required
def test_generate():
    if request.method == "GET":
        return render_template("test_generate.html")
    n_examples = int(request.form.get("examples")) if request.form.get("examples") else 20
    examples = generate_examples(n_examples)
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
               "INSERT INTO result (user_id, test_id, example_id, answer, level, timespent) VALUES (?, ?, ?, ?, ?, ?);",
               (session["user_id"], session["test_id"], request.form.get("example_id"), request.form.get("answer"), request.form.get("level"), request.form.get("timespent"),))
    example = db_execute(SQLITE_DB, "SELECT CAST(eval AS INT) AS eval FROM example WHERE id = ?;", (request.form.get("example_id"),))
    return jsonify(example)


@app.route("/scores", methods=["GET"])
def scores():
    pastdays = {"pastdays": TIMEFRAME["week"]} # Default time frame for score table
    if request.args.get("pastdays") and TIMEFRAME["today"] <= int(request.args.get("pastdays")) <= TIMEFRAME["alltime"]:
        pastdays.update({"pastdays": int(request.args.get("pastdays"))})
    scores = dict()
    query = "SELECT *, ROW_NUMBER() OVER (ORDER BY answers DESC, examples DESC, avgtime) AS rank FROM (SELECT results.user_id, profile.name, shared.shared, shared.gender, shared.birthdate, shared.education, shared.bio, examples, right, wrong, ROUND(CAST(right AS FLOAT)*100/examples, 1) AS answers, avgtime FROM (SELECT user_id, COUNT(*) AS examples, CAST(AVG(timespent) AS INT) AS avgtime FROM result WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays AND answer IS NOT NULL GROUP BY user_id) AS results JOIN profile ON results.user_id = profile.user_id LEFT JOIN profile AS shared ON results.user_id = shared.user_id AND shared.shared LEFT JOIN (SELECT SUM(CASE WHEN eval = answer THEN 1 ELSE 0 END) AS right, SUM(CASE WHEN eval = answer THEN 0 ELSE 1 END) AS wrong, user_id FROM result JOIN example ON result.example_id = example.id WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays GROUP BY user_id) AS checks ON results.user_id = checks.user_id WHERE examples >= 10) LIMIT 25;"
    scores["overall"] = db_execute(SQLITE_DB, query, pastdays, False)
    query = "SELECT *, ROW_NUMBER() OVER (ORDER BY avgtime, examples DESC, answers DESC) AS rank FROM (SELECT results.user_id, profile.name, shared.shared, shared.gender, shared.birthdate, shared.education, shared.bio, examples, right, wrong, ROUND(CAST(right AS FLOAT)*100/examples, 1) AS answers, avgtime FROM (SELECT user_id, COUNT(*) AS examples, CAST(AVG(timespent) AS INT) AS avgtime FROM result WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays AND answer IS NOT NULL GROUP BY user_id) AS results JOIN profile ON results.user_id = profile.user_id LEFT JOIN profile AS shared ON results.user_id = shared.user_id AND shared.shared LEFT JOIN (SELECT SUM(CASE WHEN eval = answer THEN 1 ELSE 0 END) AS right, SUM(CASE WHEN eval = answer THEN 0 ELSE 1 END) AS wrong, user_id FROM result JOIN example ON result.example_id = example.id WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays GROUP BY user_id) AS checks ON results.user_id = checks.user_id WHERE examples >= 10) WHERE answers >= 90 LIMIT 25;"
    scores["avgtime"] = db_execute(SQLITE_DB, query, pastdays, False)
    query = "SELECT *, ROW_NUMBER() OVER (ORDER BY answers DESC, examples DESC, avgtime) AS rank FROM (SELECT results.user_id, profile.name, shared.shared, shared.gender, shared.birthdate, shared.education, shared.bio, examples, right, wrong, ROUND(CAST(right AS FLOAT)*100/examples, 1) AS answers, avgtime FROM (SELECT user_id, COUNT(*) AS examples, CAST(AVG(timespent) AS INT) AS avgtime FROM result WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays AND answer IS NOT NULL GROUP BY user_id) AS results JOIN profile ON results.user_id = profile.user_id LEFT JOIN profile AS shared ON results.user_id = shared.user_id AND shared.shared LEFT JOIN (SELECT SUM(CASE WHEN eval = answer THEN 1 ELSE 0 END) AS right, SUM(CASE WHEN eval = answer THEN 0 ELSE 1 END) AS wrong, user_id FROM result JOIN example ON result.example_id = example.id WHERE CAST(JULIANDAY('now')-JULIANDAY(date) AS INT) <= :pastdays GROUP BY user_id) AS checks ON results.user_id = checks.user_id WHERE examples >= 10 AND STRFTIME('%Y', 'now') - STRFTIME('%Y', profile.birthdate) <= 10) LIMIT 25;"
    scores["underage10"] = db_execute(SQLITE_DB, query, pastdays, False)
    return render_template("scores.html", scores=scores, timeframes=TIMEFRAME, active=pastdays["pastdays"])


@app.route("/results", methods=["GET"])
@login_required
def results():
    query = "SELECT test.id AS test_id, test.date, test_example.example_id, example, eval, answer, CASE eval WHEN answer THEN 1 ELSE 0 END AS checked, timespent FROM test LEFT JOIN test_example ON test.id = test_example.test_id LEFT JOIN result ON test_example.test_id = result.test_id AND test_example.example_id = result.example_id LEFT JOIN example ON test_example.example_id = example.id WHERE test.user_id = ? AND answer IS NOT NULL;"
    table_data = db_execute(SQLITE_DB, query, (session["user_id"],), False)
    
    data = db_execute(SQLITE_DB, "SELECT example, timespent FROM result LEFT JOIN example ON result.example_id = example.id WHERE user_id = ?;", (session["user_id"],), False)
    histogram_timespent = [['Example', 'time spent, ms']]
    for row in data:
        histogram_timespent.append([row['example'], row['timespent']])
    
    data = db_execute(SQLITE_DB, "SELECT SUM(right) AS right, SUM(wrong) AS wrong FROM (SELECT CASE eval WHEN answer THEN 1 ELSE 0 END AS right, CASE eval WHEN answer THEN 0 ELSE 1 END AS wrong FROM test LEFT JOIN test_example ON test.id = test_example.test_id LEFT JOIN result ON test_example.test_id = result.test_id AND test_example.example_id = result.example_id LEFT JOIN example ON test_example.example_id = example.id WHERE test.user_id = ? AND answer IS NOT NULL);", (session["user_id"],))
    piechart_check = [['Right/Wrong', 'Examples']]
    piechart_check.append(['Right', data['right']])
    piechart_check.append(['Wrong', data['wrong']])
    
    data = db_execute(SQLITE_DB, "SELECT result.level, COUNT(*) AS examples FROM test LEFT JOIN test_example ON test.id = test_example.test_id LEFT JOIN result ON test_example.test_id = result.test_id AND test_example.example_id = result.example_id LEFT JOIN example ON test_example.example_id = example.id WHERE test.user_id = ? AND answer IS NOT NULL GROUP BY result.level;", (session["user_id"],), False)
    piechart_levels = [['Levels', 'Examples']]
    for row in data:
        piechart_levels.append(['Level '+str(row['level']), row['examples']])
    
    data = db_execute(SQLITE_DB, "SELECT example.operator, COUNT(*) AS examples FROM test LEFT JOIN test_example ON test.id = test_example.test_id LEFT JOIN result ON test_example.test_id = result.test_id AND test_example.example_id = result.example_id LEFT JOIN example ON test_example.example_id = example.id WHERE test.user_id = ? AND answer IS NOT NULL GROUP BY example.operator;", (session["user_id"],), False)
    piechart_operations = [['Operations', 'Examples']]
    for row in data:
        piechart_operations.append([row['operator'], row['examples']])
    return render_template("results.html", table_data=table_data, histogram_timespent=histogram_timespent, piechart_check=piechart_check, piechart_levels=piechart_levels, piechart_operations=piechart_operations)


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/semenov")
def semenov():
    return render_template("semenov.html")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def db_execute(db, query, args=(), fetchone=True):
    """
    Auto-closing and auto-committing function for sqlite3 queries.
    https://flask-doc.readthedocs.io/en/latest/patterns/sqlite3.html
    """
    with closing(sqlite3.connect(db)) as conn: # auto-closes
        conn.row_factory = dict_factory
        with conn: # auto-commits
            with closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(query, args)
                if any(key in query for key in ["INSERT", "REPLACE"]):
                    return cursor.lastrowid
                rv = cursor.fetchall()
                return (rv[0] if rv else None) if fetchone else rv

def db_executemany(db, query, args=()):
    """
    Auto-closing and auto-committing function for sqlite3 queries.
    """
    with closing(sqlite3.connect(db)) as conn: # auto-closes
        with conn: # auto-commits
            with closing(conn.cursor()) as cursor: # auto-closes
                cursor.executemany(query, args)
                return cursor.rowcount


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
