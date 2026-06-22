import requests
import mysql.connector
from datetime import datetime
import json
import re
import logging

API_KEY = "ddcdbb179c3d4b3ebf8101735261206"
baseurl = "http://api.weatherapi.com/v1/current.json"
failed_validation_count = 0

logging.basicConfig(
    filename="weather_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database connection 
def connect_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Jabeen@57",
            database="weather_db"
        )
        logging.info("Database connected successfully")
        return conn
    except mysql.connector.Error as e:
        logging.error(f"Database connection failed: {e}")
        print("DB connected error:", e)
        return None

# Weather API call
def get_weather(city):
    try:
        URL = f"{baseurl}?key={API_KEY}&q={city}"
        responses = requests.get(URL)
        data = responses.json()
        if responses.status_code != 200:
            print("API Error ", data)
            return None
        return data
    except Exception as e:
        print("API Error ", e)
        return None

# Validation Functions
def validate_city(city):
    return bool(re.fullmatch(r"^[A-Za-z\s\.]+$", city))

def validate_country(country):
    return bool(re.fullmatch(r"^[A-Za-z\s]+$", country))

def validate_temperature(temp):
    return bool(re.fullmatch(r"^-?\d+(\.\d+)?$", str(temp)))

def validate_humidity(humidity):
    return bool(re.fullmatch(r"^\d+(\.\d+)?$", str(humidity)))

def validate_wind_speed(speed):
    return bool(re.fullmatch(r"^\d+(\.\d+)?$", str(speed)))

def validate_condition(condition):
    return bool(re.fullmatch(r"^[A-Za-z\s]+$", condition))

def validate_weather_data(data):
    location = data["location"]
    current = data["current"]

    city = location["name"]
    country = location["country"]
    temperature = current["temp_c"]
    humidity = current["humidity"]
    wind_speed = current["wind_kph"]
    condition = current["condition"]["text"]

    print("\n----- VALIDATION REPORT -----")
    print("City Validation        :", "Passed" if validate_city(city) else "Failed")
    print("Country Validation     :", "Passed" if validate_country(country) else "Failed")
    print("Temperature Validation :", "Passed" if validate_temperature(temperature) else "Failed")
    print("Humidity Validation    :", "Passed" if validate_humidity(humidity) else "Failed")
    print("Wind Speed Validation  :", "Passed" if validate_wind_speed(wind_speed) else "Failed")
    print("Condition Validation   :", "Passed" if validate_condition(condition) else "Failed")

    return (
        validate_city(city)
        and validate_country(country)
        and validate_temperature(temperature)
        and validate_humidity(humidity)
        and validate_wind_speed(wind_speed)
        and validate_condition(condition)
    )

# Display weather
def display_weather(data):
    location = data["location"]
    current = data["current"]
    print("\n---------------------------------")
    print("weather report")
    print("-------------------------------------------------------")
    print("city:", location["name"])
    print("country:", location["country"])
    print("Temperature:", current["temp_c"], "c")
    print("Humidity:", current["humidity"], "%")
    print("wind speed:", current["wind_kph"], "km/h")
    print("condition:", current["condition"]["text"])

