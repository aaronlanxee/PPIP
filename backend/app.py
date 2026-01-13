from flask import Flask, request, jsonify
import sqlite3, hashlib, random, json, base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
from helpers import hash_password, get_user_by_email, get_user_by_username, send_otp_email, send_email

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
    """
    Expects JSON data in POST body:
    {
        "missing_location": [lat, lng]  # a list of two floats
    }
    """
    try:
        data = request.get_json()
        if not data or "missing_location" not in data:
            return jsonify({
                "success": False,
                "message": "Missing 'missing_location' in request"
            }), 400

        missing_location = data["missing_location"]

        # Validate it's a list of 2 numbers
        if (not isinstance(missing_location, list) 
            or len(missing_location) != 2 
            or not all(isinstance(x, (int, float)) for x in missing_location)):
            return jsonify({
                "success": False,
                "message": "'missing_location' must be a list of 2 numbers [lat, lng]"
            }), 400

        # Convert to JSON string to store in DB
        missing_location_json = json.dumps(missing_location)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pets
            SET is_missing = 1,
                missing_location = ?
            WHERE id = ?
        """, (missing_location_json, pet_id))

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
            "message": f"Pet {pet_id} marked as missing",
            "missing_location": missing_location
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    
@app.route("/api/missing_pets", methods=["GET"])
def load_missing_pets():
    """
    Returns a list of all pets that are marked as missing,
    including their last known missing location, owner's email, and image.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Fetch pets where is_missing = 1, including owner's email and image blob
        cursor.execute("""
            SELECT pets.id, pets.type, pets.name, pets.age, pets.breed, pets.missing_location, pets.image, users.email
            FROM pets
            JOIN users ON pets.user_id = users.id
            WHERE pets.is_missing = 1
        """)
        rows = cursor.fetchall()
        conn.close()

        missing_pets = []
        for row in rows:
            # Parse missing_location JSON string back to list
            try:
                location = json.loads(row[5]) if row[5] else None
            except Exception:
                location = None

            # Convert image blob to base64 string (if present)
            image_blob = row[6]
            image_base64 = None
            if image_blob:
                image_base64 = base64.b64encode(image_blob).decode('utf-8')

            pet_data = {
                "id": row[0],
                "type": row[1],
                "name": row[2],
                "age": row[3],
                "breed": row[4],
                "missing_location": location,
                "image": image_base64,       # <-- base64 string
                "owner_email": row[7]        # owner's email from users table
            }
            missing_pets.append(pet_data)

        return jsonify({
            "success": True,
            "missing_pets": missing_pets
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/api/pet/<int:pet_id>/found", methods=["POST"])
def mark_pet_found(pet_id):
    """
    Mark a pet as found by setting is_missing = 0 and clearing missing_location.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pets
            SET is_missing = 0,
                missing_location = NULL
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
            "message": f"Pet {pet_id} has been marked as found"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/check_image", methods=["POST"])
def check_image():
    """
    Check uploaded image against all images in pet_images table.
    If an exact match is found, return the pet_id.
    """
    try:
        if "image" not in request.files:
            return jsonify({
                "success": False,
                "message": "No image file provided"
            }), 400

        uploaded_file = request.files["image"]
        uploaded_bytes = uploaded_file.read()

        if not uploaded_bytes:
            return jsonify({
                "success": False,
                "message": "Empty image file"
            }), 400

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, image
            FROM pets
        """)

        rows = cursor.fetchall()
        conn.close()

        # Compare uploaded image with each stored image
        for pet_id, stored_blob in rows:
            if stored_blob == uploaded_bytes:
                return jsonify({
                    "success": True,
                    "match": True,
                    "pet_id": pet_id
                }), 200

        # No match found
        return jsonify({
            "success": True,
            "match": False
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/api/send_email", methods=["POST"])
def api_send_email():
    data = request.json
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    address = data.get("address", "").strip()
    pet_id = data.get("pet_id")

    if not all([name, email, address, pet_id]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get pet info
        cursor.execute("SELECT name, user_id FROM pets WHERE id = ?", (pet_id,))
        pet_row = cursor.fetchone()
        if not pet_row:
            conn.close()
            return jsonify({"success": False, "message": "Pet not found"}), 404
        pet_name, owner_id = pet_row

        # Get owner info
        cursor.execute("SELECT username, email FROM users WHERE id = ?", (owner_id,))
        owner_row = cursor.fetchone()
        if not owner_row:
            conn.close()
            return jsonify({"success": False, "message": "Owner not found"}), 404
        owner_name, owner_email = owner_row

        conn.close()

        # Prepare email content
        subject = f"Your pet {pet_name} has been found!"
        body = f"""
Hello {owner_name},

Good news! Your pet, {pet_name}, has been found.

Finder's Name: {name}
Finder's Email: {email}
Finder's Address: {address}

Please contact the finder to recover your pet.

Best regards,
Pet Finder App
"""

        # Send email
        success, msg = send_email(owner_email, subject, body)
        if not success:
            return jsonify({"success": False, "message": f"Failed to send email: {msg}"}), 500

        return jsonify({"success": True, "message": "Email sent to pet owner successfully"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
# --- Run app ---
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
