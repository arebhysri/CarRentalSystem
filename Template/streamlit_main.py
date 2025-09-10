import streamlit as st
# filepath: c:\Users\Administrator\Documents\GitHub\MSE800_ArebhyG\CAR_RENTAL_SYSTEM_A1\CarRentalSystem\Template\streamlit_main.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# ...existing code...
from Database.user_management import UserManagement
from Database.car_management import CarManagement
from Database.booking_management import BookingManagement
from Models.user import User
from Models.car import Car
from Models.booking import Booking
from datetime import datetime, timedelta
import logging
from typing import Optional, List, Dict, Any
from contextlib import closing
from sqlite3 import IntegrityError
from Enum.usre_role import user_role
from Enum.bookingAction import bookingAction as booking_action
from Enum.actionType import AdminAction

st.markdown("""
    <style>
    .stApp {
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .tooltip-container {
                position: relative;
                display: inline-block;
            }
            .main {
                max-width: 100%;
                padding-left: 2rem;
                padding-right: 2rem;
            }
    </style>
""", unsafe_allow_html=True)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Session state keys
SESSION_USER_KEY = 'user'
SESSION_ROLE_KEY = 'role'
SESSION_LOGIN_TIME_KEY = 'login_time'
SESSION_TIMEOUT_MINUTES = 30

# Initialize management classes
user_mgmt = UserManagement()
car_mgmt = CarManagement()
booking_mgmt = BookingManagement()

# Function to check session timeout
def is_session_active() -> bool:
    if SESSION_LOGIN_TIME_KEY in st.session_state:
        login_time = st.session_state[SESSION_LOGIN_TIME_KEY]
        if datetime.now() - login_time < timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            return True
    return False

# Function to reset session
def reset_session():
    for key in [SESSION_USER_KEY, SESSION_ROLE_KEY, SESSION_LOGIN_TIME_KEY]:
        if key in st.session_state:
            del st.session_state[key]

# Function to handle user login
def login_user(email: str, password: str) -> bool:
    user_data = user_mgmt.authenticate_user(email, password)
    if user_data:
        # Provide dummy values if missing
        if 'password' not in user_data:
            user_data['password'] = ''  # or None
        if 'created_at' not in user_data:
            user_data['created_at'] = ''
        st.session_state[SESSION_USER_KEY] = User(**user_data)
        st.session_state[SESSION_ROLE_KEY] = user_data['role']
        st.session_state[SESSION_LOGIN_TIME_KEY] = datetime.now()
        return True
    return False

# Function to handle user logout
def logout_user():
    reset_session()
    st.success("Logged out successfully.")
    st.rerun()

