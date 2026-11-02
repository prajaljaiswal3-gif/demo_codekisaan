import requests
from app.config import Config

MAHARASHTRA_DISTRICTS = {
    "Pune": {"lat": 18.5204, "lon": 73.8567, "marathi": "पुणे", "zone": "Western Maharashtra (Sugarcane/Vegetables)"},
    "Nashik": {"lat": 19.9975, "lon": 73.7898, "marathi": "नाशिक", "zone": "Northern Maharashtra (Grapes/Onion/Tomato)"},
    "Nagpur": {"lat": 21.1458, "lon": 79.0882, "marathi": "नागपूर", "zone": "Vidarbha (Cotton/Soybean/Oranges)"},
    "Solapur": {"lat": 17.6599, "lon": 75.9064, "marathi": "सोलापूर", "zone": "Southern Maharashtra (Pomegranate/Pulses)"},
    "Chhatrapati Sambhaji Nagar": {"lat": 19.8762, "lon": 75.3433, "marathi": "छत्रपती संभाजीनगर", "zone": "Marathwada (Cotton/Soybean/Maize)"},
    "Kolhapur": {"lat": 16.7050, "lon": 74.2433, "marathi": "कोल्हापूर", "zone": "South-West Maharashtra (Sugarcane/Rice)"},
    "Amravati": {"lat": 20.9374, "lon": 77.7796, "marathi": "अमरावती", "zone": "Vidarbha (Cotton/Soybean/Pigeon Pea)"},
    "Jalgaon": {"lat": 21.0077, "lon": 75.5626, "marathi": "जळगाव", "zone": "Khandesh (Banana/Cotton)"},
    "Nanded": {"lat": 19.1383, "lon": 77.3210, "marathi": "नांदेड", "zone": "Marathwada (Soybean/Cotton/Turmeric)"},
    "Ahmednagar": {"lat": 19.0948, "lon": 74.7480, "marathi": "अहमदनगर", "zone": "Western Maharashtra (Sugarcane/Onion)"}
}

# Weather code interpretations (WMO Code standard)
WMO_CODES = {
    0: ("Clear sky", "स्वच्छ आकाश", "स्वच्छ आकाश", "bi-sun-fill text-warning"),
    1: ("Mainly clear", "मुख्यतः साफ", "मुख्यतः स्वच्छ", "bi-cloud-sun text-warning"),
    2: ("Partly cloudy", "आंशिक बादल", "अंशतः ढगाळ", "bi-cloud-sun text-secondary"),
    3: ("Overcast", "बादल छाए रहेंगे", "पूर्णतः ढगाळ", "bi-clouds-fill text-secondary"),
    45: ("Foggy", "कोहरा", "धुके", "bi-cloud-fog-fill text-muted"),
    51: ("Light drizzle", "हल्की बूंदाबांदी", "हलकी रिमझिम", "bi-cloud-drizzle text-info"),
    61: ("Slight rain", "हल्की बारिश", "हलका पाऊस", "bi-cloud-rain text-primary"),
    63: ("Moderate rain", "मध्यम बारिश", "मध्यम पाऊस", "bi-cloud-rain-heavy text-primary"),
    65: ("Heavy rain", "भारी बारिश", "मुसळधार पाऊस", "bi-cloud-lightning-rain-fill text-danger"),
    80: ("Rain showers", "वर्षा की बौछारें", "पावसाची सर", "bi-cloud-rain text-primary"),
    95: ("Thunderstorm", "गरज के साथ तूफान", "विजांसह वादळी पाऊस", "bi-cloud-lightning-fill text-danger")
}

def get_weather_data(district_name="Pune"):
    """
    Fetches real-time weather information for the specified Maharashtra district.
    Uses free Open-Meteo API by default (no API key required), or OpenWeatherMap if key is provided.
    """
    if district_name not in MAHARASHTRA_DISTRICTS:
        district_name = "Pune"

    coords = MAHARASHTRA_DISTRICTS[district_name]
    lat = coords["lat"]
    lon = coords["lon"]

    # If OpenWeatherMap API key is provided in .env, attempt to query it
    if Config.OPENWEATHERMAP_API_KEY:
        try:
            owm_data = _fetch_openweathermap(lat, lon, district_name)
            if owm_data:
                return owm_data
        except Exception:
            pass  # Fallback to zero-config Open-Meteo

    # Default robust engine: Open-Meteo (Real scientific meteorological data, zero cost, 100% reliable)
    try:
        return _fetch_open_meteo(lat, lon, district_name)
    except Exception as e:
        return _generate_safe_fallback(district_name, error_msg=str(e))

