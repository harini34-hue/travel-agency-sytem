from flask import Flask, render_template, request, redirect, url_for
from database import get_db_connection

app = Flask(__name__)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


# =========================================================
# CUSTOMER REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            sql = """
            INSERT INTO users
            (name, email, password, phone)
            VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                sql,
                (name, email, password, phone)
            )

            connection.commit()

            # After registration → Login page
            return redirect(url_for("login"))

        except Exception as e:

            connection.rollback()

            return "Registration Failed: " + str(e)

        finally:

            cursor.close()
            connection.close()

    return render_template("register.html")

# =========================================================
# CUSTOMER LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            sql = """
            SELECT user_id, name
            FROM users
            WHERE email = %s AND password = %s
            """

            cursor.execute(
                sql,
                (email, password)
            )

            user = cursor.fetchone()

            if user:

                # After login → Home page
                return redirect(url_for("home"))

            else:

                return "Invalid email or password."

        except Exception as e:

            return "Login Failed: " + str(e)

        finally:

            cursor.close()
            connection.close()

    return render_template("login.html")

# =========================================================
# DESTINATIONS
# =========================================================

@app.route("/destinations")
def destinations():
    return render_template("destinations.html")


@app.route("/destination/<destination_name>")
def destination_details(destination_name):

    destinations_data = {
        "goa": {
            "name": "Goa",
            "description": "Enjoy beautiful beaches, exciting nightlife, delicious food and relaxing coastal views.",
            "best_time": "November to February",
            "places": "Baga Beach, Calangute Beach, Fort Aguada and Anjuna Beach"
        },

        "manali": {
            "name": "Manali",
            "description": "Experience snow-covered mountains, peaceful valleys and beautiful landscapes.",
            "best_time": "October to February",
            "places": "Solang Valley, Rohtang Pass, Hadimba Temple and Mall Road"
        },

        "kerala": {
            "name": "Kerala",
            "description": "Enjoy peaceful backwaters, lush greenery, beautiful beaches and traditional culture.",
            "best_time": "September to March",
            "places": "Alleppey, Munnar, Kochi and Thekkady"
        },

        "jaipur": {
            "name": "Jaipur",
            "description": "Explore magnificent forts, royal palaces, colorful markets and rich Rajasthani culture.",
            "best_time": "October to March",
            "places": "Amber Fort, City Palace, Hawa Mahal and Jantar Mantar"
        },

        "hyderabad": {
            "name": "Hyderabad",
            "description": "Discover historic monuments, delicious food, beautiful lakes and modern attractions.",
            "best_time": "October to February",
            "places": "Charminar, Golconda Fort, Hussain Sagar and Salar Jung Museum"
        },

        "ooty": {
            "name": "Ooty",
            "description": "Relax in beautiful hills, tea gardens, waterfalls and peaceful natural surroundings.",
            "best_time": "October to June",
            "places": "Ooty Lake, Botanical Garden, Doddabetta Peak and Tea Gardens"
        }
    }

    destination = destinations_data.get(destination_name.lower())

    if not destination:
        return "Destination not found."

    return render_template(
        "destinations.html",
        destination=destination
    )

# =========================================================
# TRAVEL PACKAGES
# =========================================================

@app.route("/packages")
def packages():

    return render_template("packages.html")


# =========================================================
# BOOKING
# =========================================================

@app.route("/booking", methods=["GET", "POST"])
def booking():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        package_name = request.form["package"]
        travel_date = request.form["travel_date"]
        people = int(request.form["people"])

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            # Find user
            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                return "User not found. Please register first."

            user_id = user[0]


            # Find package
            cursor.execute(
                """
                SELECT package_id, price
                FROM travel_packages
                WHERE package_name = %s
                """,
                (package_name,)
            )

            package = cursor.fetchone()

            if not package:
                return "Package not found."

            package_id = package[0]
            price = float(package[1])

            total_amount = price * people


            # Create booking as PENDING
            cursor.execute(
                """
                INSERT INTO bookings
                (
                    user_id,
                    package_id,
                    number_of_people,
                    total_amount,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    package_id,
                    people,
                    total_amount,
                    "Pending"
                )
            )

            connection.commit()

            booking_id = cursor.lastrowid


            # Go directly to payment page
            return redirect(
                url_for(
                    "payment",
                    booking_id=booking_id
                )
            )

        except Exception as e:

            connection.rollback()

            return "Booking Failed: " + str(e)

        finally:

            cursor.close()
            connection.close()


    return render_template("booking.html")

# =========================================================
# MY BOOKINGS
# =========================================================

