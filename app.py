import os
from flask import Flask, request, render_template, redirect, session
from lib.database_connection import get_flask_database_connection
from lib.space_repository import *
from lib.space import *
from lib.user_repository import UserRepository
from lib.user import User
from lib.booking_repository import BookingRepository
from lib.booking import Booking
from datetime import datetime, timedelta
from lib.booking_request_repository import BookingRequestRepository
from lib.space_repository import SpaceRepository
from lib.booking_request import BookingRequest


import secrets
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# == Your Routes Here ==

def get_user_details(connection):
    user_repo = UserRepository(connection)
    user_id = session.get('user_id', None)
    user_details = None
    if user_id != None:
        user_details = user_repo.get_user_details(user_id)
    return user_details

@app.route("/")
def set_default_route():
    return redirect("/spaces")

@app.route("/reseed")
def reseed_database():
    connection = get_flask_database_connection(app)
    connection.connect()
    connection.seed("seeds/makers_bnb.sql")
    return redirect("/spaces")

# 'Homepage'
@app.route("/spaces", methods=["GET"])
def get_spaces():
    connection = get_flask_database_connection(app)
    space_repo = SpaceRepository(connection)

    spaces = space_repo.all()

    logged_in = session.get('logged_in', False)
    user_details = get_user_details(connection)

    return render_template("spaces/spaces.html", spaces=spaces, logged_in=logged_in, user=user_details)


@app.route("/spaces/new", methods=['GET'])
def get_new_space():
    connection = get_flask_database_connection(app)

    logged_in = session.get('logged_in', False)
    user_details = get_user_details(connection)

    return render_template('spaces/new.html', logged_in=logged_in, user=user_details)

@app.route("/spaces", methods=['POST'])
def create_space():
    connection = get_flask_database_connection(app)
    space_repository = SpaceRepository(connection)
    booking_repository = BookingRepository(connection)

    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    available_from = request.form['available_from']
    available_to = request.form['available_to']

    user_details = get_user_details(connection)

    space = Space(None, name, description, price, user_details.id)
    space = space_repository.create(space)

    available_from = datetime.strptime(available_from, '%Y-%m-%d')
    available_to = datetime.strptime(available_to, '%Y-%m-%d')
    current_date = available_from
    while current_date <= available_to:
        booking = Booking(None, current_date, True, space.id)
        booking = booking_repository.create(booking)
        current_date += timedelta(days=1)

    return redirect(f"/spaces")


@app.route("/spaces/<id>", methods=["GET"])
def get_space(id):
    connection = get_flask_database_connection(app)
    space_repo = SpaceRepository(connection)
    booking_repo = BookingRepository(connection)
    space = space_repo.find(id)
    bookings = booking_repo.get_by_id(id)

    logged_in = session.get('logged_in', False)
    user_details = get_user_details(connection)

    return render_template("space.html", space=space, bookings=bookings, logged_in=logged_in, user=user_details)


@app.route("/spaces/rent/<booking_id>/<space_id>", methods=["GET"])
def rent_space(booking_id, space_id):
    connection = get_flask_database_connection(app)
    booking_repo = BookingRepository(connection)
    booking_repo.update_availability(booking_id)
    request_repo = BookingRequestRepository(connection)

    user_id = get_user_details(connection)
    user_booking = BookingRequest(None, user_id.id, True, False, booking_id)
    request_repo.create_booking_request(user_booking)

    return redirect(f"/spaces/{space_id}")


@app.route("/signup", methods=["GET"])
def get_user_info():
    return render_template("user_signup.html")


@app.route("/add_user", methods=["POST"])
def add_user_to_db():
    connection = get_flask_database_connection(app)
    user_repository = UserRepository(connection)

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        print("Password doesn't match")
        return render_template("user_signup.html", error = "Passwords do not match")

    user = User(None, username, email, password)
    error = user_repository.create(user)

    if error:
        return render_template("user_signup.html", error = 'Username or Email already exists')

    return redirect("/login")


@app.route("/login", methods=["GET"])
def render_login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():
    connection = get_flask_database_connection(app)
    user_repository = UserRepository(connection)

    username = request.form["user"]
    password = request.form["password"]

    # Check if user is in db and password matches
    user_id = user_repository.verify_user_login(username, password)

    # If the user can't be found:
    if not user_id:
        return render_template("login.html", errors="Incorrect login details")
    
    session['user_id'] = user_id
    session['logged_in'] = True

    return redirect("/spaces")

@app.route("/logout", methods=["GET"])
def logout_user():
    session['user_id'] = None
    session['logged_in'] = False
    return redirect(f"/spaces")

@app.route("/manage_bookings", methods=["GET"])
def get_booking_requests_for_user():
    connection = get_flask_database_connection(app)
    request_repo = BookingRequestRepository(connection)

    user_details = get_user_details(connection)
    bookings = request_repo.get_bookings_by_user(user_details.id)
    logged_in = session.get('logged_in', False)

    return render_template("booking_requests.html", logged_in=logged_in, bookings=bookings, user=user_details)
    
@app.route("/manage_bookings/accept/<booking_requests_id>", methods=["POST"])
def accept_request(booking_requests_id):
    connection = get_flask_database_connection(app)
    request_repo = BookingRequestRepository(connection)

    # booking_requests_id = request.form['booking_requests_id']

    request_repo.accept_booking_request(booking_requests_id)

    return redirect("/manage_bookings")

@app.route("/manage_bookings/reject/<booking_requests_id>", methods=["POST"])
def reject_request(booking_requests_id):
    connection = get_flask_database_connection(app)
    request_repo = BookingRequestRepository(connection)

    # booking_requests_id = request.form['booking_requests_id']

    request_repo.reject_booking_request(booking_requests_id)

    return redirect("/manage_bookings")



if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5001)))