def _fetch_open_meteo(lat, lon, district_name):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
        "timezone": "Asia/Kolkata"
    }
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    curr = data.get("current") or {}
    daily = data.get("daily") or {}

    t_val = curr.get("temperature_2m")
    temp = round(float(t_val if t_val is not None else 28.0), 1)

    h_val = curr.get("relative_humidity_2m")
    humidity = round(float(h_val if h_val is not None else 60.0), 1)

    w_val = curr.get("wind_speed_10m")
    wind_speed = round(float(w_val if w_val is not None else 8.0), 1)

    p_val = curr.get("precipitation")
    precip = round(float(p_val if p_val is not None else 0.0), 1)

    w_code = curr.get("weather_code")
    w_code = int(w_code) if w_code is not None else 0

    weather_desc_en, weather_desc_hi, weather_desc_mr, icon_class = WMO_CODES.get(
        w_code, ("Fair", "सामान्य", "सामान्य", "bi-sun-fill text-warning")
    )

    # Calculate Agricultural Advisory Risk Metrics
    risk_assessment = _calculate_crop_risk(temp, humidity, precip, wind_speed)

    # Extended forecast summary
    forecast = []
    daily_times = daily.get("time") or []
    if len(daily_times) >= 3:
        num_days = min(4, len(daily_times))
        wcode_list = daily.get("weather_code") or []
        tmax_list = daily.get("temperature_2m_max") or []
        tmin_list = daily.get("temperature_2m_min") or []
        prec_list = daily.get("precipitation_sum") or []

        for i in range(num_days):
            day_wcode = wcode_list[i] if i < len(wcode_list) and wcode_list[i] is not None else 0
            day_desc_en, _, day_desc_mr, day_icon = WMO_CODES.get(day_wcode, ("Fair", "", "", "bi-sun"))

            tmax = tmax_list[i] if i < len(tmax_list) and tmax_list[i] is not None else 30.0
            tmin = tmin_list[i] if i < len(tmin_list) and tmin_list[i] is not None else 20.0
            prec_val = prec_list[i] if i < len(prec_list) and prec_list[i] is not None else 0.0

            forecast.append({
                "date": daily_times[i],
                "temp_max": round(float(tmax), 1),
                "temp_min": round(float(tmin), 1),
                "precip_sum": round(float(prec_val), 1),
                "desc_en": day_desc_en,
                "desc_mr": day_desc_mr,
                "icon": day_icon
            })

    return {
        "success": True,
        "district": district_name,
        "district_mr": MAHARASHTRA_DISTRICTS[district_name]["marathi"],
        "zone": MAHARASHTRA_DISTRICTS[district_name]["zone"],
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "precipitation": precip,
        "condition_en": weather_desc_en,
        "condition_hi": weather_desc_hi,
        "condition_mr": weather_desc_mr,
        "icon": icon_class,
        "risk": risk_assessment,
        "forecast": forecast,
        "source": "Open-Meteo Meteorological Service (Live Live Data)",
        "has_live_api": True
    }

def _fetch_openweathermap(lat, lon, district_name):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={Config.OPENWEATHERMAP_API_KEY}&units=metric"
    resp = requests.get(url, timeout=4)
    resp.raise_for_status()
    data = resp.json()

    main_data = data.get("main") or {}
    wind_data = data.get("wind") or {}
    rain_data = data.get("rain") or {}
    weather_list = data.get("weather") or [{}]

    temp_val = main_data.get("temp", 28.0)
    temp = round(float(temp_val if temp_val is not None else 28.0), 1)

    hum_val = main_data.get("humidity", 60.0)
    humidity = round(float(hum_val if hum_val is not None else 60.0), 1)

    wind_val = wind_data.get("speed", 3.0)
    wind_speed = round(float(wind_val if wind_val is not None else 3.0) * 3.6, 1)  # convert m/s to km/h

    precip_val = rain_data.get("1h", 0.0) if isinstance(rain_data, dict) else 0.0
    precip = round(float(precip_val if precip_val is not None else 0.0), 1)

    cond_en = (weather_list[0] if weather_list else {}).get("main", "Clear")

    risk_assessment = _calculate_crop_risk(temp, humidity, precip, wind_speed)

    return {
        "success": True,
        "district": district_name,
        "district_mr": MAHARASHTRA_DISTRICTS[district_name]["marathi"],
        "zone": MAHARASHTRA_DISTRICTS[district_name]["zone"],
        "temperature": temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "precipitation": precip,
        "condition_en": cond_en,
        "condition_hi": cond_en,
        "condition_mr": cond_en,
        "icon": "bi-cloud-sun text-warning",
        "risk": risk_assessment,
        "forecast": [],
        "source": "OpenWeatherMap API (Live Data)",
        "has_live_api": True
    }

