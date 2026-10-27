"""DB Lab 3 - Library & To-Do Application (Flask + PyMySQL + bcrypt).

Continues from Lab 2 (users & todos) and implements Problem 2:
- F2.1: Books table (with author_id) and Authors table
- F2.2: Add book and add author
- F2.3: Edit book and edit author
- F2.4: Remove a book
- F2.5: Remove an author (cascades to their books)
- Bonus: Image upload for book covers and author photos
"""
import os
import uuid
from decimal import Decimal, InvalidOperation
from functools import wraps

import bcrypt
import pymysql
from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "db-lab3-secret-key-fall2026")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16 MB max upload
)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TITLE_MAX = 200
NAME_MAX = 100
COUNTRY_MAX = 100


# ---------------------------------------------------------------- database
def get_db():
    """Open a new MySQL connection. Every value is passed as a %s parameter."""
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", "root"),
        database=os.environ.get("DB_NAME", "library"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def query(sql, params=(), fetch=None):
    """Run one parameterized statement. fetch: None, 'one' or 'all'."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if fetch == "one":
                return cur.fetchone()
            if fetch == "all":
                return cur.fetchall()
            return cur.rowcount
    finally:
        conn.close()


def ensure_auth_tables():
    """Ensure Lab 2 tables (users, todos) exist if user navigates to auth/todos."""
    query("""
        CREATE TABLE IF NOT EXISTS users (
            user_id           INT          NOT NULL AUTO_INCREMENT,
            email             VARCHAR(255) NOT NULL,
            name              VARCHAR(100) NOT NULL,
            password_hash     VARCHAR(255) NOT NULL,
            registration_date TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id),
            UNIQUE (email)
        )
    """)
    query("""
        CREATE TABLE IF NOT EXISTS todos (
            todo_id    INT          NOT NULL AUTO_INCREMENT,
            user_id    INT          NOT NULL,
            title      VARCHAR(200) NOT NULL,
            is_done    TINYINT(1)   NOT NULL DEFAULT 0,
            created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (todo_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """)


# ---------------------------------------------------------------- upload helper
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage, prefix="img"):
    """Save an uploaded file safely to static/uploads and return the filename."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    clean_name = secure_filename(file_storage.filename.rsplit(".", 1)[0])[:30]
    unique_name = f"{prefix}_{clean_name}_{uuid.uuid4().hex[:8]}.{ext}"
    target_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(target_path)
    return unique_name


def delete_upload(filename):
    """Delete an image only if it is a file inside this app's uploads folder."""
    if not filename:
        return
    safe_name = os.path.basename(str(filename))
    path = os.path.abspath(os.path.join(UPLOAD_FOLDER, safe_name))
    upload_root = os.path.abspath(UPLOAD_FOLDER)
    if os.path.dirname(path) == upload_root and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            app.logger.exception("Could not delete uploaded image: %s", safe_name)


def normalized_text(value):
    """Normalize names/titles so casing and repeated whitespace don't create duplicates."""
    return " ".join((value or "").split()).casefold()


def find_duplicate_author(name, exclude_id=None):
    """Return an existing author with the same normalized name, if any."""
    authors = query("SELECT author_id, name FROM author", fetch="all")
    for author in authors:
        if exclude_id is not None and author["author_id"] == exclude_id:
            continue
        if normalized_text(author["name"]) == normalized_text(name):
            return author
    return None


def find_duplicate_book(title, exclude_id=None):
    """Return an existing book with the same normalized title, if any."""
    books = query("SELECT book_id, title FROM book", fetch="all")
    for book in books:
        if exclude_id is not None and book["book_id"] == exclude_id:
            continue
        if normalized_text(book["title"]) == normalized_text(title):
            return book
    return None


# ---------------------------------------------------------------- helpers & auth
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def validate_title(title):
    t = title.strip()
    if not t:
        return "Title is required"
    if len(t) > TITLE_MAX:
        return "Title is too long"
    return None


@app.route("/")
def index():
    """Landing page: directs to the Books catalog."""
    return redirect(url_for("books"))


@app.route("/register", methods=["GET", "POST"])
def register():
    ensure_auth_tables()
    if "user_id" in session:
        return redirect(url_for("todos"))
    form = {"name": "", "email": ""}
    errors = {}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        form = {"name": name, "email": email}

        if not name:
            errors["name"] = "Name is required"
        if not email:
            errors["email"] = "Email is required"
        if not password:
            errors["password"] = "Password is required"
        if not confirm:
            errors["confirm_password"] = "Confirm password is required"
        elif password and password != confirm:
            errors["confirm_password"] = "Passwords do not match"

        if not errors:
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
            try:
                query("INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
                      (email, name, pw_hash))
            except pymysql.err.IntegrityError as e:
                if e.args[0] == 1062:
                    errors["email"] = "Email Already Exists"
                else:
                    raise
            else:
                user = query("SELECT user_id, name, password_hash FROM users WHERE email = %s",
                             (email,), fetch="one")
                session.clear()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("todos"))
    return render_template("register.html", form=form, errors=errors), (400 if errors else 200)


@app.route("/login", methods=["GET", "POST"])
def login():
    ensure_auth_tables()
    if "user_id" in session:
        return redirect(url_for("todos"))
    email = ""
    errors = {}
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email:
            errors["email"] = "Email is required"
        if not password:
            errors["password"] = "Password is required"
        if not errors:
            user = query("SELECT user_id, name, password_hash FROM users WHERE email = %s",
                         (email,), fetch="one")
            if user and bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
                session.clear()
                session["user_id"] = user["user_id"]
                session["name"] = user["name"]
                return redirect(url_for("todos"))
            errors["form"] = "Invalid email or password"
    return render_template("login.html", email=email, errors=errors), (400 if errors else 200)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------- to-dos (Lab 2)
def render_list(errors=None, new_title="", edit_values=None, status=200):
    ensure_auth_tables()
    items = query("SELECT todo_id, title, is_done, created_at FROM todos "
                  "WHERE user_id = %s ORDER BY todo_id DESC",
                  (session["user_id"],), fetch="all")
    show = request.args.get("show", "all")
    open_count = sum(1 for t in items if not t["is_done"])
    if show == "open":
        visible = [t for t in items if not t["is_done"]]
    elif show == "done":
        visible = [t for t in items if t["is_done"]]
    else:
        show, visible = "all", items
    return render_template("todos.html", todos=visible, total=len(items), open_count=open_count,
                           show=show, errors=errors or {}, new_title=new_title,
                           edit_values=edit_values or {}), status


def back_to_list():
    show = request.args.get("show")
    return redirect(url_for("todos", show=show) if show in ("open", "done") else url_for("todos"))


@app.route("/todos")
@login_required
def todos():
    return render_list()


@app.route("/todos/add", methods=["POST"])
@login_required
def add_todo():
    title = request.form.get("title", "")
    error = validate_title(title)
    if error:
        return render_list(errors={"new": error}, new_title=title, status=400)
    query("INSERT INTO todos (user_id, title) VALUES (%s, %s)",
          (session["user_id"], title.strip()))
    return back_to_list()


@app.route("/todos/<int:todo_id>/edit", methods=["POST"])
@login_required
def edit_todo(todo_id):
    title = request.form.get("title", "")
    error = validate_title(title)
    if error:
        return render_list(errors={todo_id: error}, edit_values={todo_id: title}, status=400)
    query("UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s",
          (title.strip(), todo_id, session["user_id"]))
    return back_to_list()


@app.route("/todos/<int:todo_id>/done", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    is_done = 1 if request.form.get("is_done") == "1" else 0
    query("UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s",
          (is_done, todo_id, session["user_id"]))
    return back_to_list()


@app.route("/todos/<int:todo_id>/delete", methods=["POST"])
@login_required
def delete_todo(todo_id):
    query("DELETE FROM todos WHERE todo_id = %s AND user_id = %s",
          (todo_id, session["user_id"]))
    return back_to_list()


# ============================================================================
# PROBLEM 2: Library: Books and Authors (F2.1 - F2.5 + Bonus)
# ============================================================================

# ---------------------------------------------------------------- AUTHORS
@app.route("/authors")
def authors():
    """F2.1: Show a table of the authors."""
    author_list = query(
        "SELECT author_id, name, country, photo FROM author ORDER BY author_id ASC",
        fetch="all"
    )
    # Also count books for each author using simple queries (without complex joins)
    book_counts = {}
    books = query("SELECT author_id FROM book", fetch="all")
    for b in books:
        aid = b["author_id"]
        book_counts[aid] = book_counts.get(aid, 0) + 1

    return render_template("authors.html", authors=author_list, book_counts=book_counts)


@app.route("/authors/add", methods=["GET", "POST"])
def add_author():
    """F2.2: Add an author (+ bonus photo upload)."""
    form = {"name": "", "country": ""}
    errors = {}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "").strip()
        form = {"name": name, "country": country}

        if not name:
            errors["name"] = "Name is required"
        elif len(name) > NAME_MAX:
            errors["name"] = f"Name must be at most {NAME_MAX} characters"
        elif find_duplicate_author(name):
            errors["name"] = "An author with this name already exists"

        if country and len(country) > COUNTRY_MAX:
            errors["country"] = f"Country must be at most {COUNTRY_MAX} characters"

        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename and not allowed_file(photo_file.filename):
            errors["photo"] = "Allowed image formats: png, jpg, jpeg, gif, webp"

        if not errors:
            photo_filename = save_upload(photo_file, prefix="author")
            query(
                "INSERT INTO author (name, country, photo) VALUES (%s, %s, %s)",
                (name, country or None, photo_filename)
            )
            flash(f"Author '{name}' added successfully!", "success")
            return redirect(url_for("authors"))

    return render_template("author_form.html", form=form, errors=errors, is_edit=False), (400 if errors else 200)


@app.route("/authors/<int:author_id>/edit", methods=["GET", "POST"])
def edit_author(author_id):
    """F2.3: Edit an author (+ bonus photo update)."""
    author = query("SELECT author_id, name, country, photo FROM author WHERE author_id = %s",
                   (author_id,), fetch="one")
    if not author:
        return render_template("error.html", title="Author not found",
                               message=f"No author found with ID {author_id}."), 404

    form = {"name": author["name"], "country": author["country"] or ""}
    errors = {}

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "").strip()
        form = {"name": name, "country": country}

        if not name:
            errors["name"] = "Name is required"
        elif len(name) > NAME_MAX:
            errors["name"] = f"Name must be at most {NAME_MAX} characters"
        elif find_duplicate_author(name, exclude_id=author_id):
            errors["name"] = "An author with this name already exists"

        if country and len(country) > COUNTRY_MAX:
            errors["country"] = f"Country must be at most {COUNTRY_MAX} characters"

        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename and not allowed_file(photo_file.filename):
            errors["photo"] = "Allowed image formats: png, jpg, jpeg, gif, webp"

        if not errors:
            remove_photo = request.form.get("remove_photo") == "1"
            if (photo_file and photo_file.filename) or remove_photo:
                new_photo = save_upload(photo_file, prefix="author") if photo_file and photo_file.filename else None
                query(
                    "UPDATE author SET name = %s, country = %s, photo = %s WHERE author_id = %s",
                    (name, country or None, new_photo, author_id)
                )
                if author.get("photo") and author.get("photo") != new_photo:
                    delete_upload(author["photo"])
            else:
                query(
                    "UPDATE author SET name = %s, country = %s WHERE author_id = %s",
                    (name, country or None, author_id)
                )
            flash(f"Author '{name}' updated successfully!", "success")
            return redirect(url_for("authors"))

    return render_template("author_form.html", form=form, errors=errors,
                           is_edit=True, author=author), (400 if errors else 200)


