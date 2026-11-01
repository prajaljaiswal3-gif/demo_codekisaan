import os
import sys

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    print("=" * 60)
    print("CodeKisaan - Seva Innovation Challenge 2026")
    print(f"Server launching at: http://127.0.0.1:{port}")
    print("Dedicated to the Farming Community of Maharashtra")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=debug)
