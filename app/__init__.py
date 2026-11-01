import os
from flask import Flask, render_template, session, request
from app.config import Config
from app.database import init_db
from app.services.translation import get_text

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize SQLite database and seed data
    init_db()

    # Context Processor for Trilingual Translation Engine
    @app.context_processor
    def inject_translation():
        current_lang = session.get("lang", Config.DEFAULT_LANGUAGE)
        def t(key, default=None):
            return get_text(key, lang=current_lang, default=default)
        return dict(t=t, current_lang=current_lang, all_languages=Config.LANGUAGES)

    # Register Route Blueprints
    from app.routes.main import main_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.disease import disease_bp
    from app.routes.weather import weather_bp
    from app.routes.advisory import advisory_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(weather_bp)
    app.register_blueprint(advisory_bp)

    # Robust Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("base.html", active_page=""), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return "फोटोचा आकार 5MB पेक्षा जास्त आहे / File size exceeds 5MB limit.", 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return "सर्व्हर त्रुटी उद्भवली. कृपया पुन्हा प्रयत्न करा. / Internal Server Error.", 500

    return app