@app.route("/my-bookings")
@app.route("/my_bookings")
def my_bookings():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                b.booking_id,
                tp.package_name,
                tp.destination,
                tp.duration,
                b.booking_date,
                b.number_of_people,
                b.total_amount,
                b.status
            FROM bookings b
            JOIN travel_packages tp
                ON b.package_id = tp.package_id
            ORDER BY b.booking_id DESC
            """
        )

        bookings = cursor.fetchall()

        return render_template(
            "my_bookings.html",
            bookings=bookings
        )

    except Exception as e:

        return "Error: " + str(e)

    finally:

        cursor.close()
        connection.close()


# =========================================================
# PAYMENT
# =========================================================

@app.route("/payment", methods=["GET", "POST"])
def payment():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # =========================
        # GET → SHOW PAYMENT PAGE
        # =========================
        if request.method == "GET":

            booking_id = request.args.get("booking_id")

            if not booking_id:
                return "Booking ID is missing."

            cursor.execute(
                """
                SELECT
                    b.booking_id,
                    tp.package_name,
                    b.number_of_people,
                    b.total_amount
                FROM bookings b
                JOIN travel_packages tp
                    ON b.package_id = tp.package_id
                WHERE b.booking_id = %s
                """,
                (booking_id,)
            )

            booking = cursor.fetchone()

            if not booking:
                return "Booking not found."

            return render_template(
                "payment.html",
                booking_id=booking[0],
                package_name=booking[1],
                people=booking[2],
                total_amount=booking[3]
            )


        # =========================
        # POST → PROCESS PAYMENT
        # =========================

        booking_id = request.form.get("booking_id")
        payment_method = request.form.get("payment_method")

        if not booking_id:
            return "Booking ID is missing."

        if not payment_method:
            return "Please select a payment method."


        # Get booking amount
        cursor.execute(
            """
            SELECT total_amount
            FROM bookings
            WHERE booking_id = %s
            """,
            (booking_id,)
        )

        booking = cursor.fetchone()

        if not booking:
            return "Booking not found."

        amount = booking[0]


        # Insert payment
        cursor.execute(
            """
            INSERT INTO payments
            (
                booking_id,
                amount,
                payment_method,
                payment_status
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                booking_id,
                amount,
                payment_method,
                "Paid"
            )
        )


        # Confirm booking
        cursor.execute(
            """
            UPDATE bookings
            SET status = 'Confirmed'
            WHERE booking_id = %s
            """,
            (booking_id,)
        )

        connection.commit()


        # After payment → My Bookings
        return redirect(url_for("my_bookings"))


    except Exception as e:

        connection.rollback()

        return "Payment Failed: " + str(e)


    finally:

        cursor.close()
        connection.close()

# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        # Admin login details
        if email == "admin@travelgo.com" and password == "admin123":

            return redirect(url_for("admin_dashboard"))

        else:

            return "Invalid admin email or password."

    return render_template("admin_login.html")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin-dashboard")
def admin_dashboard():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Total users
        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        total_users = cursor.fetchone()[0]

        # Total packages
        cursor.execute(
            "SELECT COUNT(*) FROM travel_packages"
        )

        total_packages = cursor.fetchone()[0]

        # Total bookings
        cursor.execute(
            "SELECT COUNT(*) FROM bookings"
        )

        total_bookings = cursor.fetchone()[0]

        # Total payments
        cursor.execute(
            "SELECT COUNT(*) FROM payments"
        )

        total_payments = cursor.fetchone()[0]

        # Recent bookings
        cursor.execute(
            """
            SELECT
                b.booking_id,
                tp.package_name,
                b.number_of_people,
                b.total_amount,
                b.status
            FROM bookings b
            JOIN travel_packages tp
                ON b.package_id = tp.package_id
            ORDER BY b.booking_id DESC
            """
        )

        recent_bookings = cursor.fetchall()

        return render_template(
            "admin_dashboard.html",
            total_users=total_users,
            total_packages=total_packages,
            total_bookings=total_bookings,
            total_payments=total_payments,
            recent_bookings=recent_bookings
        )

    except Exception as e:

        return "Dashboard Error: " + str(e)

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN - MANAGE USERS
# =========================================================

@app.route("/admin-user")
def admin_user():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                phone,
                role
            FROM users
            ORDER BY user_id DESC
            """
        )

        users = cursor.fetchall()

        return render_template(
            "admin_users.html",
            users=users
        )

    except Exception as e:

        return "Error: " + str(e)

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN - MANAGE PACKAGES
# =========================================================

@app.route("/admin-packages")
def admin_packages():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                package_id,
                package_name,
                destination,
                duration,
                price,
                available_seats
            FROM travel_packages
            ORDER BY package_id DESC
            """
        )

        packages = cursor.fetchall()

        return render_template(
            "admin_packages.html",
            packages=packages
        )

    except Exception as e:

        return "Error: " + str(e)

    finally:

        cursor.close()
        connection.close()


# =========================================================
# ADMIN - MANAGE BOOKINGS
# =========================================================

@app.route("/admin-bookings")
def admin_bookings():

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                b.booking_id,
                u.name,
                u.email,
                tp.package_name,
                tp.destination,
                b.booking_date,
                b.number_of_people,
                b.total_amount,
                b.status
            FROM bookings b

            JOIN users u
                ON b.user_id = u.user_id

            JOIN travel_packages tp
                ON b.package_id = tp.package_id

            ORDER BY b.booking_id DESC
            """
        )

        bookings = cursor.fetchall()

        return render_template(
            "admin_bookings.html",
            bookings=bookings
        )

    except Exception as e:

        return "Error: " + str(e)

    finally:

        cursor.close()
        connection.close()


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)