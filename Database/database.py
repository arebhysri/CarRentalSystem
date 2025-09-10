import sqlite3

# Establish a connection to the SQLite database
def create_connection():
    return sqlite3.connect('car_rental.db', check_same_thread=False, timeout=30)

# Create tables if they do not exist
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Create users tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'customer')) NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT NULL,
            last_login TEXT
        )
    ''')
    
    # Create cars table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            car_id INTEGER PRIMARY KEY AUTOINCREMENT,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            year TEXT NOT NULL,
            mileage INTEGER NOT NULL,
            is_available INTEGER CHECK(is_available IN (0, 1)) NOT NULL,
            min_rental_period INTEGER NOT NULL,
            max_rental_period INTEGER NOT NULL,
            car_rate REAL NOT NULL,
            created_at TEXT NOT NULL,
            last_update TEXT NOT NULL
        )
    ''')
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY,
            car_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            rental_status TEXT NOT NULL CHECK(rental_status IN ('pending', 'approved', 'rejected', 'completed')),
            price REAL NULL,
            FOREIGN KEY(car_id) REFERENCES cars(car_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()