def _calculate_crop_risk(temp, humidity, precip, wind_speed):
    """
    Computes scientific agro-climatic risk triggers based on ICAR and MPKV Rahuri parameters:
    - High humidity (>75%) + 20-28°C promotes fungal spores (Rust, Blight, Powdery Mildew).
    - High wind (>15 km/h) or active rainfall prevents pesticide foliar spraying.
    - Low humidity (<40%) + high temp (>34°C) increases moisture stress and sucking pest vulnerability.
    """
    # 1. Fungal Spore Risk
    if humidity >= 75 and 18 <= temp <= 30:
        fungal_level = "High"
        fungal_alert_en = "Elevated Fungal & Spore Risk: Favorable climate for Rust, Blight, and Downy Mildew."
        fungal_alert_mr = "बुरशीजन्य रोगांचा उच्च धोका: आर्द्रता जास्त असल्याने तांबेरा व करपा रोगाचा प्रादुर्भाव वाढू शकतो."
        fungal_badge = "danger"
    elif humidity >= 65:
        fungal_level = "Moderate"
        fungal_alert_en = "Moderate Fungal Risk: Inspect leaf undersides regularly for early infection."
        fungal_alert_mr = "मध्यम बुरशी धोका: पानांच्या खालच्या बाजूवर ठिपके किंवा पुरळ दिसतात का ते तपासावे."
        fungal_badge = "warning"
    else:
        fungal_level = "Low"
        fungal_alert_en = "Low Fungal Risk: Weather conditions currently dry and stable."
        fungal_alert_mr = "बुरशीचा धोका कमी: कोरडे हवामान असल्याने बुरशीचा प्रसार कमी राहील."
        fungal_badge = "success"

    # 2. Spraying Suitability
    if precip > 0.5:
        spray_ok = False
        spray_desc_en = "Spraying Not Advised: Rain will wash off active chemical and biological agents."
        spray_desc_mr = "फवारणी करू नये: पावसामुळे फवारलेले औषध वाहून जाऊन नुकसान होईल."
        spray_badge = "danger"
    elif wind_speed > 16:
        spray_ok = False
        spray_desc_en = "Spraying Restricted: Wind speed exceeds 16 km/h causing pesticide drift."
        spray_desc_mr = "फवारणी टाळावी: वाऱ्याचा वेग जास्त असल्याने औषधाचा योग्य परिणाम होणार नाही."
        spray_badge = "warning"
    else:
        spray_ok = True
        spray_desc_en = "Ideal Spraying Window: Calm winds and dry canopy favor efficient foliar spray."
        spray_desc_mr = "फवारणीसाठी उत्तम वेळ: शांत हवामान व कोरडे पान असल्याने औषध शोषले जाईल."
        spray_badge = "success"

    # 3. Irrigation Recommendation
    if precip >= 5:
        irrigation_en = "Skip Irrigation: Recent precipitation provides adequate soil root moisture."
        irrigation_mr = "सिंचन थांबवा: पावसामुळे जमिनीत पुरेशी ओल उपलब्ध आहे."
    elif temp > 33 and humidity < 50:
        irrigation_en = "Schedule Drip Irrigation: High evapotranspiration rate; irrigate in early morning."
        irrigation_mr = "सकाळच्या सत्रात ठिबक सिंचन करा: उष्णतेमुळे पाण्याचे बाष्पीभवन वेगाने होत आहे."
    else:
        irrigation_en = "Normal Irrigation Cycle: Maintain standard moisture schedule according to crop stage."
        irrigation_mr = "नियमित सिंचन ठेवा: पिकाच्या वाढीच्या अवस्थेनुसार नियमित पाणी द्यावे."

    return {
        "fungal_level": fungal_level,
        "fungal_badge": fungal_badge,
        "fungal_alert_en": fungal_alert_en,
        "fungal_alert_mr": fungal_alert_mr,
        "spray_ok": spray_ok,
        "spray_badge": spray_badge,
        "spray_desc_en": spray_desc_en,
        "spray_desc_mr": spray_desc_mr,
        "irrigation_en": irrigation_en,
        "irrigation_mr": irrigation_mr
    }

def _generate_safe_fallback(district_name, error_msg=""):
    """Graceful offline fallback that never fabricates live weather as active."""
    return {
        "success": False,
        "district": district_name,
        "district_mr": MAHARASHTRA_DISTRICTS.get(district_name, {}).get("marathi", district_name),
        "zone": MAHARASHTRA_DISTRICTS.get(district_name, {}).get("zone", "Maharashtra"),
        "temperature": 27.5,
        "humidity": 65.0,
        "wind_speed": 9.0,
        "precipitation": 0.0,
        "condition_en": "Station Offline",
        "condition_hi": "स्टेशन ऑफलाइन",
        "condition_mr": "माहिती उपलब्ध नाही",
        "icon": "bi-exclamation-triangle text-warning",
        "risk": _calculate_crop_risk(27.5, 65.0, 0.0, 9.0),
        "forecast": [],
        "source": "Local Fallback (Live meteorological connection currently unavailable)",
        "has_live_api": False,
        "error_detail": error_msg
    }
