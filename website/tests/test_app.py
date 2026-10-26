"""Automated test suite for DB Lab 3: Books, Authors, Image Uploads, and To-Dos.
Run:  python -m pytest -q
"""
import io
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import app, ensure_auth_tables, query  # noqa: E402


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Clean tables before each test
    ensure_auth_tables()
    query("DELETE FROM book")
    query("DELETE FROM author")
    query("DELETE FROM todos")
    query("DELETE FROM users")
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------- Problem 2: Authors Tests
def test_authors_page_empty(client):
    r = client.get("/authors")
    assert r.status_code == 200
    assert "Authors Directory" in r.get_data(as_text=True)


def test_add_author_success(client):
    r = client.post("/authors/add", data={"name": "Naguib Mahfouz", "country": "Egypt"},
                    follow_redirects=True)
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Naguib Mahfouz" in body
    assert "Egypt" in body

    author = query("SELECT author_id, name, country FROM author WHERE name = %s",
                   ("Naguib Mahfouz",), fetch="one")
    assert author is not None
    assert author["country"] == "Egypt"


def test_add_author_validation_empty_name(client):
    r = client.post("/authors/add", data={"name": "   ", "country": "Egypt"})
    assert r.status_code == 400
    assert "Name is required" in r.get_data(as_text=True)
    assert query("SELECT COUNT(*) n FROM author", fetch="one")["n"] == 0


def test_edit_author(client):
    client.post("/authors/add", data={"name": "Old Name", "country": "Old Country"})
    author = query("SELECT author_id FROM author WHERE name = %s", ("Old Name",), fetch="one")
    aid = author["author_id"]

    # Check GET edit form
    r_get = client.get(f"/authors/{aid}/edit")
    assert r_get.status_code == 200
    assert "Old Name" in r_get.get_data(as_text=True)

    # Submit POST update
    r_post = client.post(f"/authors/{aid}/edit",
                         data={"name": "Updated Name", "country": "New Country"},
                         follow_redirects=True)
    assert r_post.status_code == 200
    assert "Updated Name" in r_post.get_data(as_text=True)

    updated = query("SELECT name, country FROM author WHERE author_id = %s", (aid,), fetch="one")
    assert updated["name"] == "Updated Name"
    assert updated["country"] == "New Country"


# ---------------------------------------------------------------- Problem 2: Books Tests
def test_books_page_empty(client):
    r = client.get("/books")
    assert r.status_code == 200
    assert "Books Catalog" in r.get_data(as_text=True)


def test_add_book_success(client):
    # First add author
    client.post("/authors/add", data={"name": "George Orwell", "country": "United Kingdom"})
    author = query("SELECT author_id FROM author WHERE name = %s", ("George Orwell",), fetch="one")
    aid = author["author_id"]

    r = client.post("/books/add",
                    data={"title": "1984", "price": "18.50", "author_id": str(aid)},
                    follow_redirects=True)
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "1984" in body
    assert "18.50" in body
    assert f"ID: {aid}" in body

    book = query("SELECT title, price, author_id FROM book WHERE title = %s", ("1984",), fetch="one")
    assert book is not None
    assert float(book["price"]) == 18.50
    assert book["author_id"] == aid


def test_add_book_validation(client):
    # Empty title
    r1 = client.post("/books/add", data={"title": "", "price": "10.00", "author_id": "1"})
    assert r1.status_code == 400
    assert "Title is required" in r1.get_data(as_text=True)

    # Invalid negative price
    r2 = client.post("/books/add", data={"title": "Test", "price": "-5", "author_id": "1"})
    assert r2.status_code == 400
    assert "Price cannot be negative" in r2.get_data(as_text=True)

    # Non-existent author
    r3 = client.post("/books/add", data={"title": "Test", "price": "15.00", "author_id": "999"})
    assert r3.status_code == 400
    assert "Selected author does not exist" in r3.get_data(as_text=True)


def test_edit_book(client):
    client.post("/authors/add", data={"name": "Author 1", "country": "Country 1"})
    author = query("SELECT author_id FROM author LIMIT 1", fetch="one")
    aid = author["author_id"]

    client.post("/books/add", data={"title": "Old Title", "price": "10.00", "author_id": str(aid)})
    book = query("SELECT book_id FROM book WHERE title = %s", ("Old Title",), fetch="one")
    bid = book["book_id"]

    r = client.post(f"/books/{bid}/edit",
                    data={"title": "New Title", "price": "25.00", "author_id": str(aid)},
                    follow_redirects=True)
    assert r.status_code == 200
    assert "New Title" in r.get_data(as_text=True)

    updated = query("SELECT title, price FROM book WHERE book_id = %s", (bid,), fetch="one")
    assert updated["title"] == "New Title"
    assert float(updated["price"]) == 25.00


