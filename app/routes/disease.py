import os
import shutil
import time
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from werkzeug.utils import secure_filename

from app.config import Config
from app.database import get_db_connection
from app.services.ai_detector import validate_uploaded_image, analyze_leaf_image

disease_bp = Blueprint("disease", __name__, url_prefix="/disease")

@disease_bp.route("/scan", methods=["GET"])
def scan_page():
    return render_template("disease_scan.html", active_page="disease")

@disease_bp.route("/analyze", methods=["POST"])
def analyze_scan():
    crop_name = request.form.get("crop_name", "Cotton")
    sample_name = request.form.get("sample_image_name", "").strip()
    
    saved_filename = None
    saved_path = None

    # Option A: Quick Sample Leaf testing for Judges
    if sample_name:
        safe_sample = secure_filename(sample_name)
        if safe_sample:
            sample_source = Config.BASE_DIR / "app" / "static" / "img" / "samples" / safe_sample
            if sample_source.exists():
                timestamp = int(time.time())
                saved_filename = f"sample_{timestamp}_{safe_sample}"
                saved_path = Config.UPLOAD_FOLDER / saved_filename
                shutil.copy(sample_source, saved_path)

    # Option B: Uploaded Leaf Photo from Farmer
    if not saved_path:
        if "leaf_image" not in request.files:
            flash("कृपया पिकाच्या पानाचा फोटो निवडा / Please select or upload a leaf photo.", "warning")
            return redirect(url_for("disease.scan_page"))

        file = request.files["leaf_image"]
        if file.filename == "":
            flash("कोणतीही फाईल निवडली नाही / No file selected.", "warning")
            return redirect(url_for("disease.scan_page"))

        # Verify extension security against allowed list
        ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        if ext not in Config.ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(Config.ALLOWED_EXTENSIONS))
            flash(f"अवैध फाईल प्रकार. फक्त {allowed_list} समर्थित आहेत / Unsupported file format. Allowed: {allowed_list}", "danger")
            return redirect(url_for("disease.scan_page"))

        # Structural & Cryptographic PIL Image Validation
        is_valid, error_msg, _ = validate_uploaded_image(file.stream)
        if not is_valid:
            flash(error_msg, "danger")
            return redirect(url_for("disease.scan_page"))

        # Reset stream and save securely
        file.stream.seek(0)
        timestamp = int(time.time())
        base_name = file.filename.rsplit(".", 1)[0] if "." in file.filename else "leaf"
        clean_name = secure_filename(base_name) or "leaf"
        saved_filename = f"scan_{timestamp}_{clean_name}.{ext}"
        saved_path = Config.UPLOAD_FOLDER / saved_filename
        file.save(saved_path)

    # Execute Computer Vision Diagnostic Analysis
    try:
        diagnosis = analyze_leaf_image(saved_path, crop_hint=crop_name)
    except Exception as e:
        flash(f"प्रतिमा विश्लेषणात त्रुटी उद्भवली: {str(e)}", "danger")
        return redirect(url_for("disease.scan_page"))

    # Persist Diagnostic Record into Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scans (
            filename, crop_name, predicted_disease, disease_mr, disease_hi,
            confidence, status, severity,
            summary_en, summary_hi, summary_mr,
            organic_remedy, chemical_remedy, prevention_tip, model_mode
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        saved_filename,
        crop_name,
        diagnosis["disease_en"],
        diagnosis.get("disease_mr"),
        diagnosis.get("disease_hi"),
        diagnosis["confidence"],
        diagnosis["status"],
        diagnosis["severity"],
        diagnosis["summary_en"],
        diagnosis["summary_hi"],
        diagnosis["summary_mr"],
        diagnosis["organic_remedy"],
        diagnosis["chemical_remedy"],
        diagnosis["prevention"],
        diagnosis["model_mode"]
    ))
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()

    flash(f"निदान यशस्वी झाले: {diagnosis['disease_mr']}", "success")
    return redirect(url_for("disease.view_result", scan_id=scan_id))

@disease_bp.route("/result/<int:scan_id>")
def view_result(scan_id):
    conn = get_db_connection()
    scan = conn.execute("SELECT * FROM scans WHERE id = ?", (scan_id,)).fetchone()
    conn.close()

    if not scan:
        flash("तपासणी अहवाल सापडला नाही / Scan record not found.", "warning")
        return redirect(url_for("disease.scan_page"))

    return render_template(
        "disease_result.html",
        active_page="disease",
        scan=scan
    )
