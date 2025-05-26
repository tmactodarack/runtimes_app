import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for
import markdown # Import the markdown library

# 1. Create a Blueprint object
# The first argument, 'blog', is the name of the blueprint.
# The second argument, __name__, is the import name of the blueprint's package.
blog_bp = Blueprint('blog', __name__)

DB_FILE = 'headlines.db'

# 2. Define routes using the Blueprint decorator
@blog_bp.route('/')
def list_posts():
    """Shows a list of all blog posts."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM posts ORDER BY timestamp DESC")
    posts = c.fetchall()
    conn.close()
    return render_template('blog.html', posts=posts)


@blog_bp.route('/<int:post_id>')
def show_post(post_id):
    """Shows a single blog post."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = c.fetchone()
    conn.close()
    return render_template('post.html', post=post)


@blog_bp.route('/create', methods=['GET', 'POST'])
def create_post():
    """Allows creating a new blog post."""
    if request.method == 'POST':
        title = request.form['title']
        content_markdown = request.form['content']
        content_html = markdown.markdown(content_markdown) # Convert markdown to HTML

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content_html))
        conn.commit()
        conn.close()
        return redirect(url_for('blog.list_posts')) # Redirect to the blog list after creating

    return render_template('create_post.html') # Render the form on GET request