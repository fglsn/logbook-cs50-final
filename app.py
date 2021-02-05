from dbsession import DbSessionInterface
from flask import Flask, session, render_template, redirect
from flask.globals import request
from db import fetch, fetch_one, execute
from random import randint
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from tempfile import mkdtemp
import re
from functools import wraps

app = Flask(__name__)

app.session_interface = DbSessionInterface()


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

    print('login start')
    session.clear()

    if request.method == "POST":

        if not request.form.get("email"):
            return render_template("login.html", error_message="Please provide your email address to log in")
        
        elif not request.form.get("password"):
            return render_template("login.html", error_message="Please provide password")

        rows = fetch("SELECT * FROM users WHERE email = %(email)s",
                          email=request.form.get("email"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error_message="Invalid username and/or password")

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    
    else:
        return render_template("login.html")

#For pwd strength validation
def password_validation(password):

    length_error = len(password) < 8
    ws_error = re.search(r"\s", password) is not None
    digit_error = re.search(r"\d", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    lowercase_error = re.search(r"[a-z]", password) is None
    symbol_error = re.search(r"\W", password) is None

    return not (length_error or digit_error or uppercase_error or lowercase_error or symbol_error or ws_error)    

@app.route('/register', methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "GET":
        return render_template("register.html")
    
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        #Validate input
        if not email:
            return render_template("register.html", error_message="Email is required")
        elif not password:
            return render_template("register.html", error_message="Password is required")
        elif not confirmation: 
            return render_template("register.html", error_message="Please enter password confirmation")

        if password != confirmation:
            return render_template("register.html", error_message="Password confirmation doesn't match")
        
        if not password_validation(password):
            return render_template("register.html", error_message="Your password is too weak")

        email = email.strip().lower()
        # Query database for username
        rows = fetch("SELECT * FROM users WHERE email = %(email)s",
                          email=email)
        if rows:
            return render_template("register.html", error_message="Account with this email address already exists, please choose another one") 

        user = fetch_one("INSERT INTO users(email, hash) VALUES (%(email)s, %(hash)s) RETURNING id",
                        email=email, hash=generate_password_hash(password))

        session["user_id"] = user["id"]
        return redirect("/")

#Decorate routes to require login.
#http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
def login_required(f):
   
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    return render_template("index.html")
    

#For reg.plate number validation
def reg_num_validation(reg_num):
    private_re=re.compile("^[A-Za-z]{3}-[0-9]{3}$")
    diplomat_re=re.compile("^CD-[0-9]{4}$")
    other_diplomat_re=re.compile("^C-[0-9]{5}$")

    private_matches = private_re.search(reg_num) is not None
    diplomat_matches = diplomat_re.search(reg_num) is not None
    other_diplomat_matches = other_diplomat_re.search(reg_num) is not None

    return private_matches or diplomat_matches or other_diplomat_matches    


@app.route('/vehicles', methods=["GET", "POST"])
@login_required
def vehicles():

    user_id = session.get("user_id")

    if request.method == "POST":
        reg_num = request.form.get("reg_num")
        allowance = request.form.get("allowance")
        odometer = request.form.get("odometer")

        if not reg_num or not allowance or not odometer:
            return render_template("vehicles.html", error_message="Check required fields")
        elif float(allowance) <= 0:
            return render_template("vehicles.html", error_message="Allowance: how many € per km? Enter positive number")
        elif int(odometer) < 0:
            return render_template("vehicles.html", error_message="Odometer reading cannot be negative")
        
        if not reg_num_validation(reg_num):
            return render_template("vehicles.html", error_message="Invalid registration number")
        
        reg_num = reg_num.strip().upper()

        # Query database for vehicle
        vehicle_rows = fetch("SELECT * FROM vehicles WHERE reg_num = %(reg_num)s",
                          reg_num=reg_num)
        if vehicle_rows:
            return render_template("vehicles.html", error_message="Vehicle already exists") 

        execute("INSERT INTO vehicles(user_id, reg_num, allowance, odometer) VALUES (%(user_id)s, %(reg_num)s, %(allowance)s, %(odometer)s)",
                        user_id=user_id, reg_num=reg_num, allowance=allowance, odometer=odometer)
    
    vehicles = fetch("SELECT * FROM vehicles WHERE user_id = %(user_id)s ORDER BY modified_at",
                            user_id=user_id)

    return render_template("vehicles.html", vehicles=vehicles)