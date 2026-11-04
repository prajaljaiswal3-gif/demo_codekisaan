import re
from functools import wraps
from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import get_db_connection

auth_bp = Blueprint("auth", __name__)

MAHARASHTRA_DISTRICTS_LIST = [
    "Ahmednagar", "Akola", "Amravati", "Chhatrapati Sambhaji Nagar", "Beed",
    "Bhandara", "Buldhana", "Chandrapur", "Dhule", "Gadchiroli", "Gondia",
    "Hingoli", "Jalgaon", "Jalna", "Kolhapur", "Latur", "Mumbai City",
    "Mumbai Suburban", "Nagpur", "Nanded", "Nandurbar", "Nashik",
    "Dharashiv (Osmanabad)", "Palghar", "Parbhani", "Pune", "Raigad",
    "Ratnagiri", "Sangli", "Satara", "Sindhudurg", "Solapur", "Thane",
    "Wardha", "Washim", "Yavatmal"
]

def login_required(f):
    """
    Decorator to protect views so only authenticated farmers can access them.
    Redirects unauthenticated visitors to login with an informational notice.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("farmer_id"):
            flash("कृपया शेतकरी डॅशबोर्ड पाहण्यासाठी प्रथम लॉगिन करा. / Please log in to access your farmer dashboard.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def clean_mobile_number(raw_mobile):
    """Normalizes mobile number to 10 digits."""
    if not raw_mobile:
        return ""
    digits = re.sub(r"\D", "", raw_mobile)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, redirect directly to dashboard
    if session.get("farmer_id"):
        return redirect(url_for("dashboard.view_dashboard"))

    if request.method == "GET":
        return render_template(
            "register.html",
            active_page="register",
            districts=MAHARASHTRA_DISTRICTS_LIST,
            form_data={}
        )

    # Extract POST Form Data
    full_name = request.form.get("full_name", "").strip()
    raw_mobile = request.form.get("mobile_number", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    village = request.form.get("village", "").strip()
    district = request.form.get("district", "Pune").strip()
    state = request.form.get("state", "Maharashtra").strip() or "Maharashtra"

    clean_mobile = clean_mobile_number(raw_mobile)

    form_data = {
        "full_name": full_name,
        "mobile_number": raw_mobile,
        "email": email,
        "village": village,
        "district": district,
        "state": state
    }

    # 1. Validation: Full Name
    if len(full_name) < 2:
        flash("कृपया आपले पूर्ण नाव प्रविष्ट करा (किमान २ अक्षरे) / Please enter your full name (minimum 2 characters).", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 2. Validation: Mobile Number (10 digits)
    if len(clean_mobile) != 10 or not clean_mobile.isdigit():
        flash("कृपया वैध १० अंकी मोबाईल क्रमांक प्रविष्ट करा / Please enter a valid 10-digit mobile number.", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 3. Validation: Email (Optional, but if given must be valid format)
    if email:
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            flash("कृपया वैध ईमेल पत्ता प्रविष्ट करा / Please enter a valid email address.", "danger")
            return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 4. Validation: Password Length
    if len(password) < 6:
        flash("पासवर्ड किमान ६ अक्षरांचा असणे आवश्यक आहे / Password must be at least 6 characters long.", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 5. Validation: Confirm Password Matching
    if password != confirm_password:
        flash("पासवर्ड आणि पुष्टीकरण पासवर्ड जुळत नाहीत / Password and Confirm Password do not match.", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 6. Validation: Village & District
    if len(village) < 2:
        flash("कृपया आपल्या गावाचे नाव प्रविष्ट करा / Please enter your village name.", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    if not district:
        flash("कृपया जिल्हा निवडा / Please select your district.", "danger")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 7. Check for duplicate mobile number and email in Database
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_mobile = cursor.execute(
        "SELECT id FROM farmers WHERE mobile_number = ?", (clean_mobile,)
    ).fetchone()
    if existing_mobile:
        conn.close()
        flash("हा मोबाईल क्रमांक आधीच नोंदणीकृत आहे. कृपया लॉगिन करा. / This mobile number is already registered. Please log in.", "warning")
        return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    if email:
        existing_email = cursor.execute(
            "SELECT id FROM farmers WHERE LOWER(email) = LOWER(?)", (email,)
        ).fetchone()
        if existing_email:
            conn.close()
            flash("हा ईमेल पत्ता आधीच वापरला गेला आहे. कृपया दुसरा ईमेल वापरा. / This email address is already registered.", "warning")
            return render_template("register.html", active_page="register", districts=MAHARASHTRA_DISTRICTS_LIST, form_data=form_data)

    # 8. Hash Password securely and insert record
    hashed_pw = generate_password_hash(password)
    email_to_store = email if email else None

    cursor.execute("""
        INSERT INTO farmers (
            full_name, mobile_number, email, password_hash, village, district, state
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (full_name, clean_mobile, email_to_store, hashed_pw, village, district, state))
    new_farmer_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Automatically initialize farmer session upon successful registration
    session["farmer_id"] = new_farmer_id
    session["farmer_name"] = full_name
    session["farmer_mobile"] = clean_mobile
    session["farmer_district"] = district

    flash(f"नोंदणी यशस्वी! कोडकिसान शेतकरी सहकार्य केंद्रात आपले स्वागत आहे, {full_name}. / Registration successful! Welcome to CodeKisaan.", "success")
    return redirect(url_for("dashboard.view_dashboard"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect directly to dashboard
    if session.get("farmer_id"):
        return redirect(url_for("dashboard.view_dashboard"))

    next_url = request.args.get("next", "")

    if request.method == "GET":
        return render_template("login.html", active_page="login", next=next_url, mobile_number="")

    # Handle POST
    raw_mobile = request.form.get("mobile_number", "").strip()
    password = request.form.get("password", "")
    remember_me = request.form.get("remember_me")
    next_url = request.form.get("next") or request.args.get("next") or ""

    clean_mobile = clean_mobile_number(raw_mobile)

    if not clean_mobile or not password:
        flash("कृपया मोबाईल क्रमांक आणि पासवर्ड दोन्ही प्रविष्ट करा. / Please enter both mobile number and password.", "warning")
        return render_template("login.html", active_page="login", next=next_url, mobile_number=raw_mobile)

    conn = get_db_connection()
    farmer = conn.execute(
        "SELECT * FROM farmers WHERE mobile_number = ?", (clean_mobile,)
    ).fetchone()
    conn.close()

    # Verify farmer exists and password hash matches
    if not farmer or not check_password_hash(farmer["password_hash"], password):
        flash("मोबाईल क्रमांक किंवा पासवर्ड चुकीचा आहे. कृपया पुन्हा तपासा. / Invalid mobile number or password. Please try again.", "danger")
        return render_template("login.html", active_page="login", next=next_url, mobile_number=raw_mobile)

    # Establish session
    session["farmer_id"] = farmer["id"]
    session["farmer_name"] = farmer["full_name"]
    session["farmer_mobile"] = farmer["mobile_number"]
    session["farmer_district"] = farmer["district"]

    # Remember Me setting
    if remember_me:
        session.permanent = True
    else:
        session.permanent = False

    flash(f"स्वागत आहे, {farmer['full_name']}! / Welcome back, {farmer['full_name']}!", "success")

    # Safe redirect
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        parsed = urlparse(next_url)
        if not parsed.netloc:
            return redirect(next_url)

    return redirect(url_for("dashboard.view_dashboard"))

@auth_bp.route("/logout")
def logout():
    session.pop("farmer_id", None)
    session.pop("farmer_name", None)
    session.pop("farmer_mobile", None)
    session.pop("farmer_district", None)
    flash("आपण सुरक्षितपणे लॉगआउट झाला आहात. / You have been securely logged out.", "info")
    return redirect(url_for("auth.login"))
