
USE library;

-- 1. Insert seed data into author (4 authors: exceeds required 3)
INSERT INTO author (author_id, name, country, photo) VALUES
(1, 'Naguib Mahfouz', 'Egypt', 'naguib_mahfouz.jpg'),
(2, 'Taha Hussein', 'Egypt', 'taha_hussein.jpg'),
(3, 'George Orwell', 'United Kingdom', 'george_orwell.jpg'),
(4, 'Gabriel Garcia Marquez', 'Colombia', 'marquez.jpg');

-- 2. Insert seed data into book (7 books: exceeds required 6)
INSERT INTO book (book_id, title, price, author_id, cover) VALUES
(1, 'Palace Walk', 15.50, 1, 'palace_walk.jpg'),
(2, 'The Thief and the Dogs', 12.00, 1, 'thief_and_dogs.jpg'),
(3, 'The Days', 14.00, 2, 'the_days.jpg'),
(4, 'A Man of Letters', 11.50, 2, 'man_of_letters.jpg'),
(5, '1984', 18.00, 3, '1984.jpg'),
(6, 'Animal Farm', 10.50, 3, 'animal_farm.jpg'),
(7, 'One Hundred Years of Solitude', 22.00, 4, 'solitude.jpg');
