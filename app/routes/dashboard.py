from flask import Blueprint, render_template
from app.database import get_db_connection
from app.services.weather_service import get_weather_data
from app.config import Config

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def view_dashboard():
    conn = get_db_connection()
    scans = conn.execute("SELECT * FROM scans ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()

    # Get live weather summary for farmer's default district
    default_dist = Config.DEFAULT_DISTRICT
    weather = get_weather_data(default_dist)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        scans=scans,
        weather=weather
    )
