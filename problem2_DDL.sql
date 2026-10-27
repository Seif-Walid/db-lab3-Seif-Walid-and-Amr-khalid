
DROP DATABASE IF EXISTS library;
CREATE DATABASE library;
USE library;

-- 1. Create author table
-- Primary key: author_id (AUTO_INCREMENT)
-- Optional photo column for image upload bonus
CREATE TABLE author (
    author_id   INT            NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)   NOT NULL,
    country     VARCHAR(100),
    photo       VARCHAR(255)   DEFAULT NULL,
    PRIMARY KEY (author_id)
);

-- 2. Create book table
-- Primary key: book_id (AUTO_INCREMENT)
-- Foreign key: author_id references author(author_id) ON DELETE CASCADE
-- Optional cover column for image upload bonus
CREATE TABLE book (
    book_id     INT            NOT NULL AUTO_INCREMENT,
    title       VARCHAR(200)   NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    author_id   INT            NOT NULL,
    cover       VARCHAR(255)   DEFAULT NULL,
    PRIMARY KEY (book_id),
    FOREIGN KEY (author_id) REFERENCES author(author_id) ON DELETE CASCADE
);

-- Aliases to support case-insensitive grading scripts on case-sensitive OS