# Function to display login form
def display_login_form():
    st.title("Car Rental System - Login")

    # Input fields
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    # Define columns before using them
    col1, col2 = st.columns(2)

    # Login button in first column
    with col1:
        if st.button("Login"):
            if login_user(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    # Register button in second column
    with col2:
        if st.button("Register"):
            st.session_state['show_register'] = True
            st.rerun() 

# Function to display registration form
def display_registration_form():
    st.title("Car Rental System - Register")
    name = st.text_input("Name")
    role = st.selectbox("Role", [user_role.ADMIN, user_role.CUSTOMER])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        user_id = user_mgmt.register_user(name, role, email, password)
        if user_id:
            st.success("Registration successful! Please log in.")
            st.session_state['show_register'] = False
            st.rerun()
        else:
            st.error("Registration failed. Please check your details and try again.")
    if st.button("Back to Login"):
        st.session_state['show_register'] = False
        st.rerun()

# Function to display admin dashboard
def display_admin_dashboard():
    st.title("Admin Dashboard")
    col1, col2 = st.columns([4, 1])  # Adjust ratio as needed

    with col1:
        st.write(f"Welcome, {st.session_state[SESSION_USER_KEY].name}!")

    with col2:
        if st.button("Logout"):
            logout_user()
    st.subheader("Car Management")
    if st.button("Add New Car"):
        st.session_state['show_add_car'] = True
        st.rerun()
    cars = car_mgmt.list_cars()
    if cars:
        st.subheader("Available Cars")

        # Table header
        header_cols = st.columns([1, 2, 2, 1, 1, 1, 1])
        header_labels = ["ID", "Manufacturer", "Model (Year)", "Mileage", "Available", "Rate", "Actions"]
        for col, label in zip(header_cols, header_labels):
            col.markdown(f"**{label}**")

        # Table rows
        for car_data in cars:
            if 'is_Available' in car_data:
                car_data['is_available'] = car_data.pop('is_Available')
            car = Car(**car_data)

            row = st.columns([1, 2, 2, 1, 1, 1, 1])
            row[0].write(car.car_id)
            row[1].write(car._manufacturer)
            row[2].write(f"{car._model} ({car.year})")
            row[3].write(car.get_mileage())
            row[4].write("Yes" if car.is_available else "No")
            row[5].write(f"${car.get_rate()}/day")

            # Inline buttons
            with row[6]:
                col_edit, col_delete = st.columns([1, 1])
                if col_edit.button("✏️", key=f"edit_{car.car_id}", help="Edit"):
                    st.session_state['edit_car_id'] = car.car_id
                    st.session_state['show_edit_car'] = True
                    st.rerun()

                if col_delete.button("🗑️", key=f"delete_{car.car_id}", help="Delete"):
                    if car_mgmt.delete_car(car.car_id):
                        st.success(f"Car {car.car_id} deleted successfully.")
                    else:
                        st.error(f"Failed to delete Car {car.car_id}.")
                    st.rerun()
    else:
        st.info("No cars available. Please add new cars.")
    st.subheader("Booking Management")
    
    bookings = booking_mgmt.get_all_bookings()
    if bookings:
        # Table header
        header_cols = st.columns([1, 1, 1, 2, 2, 1, 2])
        headers = ["#", "Model", "User Name", "Start Date", "End Date", "Price","Rental status", "Actions"]
        for col, label in zip(header_cols, headers):
            col.markdown(f"**{label}**")

        # Table rows
        for booking_data in bookings:
            booking = Booking(**booking_data)

            row = st.columns([1, 1, 1, 1.5, 1.5, 1, 2, 2])
            row[0].write(booking.booking_id)
            row[1].write(booking.model)
            row[2].write(booking.name)
            row[3].write(booking.start_date)
            row[4].write(booking.end_date)
            row[5].write(booking._price)
            row[6].write(booking._rental_status)

            # Action buttons only for pending bookings
            if booking._rental_status == booking_action.PENDING:
                with row[7]:
                    col_approve, col_reject = st.columns([1, 1])
                    approve_key = f"approve_{booking.booking_id}"
                    reject_key = f"reject_{booking.booking_id}"
                
                if col_approve.button("✅", key=approve_key, help="Approve"):
                    if booking_mgmt.update_booking_status(booking.booking_id, booking_action.APPROVE):
                        st.success(f"Booking {booking.booking_id} approved.")
                    else:
                        st.error(f"Failed to approve Booking {booking.booking_id}.")
                    st.rerun()

                if col_reject.button("❌", key=reject_key, help="Reject"):
                    if booking_mgmt.update_booking_status(booking.booking_id, booking_action.REJECT):
                        st.success(f"Booking {booking.booking_id} rejected.")
                    else:
                        st.error(f"Failed to reject Booking {booking.booking_id}.")
                    st.rerun()
    else:
        st.info("No bookings available.")

# Function to display add car form
def display_add_car_form():
    st.title("Add New Car")
    manufacturer = st.text_input("Manufacturer")
    model = st.text_input("Model")
    year = st.text_input("Year")
    mileage = st.number_input("Mileage", min_value=0)
    is_Available = st.checkbox("Is Available", value=True)
    min_rental_period = st.number_input("Minimum Rental Period (days)", min_value=1)
    max_rental_period = st.number_input("Maximum Rental Period (days)", min_value=1)
    car_rate = st.number_input("Car Rate ($/day)", min_value=0.0, format="%.2f")
    if st.button("Add Car"):
        car_id = car_mgmt.add_car(manufacturer, model, year, mileage, is_Available, min_rental_period, max_rental_period, car_rate)
        if car_id:
            st.success(f"Car added successfully with ID {car_id}.")
            st.session_state['show_add_car'] = False
            st.rerun()
        else:
            st.error("Failed to add car. Please check the details and try again.")
    if st.button("Back to Dashboard"):
        st.session_state['show_add_car'] = False
        st.rerun()

# Function to display edit car form
def display_edit_car_form(car_id: int):
    car_data = car_mgmt.get_car_by_car_id(car_id)
    if not car_data:
        st.error("Car not found.")
        st.session_state['show_edit_car'] = False
        st.rerun()
    car = Car(**car_data)
    st.title(f"Edit Car ID {car.car_id}")
    manufacturer = st.text_input("Manufacturer", value=car._manufacturer)
    model = st.text_input("Model", value=car._model)
    year = st.text_input("Year", value=car.year)
    mileage = st.number_input("Mileage", min_value=0, value=car.get_mileage())
    is_available = st.checkbox("Is Available", value=car.is_available)
    min_rental_period = st.number_input("Minimum Rental Period (days)", min_value=1, value=car._min_rental_period)
    max_rental_period = st.number_input("Maximum Rental Period (days)", min_value=1, value=car._max_rental_period)
    car_rate = st.number_input("Car Rate ($/day)", min_value=0.0, format="%.2f", value=car.get_rate())
    if st.button("Update Car"):
        if car_mgmt.update_car(car.car_id, manufacturer, model, year, mileage, is_available, min_rental_period, max_rental_period, car_rate):
            st.success(f"Car ID {car.car_id} updated successfully.")
            st.session_state['show_edit_car'] = False
            del st.session_state['edit_car_id']
            st.rerun()
        else:
            st.error("Failed to update car. Please check the details and try again.")
    if st.button("Back to Dashboard"):
        st.session_state['show_edit_car'] = False
        del st.session_state['edit_car_id']
        st.rerun()

# Function to display customer dashboard
def display_customer_dashboard():
    st.title("Customer Dashboard")
    st.write(f"Welcome, {st.session_state[SESSION_USER_KEY].name}!")
    if st.button("Logout"):
        logout_user()
    st.subheader("Available Cars")
    cars = car_mgmt.list_cars()
    if cars:
        for car_data in cars:
            if 'is_available' in car_data:
                car_data['is_available'] = car_data.pop('is_available')
            car = Car(**car_data)
            st.write(f"ID: {car.car_id}, {car._manufacturer} {car._model} ({car.year}), Mileage: {car.get_mileage()}, Available: {'Yes' if car.is_available else 'No'}, Rate: ${car.get_rate()}/day")
            if car.is_available:
                if st.button(f"Book Car {car.car_id}"):
                    st.session_state['book_car_id'] = car.car_id
                    st.session_state['show_book_car'] = True
                    st.rerun()
    else:
        st.info("No cars available at the moment.")
    st.subheader("My Bookings")
    bookings = booking_mgmt.get_all_bookings()
    user_bookings = [b for b in bookings if b['user_id'] == st.session_state[SESSION_USER_KEY].user_id]
    if user_bookings:
        for booking_data in user_bookings:
            booking = Booking(**booking_data)
            st.write(f"Booking ID: {booking.booking_id}, Car ID: {booking.car_id}, Status: {booking._rental_status}, From: {booking.start_date}, To: {booking.end_date}")
    else:
        st.info("You have no bookings.")

# Function to display book car form
def display_book_car_form(car_id: int):
    car_data = car_mgmt.get_car_by_car_id(car_id)
    if not car_data:
        st.error("Car not found.")
        st.session_state['show_book_car'] = False
        st.rerun()

    st.write(f"You can book this car for up to **{car_data['max_rental_period']} days**, if available.")

    if 'is_Available' in car_data:
        car_data['is_available'] = car_data.pop('is_Available')

    car = Car(**car_data)
    st.title(f"Book Car ID {car.car_id} - {car._manufacturer} {car._model}")

    # Fetch booked dates
    booked_dates = booking_mgmt.get_booked_dates(car.car_id)
    today = datetime.today().date()
    max_date = today + timedelta(days=90)

    # Generate available dates
    available_dates = [
        today + timedelta(days=i)
        for i in range((max_date - today).days + 1)
        if (today + timedelta(days=i)) not in booked_dates
    ]

    if not available_dates:
        st.warning("No available dates for this car in the next 90 days.")
        return

    # Select start and end dates from available options
    start_date = st.selectbox("Start Date", available_dates)
    end_options = [d for d in available_dates if d > start_date and (d - start_date).days <= car_data['max_rental_period']]
    end_date = st.selectbox("End Date", end_options)

    if st.button("Book Now", key="book_now_btn"):
        if start_date >= end_date:
            st.error("End date must be after start date.")
        elif any(d in booked_dates for d in [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]):
            st.error("Selected range overlaps with existing bookings.")
        elif (end_date - start_date).days > car_data['max_rental_period']:
            st.error(f"Booking period exceeds maximum of {car_data['max_rental_period']} days.")
        else:
            booking_id = booking_mgmt.create_booking(
                car_id=car.car_id,
                user_id=st.session_state[SESSION_USER_KEY].user_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                car_rate=car.get_rate()
            )
            if booking_id:
                st.success(f"Booking created successfully with ID {booking_id}. Awaiting approval.")
                st.session_state['show_book_car'] = False
                del st.session_state['book_car_id']
                st.rerun()
            else:
                st.error("Failed to create booking. Please try again.")

    if st.button("Back to Dashboard", key="back_dashboard_booking"):
        st.session_state['show_book_car'] = False
        del st.session_state['book_car_id']
        st.rerun()


# Main function to control the app flow
def main():
    if SESSION_USER_KEY not in st.session_state or not is_session_active():
        reset_session()
        if 'show_register' not in st.session_state:
            st.session_state['show_register'] = False
        if st.session_state['show_register']:
            display_registration_form()
        else:
            display_login_form()
    else:
        st.session_state[SESSION_LOGIN_TIME_KEY] = datetime.now()  # Refresh session time
        if st.session_state[SESSION_ROLE_KEY] == user_role.ADMIN:
            if 'show_add_car' in st.session_state and st.session_state['show_add_car']:
                display_add_car_form()
            elif 'show_edit_car' in st.session_state and st.session_state['show_edit_car'] and 'edit_car_id' in st.session_state:
                display_edit_car_form(st.session_state['edit_car_id'])
            else:
                display_admin_dashboard()
        elif st.session_state[SESSION_ROLE_KEY] == user_role.CUSTOMER:
            if 'show_book_car' in st.session_state and st.session_state['show_book_car'] and 'book_car_id' in st.session_state:
                display_book_car_form(st.session_state['book_car_id'])
            else:
                display_customer_dashboard()
        else:
            st.error("Invalid user role. Please contact support.")
            reset_session()
            st.rerun()

if __name__ == "__main__":
    main()
# End of file