from flask import Blueprint, render_template, request
from app.database import get_db_connection

advisory_bp = Blueprint("advisory", __name__)

@advisory_bp.route("/advisory")
def view_advisory():
    selected_crop = request.args.get("crop", "").strip()

    conn = get_db_connection()
    if selected_crop:
        advisories = conn.execute(
            "SELECT * FROM advisory_items WHERE LOWER(crop) = LOWER(?) ORDER BY id ASC",
            (selected_crop,)
        ).fetchall()
    else:
        advisories = conn.execute("SELECT * FROM advisory_items ORDER BY crop ASC, id ASC").fetchall()
    conn.close()

    return render_template(
        "advisory.html",
        active_page="advisory",
        advisories=advisories,
        selected_crop=selected_crop
    )
