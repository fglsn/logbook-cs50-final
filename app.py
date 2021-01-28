from flask import Flask, session, render_template
from db import get_db_cursor

app = Flask(__name__)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/login', methods=["GET", "POST"])
def login():

    #session.clear()

    return render_template("login.html")
    
    #with get_db_cursor() as cursor:
    #    cursor.execute('select id, name from squanches')
    #    squanches = cursor.fetchmany()
    #return f'Hello, this is login response for now, and these are squanches: '

@app.route('/register', methods=["GET", "POST"])
def register():

    return render_template("register.html")


@app.route('/', methods=["GET", "POST"])
def index():

    return render_template("index.html")