def test_delete_book(client):
    client.post("/authors/add", data={"name": "Author 1", "country": "Country 1"})
    aid = query("SELECT author_id FROM author LIMIT 1", fetch="one")["author_id"]

    client.post("/books/add", data={"title": "To Delete", "price": "12.00", "author_id": str(aid)})
    bid = query("SELECT book_id FROM book WHERE title = %s", ("To Delete",), fetch="one")["book_id"]

    r = client.post(f"/books/{bid}/delete", follow_redirects=True)
    assert r.status_code == 200
    assert query("SELECT COUNT(*) n FROM book WHERE book_id = %s", (bid,), fetch="one")["n"] == 0


def test_delete_author_cascades_books(client):
    """Verifies referential integrity ON DELETE CASCADE."""
    client.post("/authors/add", data={"name": "Author Cascade", "country": "Country"})
    aid = query("SELECT author_id FROM author WHERE name = %s", ("Author Cascade",), fetch="one")["author_id"]

    client.post("/books/add", data={"title": "Cascade Book 1", "price": "10.00", "author_id": str(aid)})
    client.post("/books/add", data={"title": "Cascade Book 2", "price": "20.00", "author_id": str(aid)})
    assert query("SELECT COUNT(*) n FROM book WHERE author_id = %s", (aid,), fetch="one")["n"] == 2

    # Delete author -> should cascade and delete both books
    r = client.post(f"/authors/{aid}/delete", follow_redirects=True)
    assert r.status_code == 200
    assert query("SELECT COUNT(*) n FROM author WHERE author_id = %s", (aid,), fetch="one")["n"] == 0
    assert query("SELECT COUNT(*) n FROM book WHERE author_id = %s", (aid,), fetch="one")["n"] == 0


# ---------------------------------------------------------------- Bonus: Image Upload Tests
def test_bonus_image_upload_author_and_book(client):
    photo_data = (io.BytesIO(b"fake photo image bytes"), "author_photo.jpg")
    r_author = client.post("/authors/add",
                           data={"name": "Photo Author", "country": "Egypt", "photo": photo_data},
                           content_type="multipart/form-data",
                           follow_redirects=True)
    assert r_author.status_code == 200
    author = query("SELECT author_id, photo FROM author WHERE name = %s", ("Photo Author",), fetch="one")
    assert author["photo"] is not None
    assert author["photo"].endswith(".jpg")

    aid = author["author_id"]
    cover_data = (io.BytesIO(b"fake cover image bytes"), "book_cover.png")
    r_book = client.post("/books/add",
                         data={"title": "Photo Book", "price": "19.99", "author_id": str(aid), "cover": cover_data},
                         content_type="multipart/form-data",
                         follow_redirects=True)
    assert r_book.status_code == 200
    book = query("SELECT cover FROM book WHERE title = %s", ("Photo Book",), fetch="one")
    assert book["cover"] is not None
    assert book["cover"].endswith(".png")


# ---------------------------------------------------------------- Lab 2: Auth and Todos Tests
def register(c, name="Sara", email="sara@mail.com", pw="secret", confirm=None):
    return c.post("/register", data={"name": name, "email": email, "password": pw,
                                     "confirm_password": pw if confirm is None else confirm})


def login(c, email="sara@mail.com", pw="secret"):
    return c.post("/login", data={"email": email, "password": pw})


def test_todos_requires_login(client):
    r = client.get("/todos")
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")


def test_register_login_and_todos_workflow(client):
    r_reg = register(client, name="Sara", email="sara@mail.com", pw="pass123")
    assert r_reg.status_code == 302 and r_reg.headers["Location"].endswith("/todos")

    # Add a todo
    r_add = client.post("/todos/add", data={"title": "Read Database Chapter 3"}, follow_redirects=True)
    assert r_add.status_code == 200
    assert "Read Database Chapter 3" in r_add.get_data(as_text=True)

    # Edit todo
    todo = query("SELECT todo_id FROM todos LIMIT 1", fetch="one")
    tid = todo["todo_id"]
    r_edit = client.post(f"/todos/{tid}/edit", data={"title": "Read Chapter 3 and 4"}, follow_redirects=True)
    assert r_edit.status_code == 200
    assert "Read Chapter 3 and 4" in r_edit.get_data(as_text=True)

    # Toggle done
    client.post(f"/todos/{tid}/done", data={"is_done": "1"}, follow_redirects=True)
    assert query("SELECT is_done FROM todos WHERE todo_id = %s", (tid,), fetch="one")["is_done"] == 1

    # Delete todo
    client.post(f"/todos/{tid}/delete", follow_redirects=True)
    assert query("SELECT COUNT(*) n FROM todos WHERE todo_id = %s", (tid,), fetch="one")["n"] == 0
