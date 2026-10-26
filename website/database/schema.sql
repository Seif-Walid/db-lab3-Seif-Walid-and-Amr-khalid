-- ============================================================================
-- DB Lab 3 - Library & To-Do Application Schema
-- Re-runnable DDL script: drops and rebuilds database 'library'
-- ============================================================================

DROP DATABASE IF EXISTS library;
CREATE DATABASE library;
USE library;

-- ----------------------------------------------------------------------------
-- PART II - Problem 2: Books and Authors
-- ----------------------------------------------------------------------------
CREATE TABLE author (
    author_id   INT            NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)   NOT NULL,
    country     VARCHAR(100),
    photo       VARCHAR(255)   DEFAULT NULL,
    PRIMARY KEY (author_id)
);

CREATE TABLE book (
    book_id     INT            NOT NULL AUTO_INCREMENT,
    title       VARCHAR(200)   NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    author_id   INT            NOT NULL,
    cover       VARCHAR(255)   DEFAULT NULL,
    PRIMARY KEY (book_id),
    FOREIGN KEY (author_id) REFERENCES author(author_id) ON DELETE CASCADE
);

-- Case aliases for cross-platform compatibility
CREATE OR REPLACE VIEW AUTHOR AS SELECT * FROM author;
CREATE OR REPLACE VIEW BOOK AS SELECT * FROM book;

-- ----------------------------------------------------------------------------
-- Lab 2 Components: Users and To-Dos
-- ----------------------------------------------------------------------------
CREATE TABLE users (
    user_id           INT          NOT NULL AUTO_INCREMENT,
    email             VARCHAR(255) NOT NULL,
    name              VARCHAR(100) NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE (email)
);

CREATE TABLE todos (
    todo_id    INT          NOT NULL AUTO_INCREMENT,
    user_id    INT          NOT NULL,
    title      VARCHAR(200) NOT NULL,
    is_done    TINYINT(1)   NOT NULL DEFAULT 0,
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (todo_id),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);
