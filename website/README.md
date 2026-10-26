# DB Lab 3 — Foreign Keys, Simple SQL & Library Application

A complete submission for **Lab 3: Foreign Keys and Simple SQL**, containing the SQL scripts, conceptual answers for referential integrity, and an enhanced full-stack web application continuing from Lab 2.

Built for *Introduction to Database Systems*, Alexandria National University, Faculty of Engineering, Fall 2026.

---

## 1. Team

| Name | ID | Contribution |
|------|----|--------------|
| **Amr Khalid Mohamed** | **2304120** | Implemented Problem 1 DDL & DML, solved and verified questions Q1.1–Q1.3, implemented Problem 2 DDL & DML with `ON DELETE CASCADE`, built the Library website extensions (F2.1–F2.5), added the image upload bonus (book covers & author photos), and automated test suites. |
| **Seif Eldin Walid Ibrahim** | **2404028** | Partnered on backend and database integration, schema design and referential integrity testing, web route verification, bonus image upload validation, and documentation. |

---

## 2. Deliverables Structure

Deliverables are organized in this repository according to the lab specification:

```
db-lab3-Seif-Walid-and-Amr-khalid/
├── problem1_DDL.sql      # DDL scripts for database 'company' (Problem 1)
├── problem1_DML.sql      # INSERT queries: at least 3 records in each table (Problem 1)
├── problem1_Answers.txt  # SQL used and exact MySQL output/error for Q1.1–Q1.3
├── problem2_DDL.sql      # DDL scripts for database 'library' (Problem 2)
├── problem2_DML.sql      # Seed data (INSERT): 4 authors and 7 books (Problem 2)
├── website/              # Full Lab 2 website extended with Library features
│   ├── app.py            # Flask server: routes, validation, plain SQL
│   ├── database/         # Re-runnable schema DDL
│   ├── templates/        # Base, books, authors, book_form, author_form, todos, auth
│   ├── static/           # style.css, validate.js, uploads/ (with seed images)
│   ├── tests/            # Automated pytest suite (13 passing tests)
│   ├── requirements.txt  # Dependencies
│   └── .env.example      # Example environment configuration
└── README.md             # This step-by-step guide
```

---

## 3. Quick Start & Execution Guide

### Prerequisites
- MySQL Server 8.0+
- Python 3.10+ and pip

---

### Part I: Problem 1 — The COMPANY Database

1. **Build the database and tables**:
   ```bash
   mysql -u root -p < problem1_DDL.sql
   ```
   *Creates database `company` with tables `EMPLOYEE`, `DEPARTMENT`, and `PROJECT` with primary keys and foreign keys.*

2. **Insert the rows**:
   ```bash
   mysql -u root -p < problem1_DML.sql
   ```
   *Inserts 4 employees, 3 departments, and 4 projects while respecting foreign key constraints.*

3. **Verify the data in MySQL**:
   ```bash
   mysql -u root -p company
   ```
   ```sql
   SELECT * FROM EMPLOYEE;
   SELECT * FROM DEPARTMENT;
   SELECT * FROM PROJECT;
   ```

4. **Questions Q1.1–Q1.3 Answers**:
   See `problem1_Answers.txt` for the full SQL and exact error messages produced by MySQL:
   - **Q1.1**: Deleting a referenced employee fails with `ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails` due to referential integrity (RESTRICT).
   - **Q1.2**: Inserting a project referencing a nonexistent department fails with `ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails`.
   - **Q1.3**: When both foreign keys are `NOT NULL`, a circular dependency occurs. In MySQL, disable foreign key checks temporarily:
     ```sql
     SET FOREIGN_KEY_CHECKS = 0;
     -- Insert employee and department
     SET FOREIGN_KEY_CHECKS = 1;
     ```
     Alternatively, add the foreign key constraint or NOT NULL constraint using `ALTER TABLE` after initial rows are inserted.

---

### Part II: Problem 2 — Library: Books and Authors

1. **Build the library database and tables**:
   ```bash
   mysql -u root -p < problem2_DDL.sql
   ```
   *Creates database `library` with tables `author` and `book`. Defines `FOREIGN KEY (author_id) REFERENCES author(author_id) ON DELETE CASCADE`.*

2. **Insert seed data**:
   ```bash
   mysql -u root -p < problem2_DML.sql
   ```
   *Seeds 4 authors and 7 books (exceeding the required 3 authors and 6 books).*

---

### Part III: Running the Website

1. **Navigate to the website directory**:
   ```bash
   cd website
   ```

