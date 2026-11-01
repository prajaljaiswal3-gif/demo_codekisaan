from flask import Blueprint, render_template, request
from app.services.weather_service import get_weather_data, MAHARASHTRA_DISTRICTS
from app.config import Config

weather_bp = Blueprint("weather", __name__)

@weather_bp.route("/weather")
def view_weather():
    selected_district = request.args.get("district", Config.DEFAULT_DISTRICT).strip()
    if selected_district not in MAHARASHTRA_DISTRICTS:
        selected_district = Config.DEFAULT_DISTRICT

    weather_data = get_weather_data(selected_district)

    return render_template(
        "weather.html",
        active_page="weather",
        weather=weather_data,
        districts=MAHARASHTRA_DISTRICTS,
        selected_district=selected_district
    )
