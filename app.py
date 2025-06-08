from flask import Flask
from flask_cors import CORS 
# 1. Import your Blueprint objects
from routes.main_routes import main_bp
from routes.blog_routes import blog_bp
from routes.macro_routes import macro_bp
from routes.bess_routes import bess_bp

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    CORS(app) 
    # 2. Register the main blueprint
    app.register_blueprint(main_bp)

    app.register_blueprint(blog_bp, url_prefix='/blog')

    app.register_blueprint(macro_bp, url_prefix='/macro')

    app.register_blueprint(bess_bp, url_prefix='/bess')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)