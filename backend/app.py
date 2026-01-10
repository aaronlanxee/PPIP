from flask import Flask, request, jsonify
import sqlite3, hashlib, random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from helpers import hash_password, get_user_by_email, get_user_by_username, send_otp_email

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

DB_PATH = Path(__file__).parent / "ppip.db"


otp_store = {}

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json

    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm_password = data.get("confirm_password", "")

    # ----- Validation -----
    if not username or not email or not password or not confirm_password:
        return jsonify({"error": "All fields are required"}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    if get_user_by_username(username):
        return jsonify({"error": "Username already exists"}), 400

    if get_user_by_email(email):
        return jsonify({"error": "Email already registered"}), 400

    # ----- Save user -----
    hashed_password = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
        (username, email, hashed_password)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Registration successful"}), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")

    user = get_user_by_username(username)
    if not user:
        return jsonify({"status": "error", "message": "Invalid Username or Password."}), 401

    hashed_password = hash_password(password)
    if user[3] == hashed_password:  # user[3] is password column

        # ---------- Generate OTP ----------
        otp = str(random.randint(100000, 999999))  # 6-digit OTP
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        otp_store[username] = {"otp": otp, "expires_at": expires_at}

        # ---------- Send OTP via Email ----------
        user_email = user[2]  # assuming user[2] is email
        try:
            send_otp_email(user_email, otp)
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to send OTP: {e}"}), 500

        print(otp_store)
        return jsonify({
            "user_id": user[0],
            "status": "success",
            "message": "OTP sent to your email.",
            "username": username  # send username to frontend if needed
        }), 200

    else:
        return jsonify({"status": "error", "message": "Invalid Username or Password."}), 401
    

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.json
    username = data.get("username", "").strip().lower()
    otp = data.get("otp", "").strip()

    print(otp_store)
    print(username)
    if username not in otp_store:
        return jsonify({"status": "error", "message": "No OTP found. Please login first."}), 400

    record = otp_store[username]
    if datetime.now(timezone.utc) > record["expires_at"]:
        del otp_store[username]
        return jsonify({"status": "error", "message": "OTP expired."}), 400

    if otp == record["otp"]:
        del otp_store[username]  # OTP can only be used once
        return jsonify({"status": "success", "message": "OTP verified."}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid OTP."}), 400


@app.route('/api/register_pet', methods=['POST'])
def register_pet():
    type_ = request.form.get("type")
    name = request.form.get("name")
    age = request.form.get("age")
    breed = request.form.get("breed")
    image_file = request.files.get("image")  # <--- image comes here

    image_blob = image_file.read() if image_file else None

    conn = sqlite3.connect("ppip.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pets (user_id, type, name, age, breed, image)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, type_, name, age, breed, image_blob))
    conn.commit()
    conn.close()
    print(name)
    return {"message": "Pet registered successfully"}, 200

@app.route("/api/user/<int:user_id>", methods=["GET"])
def api_get_user(user_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # --- Get user info ---
        cursor.execute(
            "SELECT id, username, email FROM users WHERE id = ?",
            (user_id,)
        )
        user_row = cursor.fetchone()

        if not user_row:
            conn.close()
            return jsonify({"success": False, "message": "User not found"}), 404

        user_data = {
            "id": user_row[0],
            "username": user_row[1],
            "email": user_row[2]
        }

        # --- Get all pets for this user ---
        cursor.execute(
            "SELECT id, type, name, age, breed, image, is_missing FROM pets WHERE user_id = ?",
            (user_id,)
        )
        pet_rows = cursor.fetchall()

        pets = []
        for row in pet_rows:
            pet = {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "age": row[3],
                "breed": row[4],
                "image": row[5].hex() if row[5] else None,  # Convert BLOB to hex string
                "is_missing": row[6]
            }
            pets.append(pet)

        user_data["pets"] = pets  # Add pets array to user_data

        conn.close()
        return jsonify({"success": True, "user": user_data})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/api/pet/<int:pet_id>/mark_missing", methods=["POST"])
def mark_pet_missing(pet_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pets
            SET is_missing = 1
            WHERE id = ?
        """, (pet_id,))

        conn.commit()

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Pet not found"
            }), 404

        conn.close()

        return jsonify({
            "success": True,
            "message": "Pet marked as missing"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# --- Run app ---
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
