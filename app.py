import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, render_template, g

app = Flask(__name__)
DB_PATH = os.getenv("DB_PATH", "history.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                city        TEXT    NOT NULL,
                condition   TEXT    NOT NULL,
                description TEXT    NOT NULL,
                temp        INTEGER NOT NULL,
                season      TEXT    NOT NULL,
                overlay     TEXT    NOT NULL,
                success     INTEGER NOT NULL,
                error       TEXT
            )
        """)


init_db()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


@app.route("/")
def index():
    db = get_db()

    last = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    history = db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 50").fetchall()

    total = db.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    success_count = db.execute("SELECT COUNT(*) FROM runs WHERE success = 1").fetchone()[0]
    fail_count = total - success_count

    recent = db.execute("SELECT success FROM runs ORDER BY id DESC LIMIT 24").fetchall()
    sparkline = [r["success"] for r in reversed(recent)]

    top_condition = db.execute(
        "SELECT condition, COUNT(*) as cnt FROM runs GROUP BY condition ORDER BY cnt DESC LIMIT 1"
    ).fetchone()

    return render_template(
        "dashboard.html",
        last=last,
        history=history,
        total=total,
        success_count=success_count,
        fail_count=fail_count,
        sparkline=sparkline,
        top_condition=top_condition,
        now=datetime.now(timezone.utc).strftime("%H:%M UTC"),
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
