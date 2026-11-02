from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database import get_db_connection
from app.config import Config

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("index.html", active_page="home")

@main_bp.route("/about")
def about():
    return render_template("about.html", active_page="about")

@main_bp.route("/contact")
def contact():
    return render_template("contact.html", active_page="contact")

@main_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    farmer_name = request.form.get("farmer_name", "").strip()
    contact_number = request.form.get("contact_number", "").strip()
    district = request.form.get("district", "Pune").strip()
    crop_type = request.form.get("crop_type", "").strip()
    message = request.form.get("message", "").strip()

    if not farmer_name or not message:
        flash("कृपया आपले नाव आणि संदेश प्रविष्ट करा / Please enter name and query message.", "warning")
        return redirect(url_for("main.contact"))

    try:
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO feedback (farmer_name, contact_number, district, crop_type, message)
            VALUES (?, ?, ?, ?, ?)
        """, (farmer_name, contact_number, district, crop_type, message))
        conn.commit()
        conn.close()
        flash("धन्यवाद! आपला संदेश यशस्वीरीत्या नोंदवला गेला आहे. आमचे कृषी सहाय्यक लवकरच संपर्क साधतील.", "success")
    except Exception as e:
        flash(f"त्रुटी: संदेश जतन करता आला नाही ({str(e)})", "danger")

    return redirect(url_for("main.contact"))

@main_bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in Config.LANGUAGES:
        session["lang"] = lang
    next_url = request.args.get("next") or url_for("main.index")
    # Prevent open redirect vulnerabilities
    parsed = urlparse(next_url)
    if parsed.netloc or not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.index")
    return redirect(next_url)
