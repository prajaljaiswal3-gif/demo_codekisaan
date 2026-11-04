from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.database import get_db_connection
from app.services.weather_service import get_weather_data, MAHARASHTRA_DISTRICTS
from app.config import Config
from app.routes.auth import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def view_dashboard():
    farmer_id = session.get("farmer_id")
    conn = get_db_connection()

    # Load authenticated farmer's profile
    farmer = conn.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
    if not farmer:
        session.clear()
        flash("खाते माहिती सापडली नाही. कृपया पुन्हा लॉगिन करा. / Farmer profile not found. Please log in again.", "warning")
        return redirect(url_for("auth.login"))

    # Fetch farmer's personal disease detection reports
    farmer_scans = conn.execute(
        "SELECT * FROM scans WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer_id,)
    ).fetchall()

    # Fetch recent scans overall (for analytics charts and fallback demonstration)
    all_scans = conn.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT 10").fetchall()

    # Fetch smart farming advisory recommendations
    recommendations = conn.execute(
        "SELECT * FROM advisory_items ORDER BY id ASC LIMIT 4"
    ).fetchall()

    conn.close()

    # Determine district for weather: requested district override or farmer's registered district
    district_query = request.args.get("district", "").strip()
    if district_query and district_query in MAHARASHTRA_DISTRICTS:
        selected_district = district_query
    elif farmer["district"] and farmer["district"] in MAHARASHTRA_DISTRICTS:
        selected_district = farmer["district"]
    else:
        selected_district = Config.DEFAULT_DISTRICT

    weather = get_weather_data(selected_district)

    # Scans to display in the reports table
    display_scans = farmer_scans if len(farmer_scans) > 0 else all_scans

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        farmer=farmer,
        scans=display_scans,
        farmer_scans=farmer_scans,
        all_scans=all_scans,
        has_personal_scans=(len(farmer_scans) > 0),
        weather=weather,
        recommendations=recommendations,
        selected_district=selected_district
    )
