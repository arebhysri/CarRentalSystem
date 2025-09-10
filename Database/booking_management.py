from .database import create_connection
from Enum.bookingAction import bookingAction as booking_action
import re
import sqlite3
import logging
from typing import Optional, List, Dict, Any
from sqlite3 import IntegrityError
from contextlib import closing
from datetime import datetime, timedelta
from typing import List
from contextlib import closing

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Bcrypt salt rounds
SALT_ROUNDS = 12

class BookingManagement:
    def __init__(self):
        self.conn = create_connection()
        self.create_tables()

    def create_tables(self):
        # This function ensures that the necessary tables exist
        from .database import create_tables
        create_tables()

    #calculate price
    def calculate_price(self, car_rate: float, start_date: str, end_date: str) -> float:
        date_format = "%Y-%m-%d"
        start = datetime.strptime(start_date, date_format)
        end = datetime.strptime(end_date, date_format)
        delta = end - start
        days = delta.days + 1
        return car_rate * days
    
    # Create a new booking
    def create_booking(self, car_id: int, user_id: int, start_date: str, end_date: str, car_rate) -> Optional[int]:
        rental_status = booking_action.PENDING
        price = self.calculate_price(car_rate, start_date, end_date)
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    INSERT INTO bookings (car_id, user_id, start_date, end_date, rental_status, price)
                    VALUES (?, ?, ?, ?, ?,?)
                ''', (car_id, user_id, start_date, end_date, rental_status,price))
                self.conn.commit()
                return cursor.lastrowid
        except IntegrityError as e:
            logger.error(f"Integrity error while creating booking: {e}")
            return None
        except Exception as e:
            logger.error(f"Error while creating booking: {e}")
            return None

    # Update booking status
    def update_booking_status(self, booking_id: int, rental_status: str) -> bool:
        if rental_status not in [booking_action.PENDING, booking_action.APPROVE, booking_action.REJECT, booking_action.COMPLETED]:
            logger.error("Invalid rental status provided.")
            return False
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    UPDATE bookings
                    SET rental_status = ?
                    WHERE booking_id = ?
                ''', (rental_status, booking_id))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating booking status: {e}")
            return False

    # Get booking details by booking_id
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT * FROM bookings WHERE booking_id = ?
                ''', (booking_id,))
                row = cursor.fetchone()
                if row:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Error retrieving booking by ID: {e}")
            return None

    # Get all bookings
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT bookings.booking_id,bookings.car_id,bookings.user_id, cars.model,users.name,bookings.start_date,bookings.end_date, bookings.price,bookings.rental_status FROM bookings inner join users on bookings.user_id=users.user_id inner join cars on bookings.car_id=cars.car_id')
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving all bookings: {e}")
            return []
        
    # Delete booking by booking_id
    def delete_booking(self, booking_id: int) -> bool:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting booking: {e}")
            return False
        
    # Get bookings by user_id
    def get_bookings_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT * FROM bookings WHERE user_id = ?', (user_id,))
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving bookings by user ID: {e}")
            return []
        
    # Get bookings by car_id
    def get_bookings_by_car(self, car_id: int) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT * FROM bookings WHERE car_id = ?', (car_id,))
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving bookings by car ID: {e}")
            return []
        
    # Set booking price
    def set_booking_price(self, booking_id: int, price: float) -> bool:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    UPDATE bookings
                    SET price = ?
                    WHERE booking_id = ?
                ''', (price, booking_id))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error setting booking price: {e}")
            return False
        
    # Get bookings by rental status
    def get_bookings_by_status(self, rental_status: str) -> List[Dict[str, Any]]:
        if rental_status not in [booking_action.PENDING, booking_action.APPROVE, booking_action.REJECT, booking_action.COMPLETED]:
            logger.error("Invalid rental status provided.")
            return []
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('SELECT * FROM bookings WHERE rental_status = ?', (rental_status,))
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving bookings by status: {e}")
            return []
        
    # Get bookings within a date range
    def get_bookings_in_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT * FROM bookings
                    WHERE (start_date BETWEEN ? AND ?) OR (end_date BETWEEN ? AND ?)
                ''', (start_date, end_date, start_date, end_date))
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error retrieving bookings in date range: {e}")
            return []
    

    def get_booked_dates(self, car_id: int) -> List[datetime.date]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    SELECT start_date, end_date FROM bookings
                    WHERE car_id = ? AND rental_status IN (?, ?)
                ''', (car_id, booking_action.PENDING, booking_action.APPROVE))
                rows = cursor.fetchall()

            booked = []
            for start, end in rows:
                start_dt = datetime.strptime(start, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end, "%Y-%m-%d").date()
                booked.extend([
                    start_dt + timedelta(days=i)
                    for i in range((end_dt - start_dt).days + 1)
                ])
            return booked

        except Exception as e:
            logger.error(f"Error fetching booked dates for car {car_id}: {e}")
            return []

    # Close the database connection
    def close_connection(self):
        if self.conn:
            self.conn.close()
            return False

    def __del__(self):
        if self.conn:
            self.conn.close()