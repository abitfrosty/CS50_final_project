import os, sys
import urllib.parse
import sqlite3

from flask import redirect, render_template, request, session
from functools import wraps
from contextlib import closing


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def db_execute(db, query, args=(), fetchone=True):
    """
    Auto-closing and auto-committing function for sqlite3 queries.
    https://flask-doc.readthedocs.io/en/latest/patterns/sqlite3.html
    """
    with closing(sqlite3.connect(db)) as conn: # auto-closes
        with conn: # auto-commits
            with closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(query, args)
                if any(key in query for key in ["INSERT", "REPLACE"]):
                    return cursor.lastrowid
                rv = [dict((cursor.description[idx][0], value) for idx, value in enumerate(row)) for row in cursor.fetchall()]
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


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

