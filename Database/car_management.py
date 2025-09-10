from .database import create_connection
import sqlite3
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any
from sqlite3 import IntegrityError
from contextlib import closing

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Bcrypt salt rounds
SALT_ROUNDS = 12

class CarManagement:
    def __init__(self):
        self.conn = create_connection()
        self.create_tables()

    def create_tables(self):
        # This function ensures that the necessary tables exist
        from .database import create_tables
        create_tables()

    #add a new car to the database
    def add_car(self, manufacturer: str, model: str, year: str, mileage: int,
                is_available: bool, min_rental_period: int, max_rental_period: int,
                car_rate: float) -> Optional[int]:
        created_at = datetime.now().isoformat()
        last_update = created_at
        is_available_int = 1 if is_available else 0

        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    INSERT INTO cars (manufacturer, model, year, mileage, is_available,
                                      min_rental_period, max_rental_period, car_rate,
                                      created_at, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (manufacturer, model, year, mileage, is_available_int,
                      min_rental_period, max_rental_period, car_rate,
                      created_at, last_update))
                self.conn.commit()
                return cursor.lastrowid
        except IntegrityError as e:
            logger.error(f"Integrity error while adding car: {e}")
            return None
        except Exception as e:
            logger.error(f"Error while adding car: {e}")
            return None

    #update car details
    def update_car(self, car_id: int, manufacturer: Optional[str] = None,
                   model: Optional[str] = None, year: Optional[str] = None,
                   mileage: Optional[int] = None, is_available: Optional[bool] = None,
                   min_rental_period: Optional[int] = None,
                   max_rental_period: Optional[int] = None,
                   car_rate: Optional[float] = None) -> bool:
        updates = []
        params = []

        # Build the update query dynamically based on provided parameters
        if manufacturer:
            updates.append("manufacturer = ?")
            params.append(manufacturer)
        if model:
            updates.append("model = ?")
            params.append(model)
        if year:
            updates.append("year = ?")
            params.append(year)
        if mileage is not None:
            updates.append("mileage = ?")
            params.append(mileage)
        if is_available is not None:
            updates.append("is_available = ?")
            params.append(1 if is_available else 0)
        if min_rental_period is not None:
            updates.append("min_rental_period = ?")
            params.append(min_rental_period)
        if max_rental_period is not None:
            updates.append("max_rental_period = ?")
            params.append(max_rental_period)
        if car_rate is not None:
            updates.append("car_rate = ?")
            params.append(car_rate)
        if not updates:
            logger.warning("No updates provided for car.")
            return False
        # Always update the last_update timestamp
        updates.append("last_update = ?")
        params.append(datetime.now().isoformat())
        params.append(car_id)
        sql = f"UPDATE cars SET {', '.join(updates)} WHERE car_id = ?"
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute(sql, params)
                self.conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"No car found with ID {car_id} to update.")
                    return False
                return True
        except IntegrityError as e:
            logger.error(f"Integrity error while updating car: {e}")
            return False
        except Exception as e:
            logger.error(f"Error while updating car: {e}")
            return False
    
    # remove a car from the database
    def delete_car(self, car_id: int) -> bool:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute("DELETE FROM cars WHERE car_id = ?", (car_id,))
                self.conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"No car found with ID {car_id} to delete.")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error while deleting car: {e}")
            return False
    
    # get car details by car_id
    def get_car_by_car_id(self, car_id: int) -> Optional[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute("SELECT * FROM cars WHERE car_id = ?", (car_id,))
                row = cursor.fetchone()
                if row:
                    columns = [column[0] for column in cursor.description]
                    return dict(zip(columns, row))
                else:
                    logger.info(f"No car found with ID {car_id}.")
                    return None
        except Exception as e:
            logger.error(f"Error while retrieving car: {e}")
            return None
    
    # list all cars, with optional filter for availability
    def list_cars(self, available_only: bool = False) -> List[Dict[str, Any]]:
        try:
            with closing(self.conn.cursor()) as cursor:
                if available_only:
                    cursor.execute("SELECT * FROM cars WHERE is_available = 1")
                else:
                    cursor.execute("SELECT * FROM cars")
                rows = cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error while listing cars: {e}")
            return []
    
    # set car availability
    def set_car_availability(self, car_id: int, is_available: bool) -> bool:
        is_available_int = 1 if is_available else 0
        try:
            with closing(self.conn.cursor()) as cursor:
                cursor.execute('''
                    UPDATE cars
                    SET is_available = ?, last_update = ?
                    WHERE car_id = ?
                ''', (is_available_int, datetime.now().isoformat(), car_id))
                self.conn.commit()
                if cursor.rowcount == 0:
                    logger.warning(f"No car found with ID {car_id} to update availability.")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error while setting car availability: {e}")
            return False
        
    def __del__(self):
        if self.conn:
            self.conn.close()

