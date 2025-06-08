from flask import Flask
from flask_cors import CORS 
# 1. Import your Blueprint objects
from routes.main_routes import main_bp
from routes.blog_routes import blog_bp
from routes.macro_routes import macro_bp

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    CORS(app) 
    # 2. Register the main blueprint
    app.register_blueprint(main_bp)

    # 3. Register the blog blueprint with a URL prefix
    # This means all routes in blog_bp will be prefixed with /blog
    # e.g., '/' becomes '/blog/' and '/<post_id>' becomes '/blog/<post_id>'
    app.register_blueprint(blog_bp, url_prefix='/blog')

    app.register_blueprint(macro_bp, url_prefix='/macro')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)