@app.route("/authors/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    """F2.5: Remove an author. (Foreign key ON DELETE CASCADE removes all their books too)."""
    author = query("SELECT name, photo FROM author WHERE author_id = %s", (author_id,), fetch="one")
    name = author["name"] if author else f"ID {author_id}"
    if author:
        related_books = query("SELECT cover FROM book WHERE author_id = %s", (author_id,), fetch="all")
        query("DELETE FROM author WHERE author_id = %s", (author_id,))
        delete_upload(author.get("photo"))
        for related_book in related_books:
            delete_upload(related_book.get("cover"))
    flash(f"Author '{name}' and all their books were deleted (CASCADE).", "success")
    return redirect(url_for("authors"))


# ---------------------------------------------------------------- BOOKS
@app.route("/books")
def books():
    """F2.1: Show a table of the books (with the author_id of each book)."""
    book_list = query(
        "SELECT book_id, title, price, author_id, cover FROM book ORDER BY book_id ASC",
        fetch="all"
    )
    # Fetch authors to map author_id -> author name for display (pure SELECT, no SQL join)
    authors_data = query("SELECT author_id, name FROM author", fetch="all")
    author_map = {a["author_id"]: a["name"] for a in authors_data}

    return render_template("books.html", books=book_list, author_map=author_map)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    """F2.2: Add a book (+ bonus cover upload)."""
    authors_list = query("SELECT author_id, name FROM author ORDER BY name ASC", fetch="all")
    form = {"title": "", "price": "", "author_id": ""}
    errors = {}

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price_raw = request.form.get("price", "").strip()
        author_id_raw = request.form.get("author_id", "").strip()
        form = {"title": title, "price": price_raw, "author_id": author_id_raw}

        if not title:
            errors["title"] = "Title is required"
        elif len(title) > TITLE_MAX:
            errors["title"] = f"Title must be at most {TITLE_MAX} characters"
        elif find_duplicate_book(title):
            errors["title"] = "A book with this title already exists"

        price_val = None
        if not price_raw:
            errors["price"] = "Price is required"
        else:
            try:
                price_val = Decimal(price_raw)
                if price_val < 0:
                    errors["price"] = "Price cannot be negative"
            except (InvalidOperation, ValueError):
                errors["price"] = "Price must be a valid number (e.g. 15.50)"

        author_id_val = None
        if not author_id_raw:
            errors["author_id"] = "Author is required"
        else:
            try:
                author_id_val = int(author_id_raw)
                exists = query("SELECT author_id FROM author WHERE author_id = %s",
                               (author_id_val,), fetch="one")
                if not exists:
                    errors["author_id"] = "Selected author does not exist"
            except ValueError:
                errors["author_id"] = "Invalid author ID"

        cover_file = request.files.get("cover")
        if cover_file and cover_file.filename and not allowed_file(cover_file.filename):
            errors["cover"] = "Allowed image formats: png, jpg, jpeg, gif, webp"

        if not errors:
            cover_filename = save_upload(cover_file, prefix="book")
            query(
                "INSERT INTO book (title, price, author_id, cover) VALUES (%s, %s, %s, %s)",
                (title, float(price_val), author_id_val, cover_filename)
            )
            flash(f"Book '{title}' added successfully!", "success")
            return redirect(url_for("books"))

    return render_template("book_form.html", form=form, errors=errors,
                           authors=authors_list, is_edit=False), (400 if errors else 200)


@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def edit_book(book_id):
    """F2.3: Edit a book (+ bonus cover update)."""
    book = query("SELECT book_id, title, price, author_id, cover FROM book WHERE book_id = %s",
                 (book_id,), fetch="one")
    if not book:
        return render_template("error.html", title="Book not found",
                               message=f"No book found with ID {book_id}."), 404

    authors_list = query("SELECT author_id, name FROM author ORDER BY name ASC", fetch="all")
    form = {
        "title": book["title"],
        "price": f"{book['price']:.2f}" if isinstance(book["price"], (int, float, Decimal)) else str(book["price"]),
        "author_id": str(book["author_id"]),
    }
    errors = {}

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        price_raw = request.form.get("price", "").strip()
        author_id_raw = request.form.get("author_id", "").strip()
        form = {"title": title, "price": price_raw, "author_id": author_id_raw}

        if not title:
            errors["title"] = "Title is required"
        elif len(title) > TITLE_MAX:
            errors["title"] = f"Title must be at most {TITLE_MAX} characters"
        elif find_duplicate_book(title, exclude_id=book_id):
            errors["title"] = "A book with this title already exists"

        price_val = None
        if not price_raw:
            errors["price"] = "Price is required"
        else:
            try:
                price_val = Decimal(price_raw)
                if price_val < 0:
                    errors["price"] = "Price cannot be negative"
            except (InvalidOperation, ValueError):
                errors["price"] = "Price must be a valid number (e.g. 15.50)"

        author_id_val = None
        if not author_id_raw:
            errors["author_id"] = "Author is required"
        else:
            try:
                author_id_val = int(author_id_raw)
                exists = query("SELECT author_id FROM author WHERE author_id = %s",
                               (author_id_val,), fetch="one")
                if not exists:
                    errors["author_id"] = "Selected author does not exist"
            except ValueError:
                errors["author_id"] = "Invalid author ID"

        cover_file = request.files.get("cover")
        if cover_file and cover_file.filename and not allowed_file(cover_file.filename):
            errors["cover"] = "Allowed image formats: png, jpg, jpeg, gif, webp"

        if not errors:
            remove_cover = request.form.get("remove_cover") == "1"
            if (cover_file and cover_file.filename) or remove_cover:
                new_cover = save_upload(cover_file, prefix="book") if cover_file and cover_file.filename else None
                query(
                    "UPDATE book SET title = %s, price = %s, author_id = %s, cover = %s WHERE book_id = %s",
                    (title, float(price_val), author_id_val, new_cover, book_id)
                )
                if book.get("cover") and book.get("cover") != new_cover:
                    delete_upload(book["cover"])
            else:
                query(
                    "UPDATE book SET title = %s, price = %s, author_id = %s WHERE book_id = %s",
                    (title, float(price_val), author_id_val, book_id)
                )
            flash(f"Book '{title}' updated successfully!", "success")
            return redirect(url_for("books"))

    return render_template("book_form.html", form=form, errors=errors,
                           authors=authors_list, is_edit=True, book=book), (400 if errors else 200)


@app.route("/books/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """F2.4: Remove a book."""
    book = query("SELECT title, cover FROM book WHERE book_id = %s", (book_id,), fetch="one")
    title = book["title"] if book else f"ID {book_id}"
    if book:
        query("DELETE FROM book WHERE book_id = %s", (book_id,))
        delete_upload(book.get("cover"))
    flash(f"Book '{title}' was deleted successfully.", "success")
    return redirect(url_for("books"))


# ---------------------------------------------------------------- errors
@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", title="Page not found",
                           message="The page you are looking for does not exist."), 404


@app.errorhandler(405)
def not_allowed(_e):
    return render_template("error.html", title="Not allowed",
                           message="That action is not allowed here."), 405


@app.errorhandler(Exception)
def server_error(e):
    if isinstance(e, HTTPException):
        return render_template("error.html", title=e.name, message=e.description), e.code
    app.logger.exception(e)
    return render_template("error.html", title="Something went wrong",
                           message="Please try again in a moment."), 500


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1",
            port=int(os.environ.get("PORT", 5000)))