# Insert into db 
def save_weather(conn, data):
    cursor = None
    try:
        cursor = conn.cursor()
        global failed_validation_count

        is_valid = validate_weather_data(data)
        location = data["location"]
        current = data["current"]
        now = datetime.now()

        if is_valid:
            status = "PASSED"
            print("Validation Passed")
            logging.info(f"Validation PASSED for {location['name']}")
        else:
            status = "FAILED"
            failed_validation_count += 1
            print("Validation Failed - Not Saved")
            logging.warning(f"Validation FAILED for {location['name']}")
            return

        log_validation(location["name"], "PASSED")

        sql = """
        INSERT INTO weather_reports
        (city, country, temperature, humidity,
         wind_speed, condition_desc,
         search_date, search_time,
         raw_response, validation_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            location["name"],
            location["country"],
            current["temp_c"],
            current["humidity"],
            current["wind_kph"],
            current["condition"]["text"],
            now.date(),
            now.time(),
            json.dumps(data),
            "PASSED"
        )

        cursor.execute(sql, values)
        conn.commit()
        print("Weather saved to database")

    except Exception as e:
        print("DB Insert Error:", e)
    finally:
        if cursor:
            cursor.close()

def log_validation(city, status):
    now = datetime.now()
    with open("validation_log.txt", "a") as file:
        file.write(
            f"{now.strftime('%d-%m-%Y %H:%M:%S')}\n"
            f"{city}\n"
            f"{status}\n\n"
        )

# ---------------- VIEW HISTORY ----------------
def view_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, city, temperature, condition_desc, search_date, search_time FROM weather_reports")
    records = cursor.fetchall()

    print("\n--- WEATHER HISTORY ---")
    for row in records:
        print(row)
    cursor.close()

# View last weather report
def view_last_weather(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        query = """
        SELECT id, city, country, temperature, humidity, wind_speed, condition_desc, search_date, search_time
        FROM weather_reports
        ORDER BY id DESC
        LIMIT 1
        """
        cursor.execute(query)
        record = cursor.fetchone()
        if record:
            print("\n----- LAST WEATHER SEARCH -----")
            print("City        :", record[1])
            print("Country     :", record[2])
            print("Temperature :", record[3], "°C")
            print("Humidity    :", record[4], "%")
            print("Wind Speed  :", record[5], "km/h")
            print("Condition   :", record[6])
            print("Date        :", record[7])
            print("Time        :", record[8])
        else:
            print("No weather history found")
    except Exception as e:
        print("Error fetching last search:", e)
    finally:
        if cursor:
            cursor.close()

# Hottest city 
def hottest_city(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        query = """
        SELECT city, temperature
        FROM weather_reports
        ORDER BY temperature DESC
        LIMIT 1
        """
        cursor.execute(query)
        record = cursor.fetchone()

        if record:
            print("\n🔥 HOTTEST CITY 🔥")
            print("City        :", record[0])
            print("Temperature :", record[1], "°C")
        else:
            print("No data found")
    except Exception as e:
        print("Error:", e)
    finally:
        if cursor:
            cursor.close()

# Coldest city
def coldest_city(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        # Fixed query column order explicitly to match indices perfectly
        query = """
        SELECT id, city, country, temperature, humidity, wind_speed, condition_desc, search_date, search_time
        FROM weather_reports
        ORDER BY temperature ASC
        LIMIT 1
        """
        cursor.execute(query)
        record = cursor.fetchone()
        if record:
            print("\n----- COLDEST CITY SEARCH -----")
            print("City        :", record[1])
            print("Country     :", record[2])
            print("Temperature :", record[3], "°C")
            print("Humidity    :", record[4], "%")
            print("Wind Speed  :", record[5], "km/h")
            print("Condition   :", record[6])
            print("Date        :", record[7])
            print("Time        :", record[8])
        else:
            print("No weather history found")
    except Exception as e:
        print("Error fetching coldest city:", e)
    finally:
        if cursor:
            cursor.close()

def weather_search_counter(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM weather_reports"
        cursor.execute(query)
        result = cursor.fetchone()
        print("\n---- WEATHER SEARCH COUNTER ----")
        print("Total Searches Logged:", result[0])
        cursor.close()
    except Exception as e:
        print(e)

def delete_weather_history(conn):
    try:
        cursor = conn.cursor()
        weather_id = int(input("Enter Weather Record ID to delete: "))
        query = "DELETE FROM weather_reports WHERE id = %s"
        cursor.execute(query, (weather_id,))
        conn.commit()

        if cursor.rowcount > 0:
            print("Record deleted successfully.")
        else:
            print("No record found with that ID.")
        cursor.close()
    except Exception as e:
        print("Error:", e)

def export_weather_history(conn):
    try:
        cursor = conn.cursor()
        query = "SELECT city, temperature, condition_desc FROM weather_reports"
        cursor.execute(query)
        records = cursor.fetchall()

        with open("weather_history.txt", "w") as file:
            for record in records:
                file.write(f"{record[0]} | {record[1]}°C | {record[2]}\n")

        print("Weather history exported successfully to weather_history.txt")
        cursor.close()
    except Exception as e:
        print("Error exporting history:", e)

def weather_statistics(conn):
    try:
        cursor = conn.cursor()
        query = """
        SELECT
            COUNT(*),
            MAX(temperature),
            MIN(temperature),
            AVG(temperature)
        FROM weather_reports
        """
        cursor.execute(query)
        stats = cursor.fetchone()
        print("\n===== WEATHER STATISTICS =====")
        print("Total Searches      :", stats[0])
        print("Highest Temperature :", stats[1], "°C")
        print("Lowest Temperature  :", stats[2], "°C")
        print("Average Temperature :", round(stats[3], 2), "°C")
        cursor.close()
    except Exception as e:
        print("Error:", e)

def show_failed_validations():
    global failed_validation_count
    print("\n----- FAILED VALIDATIONS -----")
    print("Total Failed Validations :", failed_validation_count)

# ---------------- MENU ----------------
def menu():
    conn = connect_db()
    if not conn:
        return

    while True:
        print("\n====== WEATHER APP ======")
        print("1. Check Weather")
        print("2. View History")
        print("3. View Last Weather Search")
        print("4. Hottest City")
        print("5. Coldest City")
        print("6. Weather Search Counter")
        print("7. Delete Weather Reports")
        print("8. Export Weather History")
        print("9. Statistics")
        print("10. Failed Validation Count")
        print("11. Exit")
        
        choice = input("Enter choice: ")
        if choice == "1":
            cities = input("Enter cities (comma separated): ").split(",")
            for city in cities:
                city = city.strip()  
                data = get_weather(city)
                if data:
                    display_weather(data)
                    save_weather(conn, data)
                else:
                    print(f"Weather not found for {city}")
        elif choice == "2":
            view_history(conn)
        elif choice == "3":
            view_last_weather(conn)
        elif choice == "4":
            hottest_city(conn)
        elif choice == "5":
            coldest_city(conn)
        elif choice == "6":
            weather_search_counter(conn)
        elif choice == "7":
            delete_weather_history(conn)
        elif choice == "8":
            export_weather_history(conn)
        elif choice == "9":
            weather_statistics(conn)
        elif choice == "10":
            show_failed_validations()
        elif choice == "11":
            print("Exiting...")
            conn.close()
            break
        else:
            print("Invalid choice")

if __name__ == "__main__":
    menu()