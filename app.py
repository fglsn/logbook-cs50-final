from dbsession import DbSessionInterface
from io import StringIO
import csv
from flask import Flask, Response, session, render_template, redirect, request
from flask.globals import request
from db import fetch, fetch_one, execute
from random import randint
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from tempfile import mkdtemp
import re
from functools import wraps
from datetime import datetime, timedelta
import pytz 
from openpyxl import Workbook

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

# --FUNCTIONS-- # 

#Passwords strength validation
def password_validation(password):

    length_error = len(password) < 8
    ws_error = re.search(r"\s", password) is not None
    digit_error = re.search(r"\d", password) is None
    uppercase_error = re.search(r"[A-Z]", password) is None
    lowercase_error = re.search(r"[a-z]", password) is None
    symbol_error = re.search(r"\W", password) is None

    return not (length_error or digit_error or uppercase_error or lowercase_error or symbol_error or ws_error)    

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
def format_date_time(value):
    return value.strftime('%d.%m.%Y %H:%M')

#For reg.plate number validation
def reg_num_validation(reg_num):
    private_re=re.compile("^[A-Za-z]{3}-[0-9]{3}$")
    diplomat_re=re.compile("^CD-[0-9]{4}$")
    other_diplomat_re=re.compile("^C-[0-9]{5}$")

    private_matches = private_re.search(reg_num) is not None
    diplomat_matches = diplomat_re.search(reg_num) is not None
    other_diplomat_matches = other_diplomat_re.search(reg_num) is not None

    return private_matches or diplomat_matches or other_diplomat_matches    

#Find all users vehicles (as registration numbers) 
def find_vehicles_registration_numbers(user_id):
    reg_num_rows = fetch("SELECT reg_num FROM vehicles WHERE user_id = %(user_id)s",
                            user_id=user_id)    
    reg_nums = []
    for reg_num_row in reg_num_rows:
        reg_nums.append(reg_num_row["reg_num"])
    return reg_nums

#Filter table by selecting reg.nums 
def parse_selected_registration_numbers(request, user_registration_numbers):
    selected_reg_nums = []
    for k, v in request.args.items():
        if k in user_registration_numbers and v == "on":
            selected_reg_nums.append(k)
    return selected_reg_nums

#Filter table by selected detes
def parse_date_filters(request):
    reportrange = request.args.get("reportrange")

    start_date_filter = None
    end_date_filter = None
    report_range_clause = ''
    if reportrange:
        reportrange = reportrange.split(" - ")
        start_date_filter = reportrange[0]
        end_date_filter = reportrange[1]

        d = timedelta(days=1)
        start_date_filter = datetime.strptime(start_date_filter, "%B %d, %Y")
        end_date_filter = datetime.strptime(end_date_filter, "%B %d, %Y") + d
        return start_date_filter, end_date_filter
    else:
        return None, None

# Query database for username
def find_user(email):
    rows = fetch("SELECT * FROM users WHERE email = %(email)s",
                    email=email)
    return rows

#Query database for rides
def find_rides(user_id, reg_nums, start_date_filter, end_date_filter):
    report_range_clause = ''
    if start_date_filter:
        report_range_clause += ' AND rides.started_at >= %(start_date_filter)s'
    if end_date_filter:
        report_range_clause += ' AND rides.finished_at < %(end_date_filter)s'
        
    if not reg_nums:
        return []
    return fetch(f"""
                    SELECT rides.id,
                        started_at, 
                        finished_at, 
                        odometer_start, 
                        distance, 
                        rides.allowance as allowance, 
                        route, 
                        reg_num, 
                        odometer_start + distance as odometer_finish, 
                        rides.allowance * distance as total 
                    FROM rides 
                    LEFT JOIN vehicles on rides.vehicle_id=vehicles.id 
                    WHERE user_id = %(user_id)s and reg_num in %(reg_nums)s
                    {report_range_clause}
                    ORDER BY finished_at""",
                        user_id=user_id, reg_nums=tuple(reg_nums), start_date_filter=start_date_filter, end_date_filter=end_date_filter)

def calculate_full_deduction(rides):
    full_deduction = 0
    for ride in rides:
        full_deduction = ride['total'] + full_deduction
    return full_deduction

def export_rides_to_csv(rides):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Start of the ride", "Finish", "Registration plate", "Km on start", "Km at finish", 
        "Route explanation", "Allowance (€)", "Distance (km)", "Tax deduction for a ride (€)"])
    for ride in rides:
        csvdata = [format_date_time(ride['started_at']), format_date_time(ride['finished_at']), 
            ride['reg_num'], ride['odometer_start'], ride['odometer_finish'], ride['route'], ride['allowance'], ride['distance'], ride['total']]
        writer.writerow(csvdata)
    return output.getvalue()

