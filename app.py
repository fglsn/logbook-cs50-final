from dbsession import DbSessionInterface
from flask import Flask, session, render_template, redirect, request
from flask.globals import request
from db import fetch, fetch_one, execute
from random import randint
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from tempfile import mkdtemp
import re
from functools import wraps
from datetime import datetime
import pytz 

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

#For passwords strength validation
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

#Set timezone 
default_timezone = pytz.timezone('Europe/Tallinn')

#Date and time parsation
def parse_date_or_none(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None
def parse_time_or_none(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M')
    except ValueError:
        return None

#Input to proper types
def int_or_none(int_str):
    if not int_str:
        return None
    try:
        return int(int_str)
    except ValueError:
        return None
def float_or_none(float_str):
    if not float_str:
        return None
    try:
        return float(float_str)
    except ValueError:
        return None

#Format date and time to display properly on page
def format_date(value):
    return value.strftime('%d.%m.%Y')
app.jinja_env.filters["format_date"] = format_date

def format_time(value):
    return value.strftime('%H:%M')
app.jinja_env.filters["format_time"] = format_time 

@app.route('/', methods=["GET"])
def index():
    user_id = session.get("user_id")
    if user_id:
        return redirect("/rides")
    else:
        return render_template("index.html")

@app.route('/rides', methods=["GET", "POST"])
@login_required
def rides():
    user_id = session.get("user_id")
    vehicle_rows = fetch("SELECT reg_num, odometer, allowance FROM vehicles WHERE user_id=%(user_id)s", user_id=user_id)
    for vehicle_row in vehicle_rows:
        vehicle_row["allowance"] = str(vehicle_row["allowance"])

    if request.method == "POST":
        registration_number = request.form.get("vehicles")
        log_date = parse_date_or_none(request.form.get("date"))
        st_time = parse_time_or_none(request.form.get("starting_time"))
        end_time = parse_time_or_none(request.form.get("ending_time"))
        st_km = int_or_none(request.form.get("starting_km"))
        end_km = int_or_none(request.form.get("ending_km"))
        allowance = float_or_none(request.form.get("allowance"))
        distance = int_or_none(request.form.get("distance"))
        route = request.form.get("route")

        if not registration_number or not log_date or not st_time or not end_time or not st_km or not distance or not allowance: 
            return render_template("rides.html", error_message="Check required fields", vehicle_rows=vehicle_rows)
        elif allowance <= 0:
            return render_template("rides.html", error_message="Incorrect allowance value", vehicle_rows=vehicle_rows)

        vehicle = fetch_one("SELECT id FROM vehicles WHERE reg_num = %(registration_number)s", registration_number=registration_number) 
        if not vehicle: 
            return render_template("rides.html", error_message="Vehicle not recognized", vehicle_rows=vehicle_rows)

        if distance <= 0 or st_km < 0 or end_km <= 0:
            return render_template("rides.html", error_message="Odometer readings or distance cannot be negative and should be more than 0 (except start)", vehicle_rows=vehicle_rows)

        if not log_date:
            return render_template("rides.html", error_message="Incorrect data format, should be yyyy-mm-dd", vehicle_rows=vehicle_rows)
        elif not st_time or not end_time:
            return render_template("rides.html", error_message="Incorrect time format, should be hh:mm", vehicle_rows=vehicle_rows)

        present = datetime.now(tz=default_timezone)
        started_at = datetime.combine(log_date, st_time.time()).astimezone(default_timezone)
        finished_at = datetime.combine(log_date, end_time.time()).astimezone(default_timezone)
        print(started_at, finished_at)
        if started_at > present or finished_at > present:
            return render_template("rides.html", error_message="You can only add past rides", vehicle_rows=vehicle_rows)
        elif started_at > finished_at: 
            return render_template("rides.html", error_message="Check start and finish times", vehicle_rows=vehicle_rows)

        execute("INSERT INTO rides (vehicle_id, started_at, finished_at, odometer_start, distance, allowance, route) VALUES (%(vehicle_id)s, %(started_at)s, %(finished_at)s, %(odometer_start)s, %(distance)s, %(allowance)s, %(route)s)",
                        vehicle_id=vehicle["id"], started_at=started_at, finished_at=finished_at, odometer_start=st_km, distance=distance, allowance=allowance, route=route)

        execute("UPDATE vehicles SET odometer = %(updated_odometer)s, modified_at=now() WHERE id=%(vehicle_id)s and odometer < %(updated_odometer)s", updated_odometer=st_km + distance, vehicle_id=vehicle["id"])

    reg_num_rows = fetch("SELECT reg_num FROM vehicles WHERE user_id = %(user_id)s",
                            user_id=user_id)    
    reg_nums = []
    for reg_num_row in reg_num_rows:
        reg_nums.append(reg_num_row["reg_num"])
    
    selected_reg_nums = []
    for k, v in request.args.items():
        if k in reg_nums and v == "on":
            selected_reg_nums.append(k)
    
    if not selected_reg_nums:
        selected_reg_nums = reg_nums
    else:
        for vehicle_row in vehicle_rows:
            if vehicle_row["reg_num"] in selected_reg_nums:
                vehicle_row["selected"] = True
            
    rides = fetch("SELECT started_at, finished_at, odometer_start, distance, rides.allowance as allowance, route, reg_num, odometer_start + distance as odometer_finish, rides.allowance * distance as total FROM rides LEFT JOIN vehicles on rides.vehicle_id=vehicles.id WHERE user_id = %(user_id)s and reg_num in %(selected_reg_nums)s ORDER BY finished_at",
                            user_id=user_id, selected_reg_nums=tuple(selected_reg_nums))

    for ride in rides:
        start = ride['started_at']
        end = ride['finished_at']
        ride['date'] = start.date()
        ride['start'] = start.time()
        ride['finish'] = end.time()

    return render_template("rides.html", vehicle_rows=vehicle_rows, rides=rides)


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


@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return redirect("/")