2. **Set up a Python virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate       # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Copy `.env.example` to `.env` and fill in your MySQL credentials:
   ```bash
   cp .env.example .env
   ```
   Example `.env` settings:
   ```env
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=root
   DB_NAME=library
   SECRET_KEY=change-this-to-a-random-secret
   ```

4. **Start the Flask server**:
   ```bash
   python app.py
   ```

5. **Open in browser**:
   Navigate to <http://127.0.0.1:5000>.

---

## 4. Website Features Breakdown

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **F2.1: Show Books Table** | Displays all books including book cover thumbnail, ID, Title, Price (`$XX.XX`), and `author_id` alongside author name. | `GET /books` -> `templates/books.html` |
| **F2.1: Show Authors Table** | Displays all authors including photo avatar, ID, Name, Country, and total books count. | `GET /authors` -> `templates/authors.html` |
| **F2.2: Add Book** | Form to add a book (Title, Price, Author dropdown selecting `author_id`, and Cover file upload). Validates server-side and client-side. | `GET / POST /books/add` -> `templates/book_form.html` |
| **F2.2: Add Author** | Form to add an author (Name, Country, and Photo file upload). Validates non-empty name. | `GET / POST /authors/add` -> `templates/author_form.html` |
| **F2.3: Edit Book** | Pre-filled form to update book title, price, author, and optional new cover image. | `GET / POST /books/<id>/edit` -> `templates/book_form.html` |
| **F2.3: Edit Author** | Pre-filled form to update author name, country, and optional new photo. | `GET / POST /authors/<id>/edit` -> `templates/author_form.html` |
| **F2.4: Remove a Book** | Deletes a book row from the table with a confirmation prompt. | `POST /books/<id>/delete` |
| **F2.5: Remove an Author (CASCADE)** | Deletes an author row. Triggers MySQL `ON DELETE CASCADE` to automatically delete all books belonging to that author. Confirmation dialog warns the user about cascade deletion. | `POST /authors/<id>/delete` |
| **Bonus: Image Uploads** | Upload book cover images and author photos. Files are safely stored in `static/uploads/`, unique filenames are generated, and image thumbnails/previews are rendered on the website. Seed images are pre-included. | `save_upload()`, `static/uploads/` |
| **Lab 2 Retained Features** | User registration with bcrypt hashing, login/logout sessions, personal to-do list (add, edit, toggle done, delete), client-side validation (`validate.js`), dark mode, and responsive layout. | `GET /todos`, `POST /login`, `POST /register` |

---

## 5. SQL Queries Used by the Website

All queries are executed with plain SQL using `%s` parameters (no ORM):

### Problem 2 Queries:
```sql
-- F2.1: Fetch books and authors
SELECT book_id, title, price, author_id, cover FROM book ORDER BY book_id ASC;
SELECT author_id, name, country, photo FROM author ORDER BY author_id ASC;

-- F2.2: Insert new author and book
INSERT INTO author (name, country, photo) VALUES (%s, %s, %s);
INSERT INTO book (title, price, author_id, cover) VALUES (%s, %s, %s, %s);

-- F2.3: Update author and book
UPDATE author SET name = %s, country = %s, photo = %s WHERE author_id = %s;
UPDATE book SET title = %s, price = %s, author_id = %s, cover = %s WHERE book_id = %s;

-- F2.4 & F2.5: Delete book and author (author deletion cascades to books)
DELETE FROM book WHERE book_id = %s;
DELETE FROM author WHERE author_id = %s;
```

---

## 6. Automated Testing

The project includes an automated test suite verifying all Problem 2 features, foreign key constraints, cascade deletion, image uploads, and Lab 2 backwards compatibility.

To run tests:
```bash
cd website
python -m pytest -v
```

**Results (13/13 passing):**
- `test_authors_page_empty`: Verifies author table view
- `test_add_author_success`: Verifies adding an author with country
- `test_add_author_validation_empty_name`: Verifies rejection of blank names
- `test_edit_author`: Verifies author editing and updates
- `test_books_page_empty`: Verifies book table view
- `test_add_book_success`: Verifies adding a book linked to an author
- `test_add_book_validation`: Verifies validation of title, price, and author
- `test_edit_book`: Verifies updating book details
- `test_delete_book`: Verifies removing a book
- `test_delete_author_cascades_books`: **Verifies foreign key `ON DELETE CASCADE`**
- `test_bonus_image_upload_author_and_book`: **Verifies image upload functionality**
- `test_todos_requires_login`: Verifies route protection
- `test_register_login_and_todos_workflow`: Verifies complete auth and todo flow