# --ENDPOINTS-- #

@app.route('/', methods=["GET"])
def index():
    user_id = session.get("user_id")
    if user_id:
        return redirect("/rides")
    else:
        return render_template("index.html")


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

        # Query database for username
        email = email.strip().lower()
        rows = find_user(email)

        if rows:
            return render_template("register.html", error_message="Account with this email address already exists, please choose another one") 

        user = fetch_one("INSERT INTO users(email, hash) VALUES (%(email)s, %(hash)s) RETURNING id",
                        email=email, hash=generate_password_hash(password))

        session["user_id"] = user["id"]
        return redirect("/vehicles")


@app.route('/login', methods=["GET", "POST"])
def login():

    print('login start')
    session.clear()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if not email:
            return render_template("login.html", error_message="Please provide your email address to log in")
        
        elif not password:
            return render_template("login.html", error_message="Please provide password")

        rows = find_user(email)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return render_template("login.html", error_message="Invalid username and/or password")

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    
    else:
        return render_template("login.html")


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
        vehicle_rows = fetch("SELECT * FROM vehicles WHERE reg_num = %(reg_num)s AND user_id = %(user_id)s",
                          reg_num=reg_num, user_id=user_id)
        if vehicle_rows:
            return render_template("vehicles.html", error_message="Vehicle already exists") 

        execute("INSERT INTO vehicles(user_id, reg_num, allowance, odometer) VALUES (%(user_id)s, %(reg_num)s, %(allowance)s, %(odometer)s)",
                        user_id=user_id, reg_num=reg_num, allowance=allowance, odometer=odometer)
    
    vehicles = fetch("SELECT * FROM vehicles WHERE user_id = %(user_id)s ORDER BY modified_at",
                            user_id=user_id)

    return render_template("vehicles.html", vehicles=vehicles)


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

        vehicle = fetch_one("SELECT id FROM vehicles WHERE reg_num = %(registration_number)s AND user_id=%(user_id)s", registration_number=registration_number, user_id=user_id) 
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

    #Apply reg.num selection filter
    reg_nums = find_vehicles_registration_numbers(user_id)
    
    selected_reg_nums = parse_selected_registration_numbers(request, reg_nums)
    
    if not selected_reg_nums:
        selected_reg_nums = reg_nums
    else:
        for vehicle_row in vehicle_rows:
            if vehicle_row["reg_num"] in selected_reg_nums:
                vehicle_row["selected"] = True

    #Apply period filter         
    start_date_filter, end_date_filter = parse_date_filters(request)
    rides = find_rides(user_id, selected_reg_nums, start_date_filter, end_date_filter)
    for ride in rides:
        start = ride['started_at']
        end = ride['finished_at']
        ride['date'] = start.date()
        ride['start'] = start.time()
        ride['finish'] = end.time()

    amount_of_deduction = calculate_full_deduction(rides)

    return render_template("rides.html", vehicle_rows=vehicle_rows, rides=rides, query_string=request.query_string.decode('utf-8'), amount_of_deduction=amount_of_deduction)


@app.route('/rides/csv_export', methods=["GET", "POST"])
@login_required
def rides_csv_export():
    user_id = session.get("user_id")
    reg_nums = find_vehicles_registration_numbers(user_id)
    selected_reg_nums = parse_selected_registration_numbers(request, reg_nums)
    
    if not selected_reg_nums:
        selected_reg_nums = reg_nums
    start_date_filter, end_date_filter = parse_date_filters(request)

    #find actual rides
    rides = find_rides(user_id, selected_reg_nums, start_date_filter, end_date_filter)

    csv_content = export_rides_to_csv(rides)

    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=table_of_rides.csv"} \
    )



@app.route('/rides/<int:ride_id>/delete', methods=["POST"])
def delete_ride(ride_id):
    delete_ride = execute("DELETE FROM rides WHERE rides.id = %(ride_id)s", ride_id=ride_id)
    return redirect("/rides")

@app.route('/vehicles/<int:vehicle_id>/delete', methods=["POST"])
def delete_vehicle(vehicle_id):
    delete_vehicle = execute("DELETE FROM vehicles WHERE vehicles.id = %(vehicle_id)s", vehicle_id=vehicle_id)
    return redirect("/rides")


@app.route('/logout', methods=["GET"])
def logout():
    session.clear()
    return redirect("/")