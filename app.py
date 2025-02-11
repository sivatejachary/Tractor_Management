import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "tractor_secret"

# Get the app subpath (needed for Hugging Face Spaces)
APP_SUBPATH = os.getenv("SPACE_ID", "").strip()

# Helper function to generate correct URLs
def fixed_url_for(endpoint, **values):
    """Fixes URL paths for Hugging Face Spaces by adding the correct subpath."""
    if APP_SUBPATH:
        return f"/{APP_SUBPATH}{url_for(endpoint, **values)}"
    return url_for(endpoint, **values)

# Serve static files explicitly
@app.route('/static/<path:filename>')
def static_files(filename):
    return app.send_static_file(filename)

# Database Connection
def get_db_connection():
    conn = sqlite3.connect("tractor.db", check_same_thread=False)  # Allow multi-threaded access
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access to rows
    return conn

# Database Initialization
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS tractor_details (
                        date TEXT NOT NULL,
                        vehicle_name TEXT NOT NULL,
                        vehicle_number TEXT PRIMARY KEY,
                        showroom_cost REAL NOT NULL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS updated_cost (
                        vehicle_number TEXT PRIMARY KEY,
                        updated_cost REAL NOT NULL,
                        FOREIGN KEY(vehicle_number) REFERENCES tractor_details(vehicle_number))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS total_cost (
                        vehicle_number TEXT PRIMARY KEY,
                        showroom_cost REAL NOT NULL,
                        updated_cost REAL DEFAULT 0,
                        total_cost REAL DEFAULT 0,
                        FOREIGN KEY(vehicle_number) REFERENCES tractor_details(vehicle_number))''')

    conn.commit()
    conn.close()

# Home Page
@app.route("/")
def main_page():
    return render_template("main.html", fixed_url_for=fixed_url_for)

# Tractor Data Entry Page
@app.route("/tractor_entry", methods=["GET", "POST"])
def tractor_entry():
    if request.method == "POST":
        date = request.form["date"]
        vehicle_name = request.form["vehicle_name"]
        vehicle_number = request.form["vehicle_number"]
        showroom_cost = float(request.form["showroom_cost"])

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO tractor_details (date, vehicle_name, vehicle_number, showroom_cost) VALUES (?, ?, ?, ?)",
                           (date, vehicle_name, vehicle_number, showroom_cost))

            cursor.execute("INSERT INTO total_cost (vehicle_number, showroom_cost, updated_cost, total_cost) VALUES (?, ?, 0, ?)",
                           (vehicle_number, showroom_cost, showroom_cost))

            conn.commit()
            flash("Tractor details added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Error: Vehicle number already exists!", "error")

        conn.close()
        return redirect(fixed_url_for("tractor_entry"))

    return render_template("index.html", fixed_url_for=fixed_url_for)

# Update Cost Page
@app.route("/update_cost", methods=["GET", "POST"])
def update_cost():
    if request.method == "POST":
        vehicle_number = request.form["vehicle_number"]
        updated_cost = float(request.form["updated_cost"])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT OR REPLACE INTO updated_cost (vehicle_number, updated_cost) VALUES (?, ?)",
                       (vehicle_number, updated_cost))

        cursor.execute("UPDATE total_cost SET updated_cost=?, total_cost=showroom_cost + ? WHERE vehicle_number=?",
                       (updated_cost, updated_cost, vehicle_number))

        conn.commit()
        conn.close()
        flash("Updated cost added successfully!", "success")
        return redirect(fixed_url_for("update_cost"))

    return render_template("update_cost.html", fixed_url_for=fixed_url_for)

# Total Cost Page
@app.route("/total_cost")
def total_cost():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT vehicle_number, showroom_cost, updated_cost, showroom_cost + updated_cost AS total_cost FROM total_cost")
    total_cost_data = cursor.fetchall()

    cursor.execute("SELECT SUM(showroom_cost + updated_cost) FROM total_cost")
    total_cost_sum = cursor.fetchone()[0] or 0

    conn.close()

    return render_template("total_cost.html", total_cost_data=total_cost_data, total_cost=total_cost_sum, fixed_url_for=fixed_url_for)

# Tractor Sales Page
@app.route("/tractor_sales")
def tractor_sales():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT td.date, td.vehicle_name, td.vehicle_number, td.showroom_cost,
               COALESCE(tc.updated_cost, 0) AS updated_cost,
               COALESCE(tc.total_cost, td.showroom_cost) AS total_cost
        FROM tractor_details td
        LEFT JOIN total_cost tc ON td.vehicle_number = tc.vehicle_number
    """)

    sales = cursor.fetchall()
    conn.close()

    return render_template("tractor_sales.html", sales=sales, fixed_url_for=fixed_url_for)

# Delete Sale Record
@app.route('/delete_sale', methods=['POST'])
def delete_sale():
    vehicle_number = request.form['vehicle_number']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete record from all related tables
    cursor.execute("DELETE FROM tractor_details WHERE vehicle_number = ?", (vehicle_number,))
    cursor.execute("DELETE FROM updated_cost WHERE vehicle_number = ?", (vehicle_number,))
    cursor.execute("DELETE FROM total_cost WHERE vehicle_number = ?", (vehicle_number,))

    conn.commit()
    conn.close()

    flash("Record deleted successfully!", "success")
    return redirect(fixed_url_for("tractor_sales"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=7860, debug=False)
