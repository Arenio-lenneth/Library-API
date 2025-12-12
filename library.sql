-- Create database and tables for Library-API
);


-- Books
CREATE TABLE IF NOT EXISTS books (
book_id INT AUTO_INCREMENT PRIMARY KEY,
title VARCHAR(200) NOT NULL,
author_id INT,
genre VARCHAR(100),
publish_year INT,
isbn VARCHAR(50),
available_copies INT DEFAULT 1,
FOREIGN KEY (author_id) REFERENCES authors(author_id)
);


-- Users (for authentication)
CREATE TABLE IF NOT EXISTS users (
user_id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(100) UNIQUE NOT NULL,
password VARCHAR(255) NOT NULL,
role VARCHAR(50) DEFAULT 'user'
);


-- Insert sample authors (10)
INSERT INTO authors (author_id, first_name, last_name, birth_year) VALUES
(1, 'J.K.', 'Rowling', 1965),
(2, 'George', 'Orwell', 1903),
(3, 'Harper', 'Lee', 1926),
(4, 'F. Scott', 'Fitzgerald', 1896),
(5, 'J.D.', 'Salinger', 1919),
(6, 'Jane', 'Austen', 1775),
(7, 'J.R.R.', 'Tolkien', 1892),
(8, 'Paulo', 'Coelho', 1947),
(9, 'Dan', 'Brown', 1964),
(10, 'Suzanne', 'Collins', 1962);


-- Insert sample books (20)
INSERT INTO books (title, author_id, genre, publish_year, isbn, available_copies) VALUES
('Harry Potter and the Chamber of Secrets', 1, 'Fantasy', 1998, '978-0439064873', 4),
('Harry Potter and the Prisoner of Azkaban', 1, 'Fantasy', 1999, '978-0439136365', 6),
('Harry Potter and the Goblet of Fire', 1, 'Fantasy', 2000, '978-0439139595', 5),
('1984', 2, 'Dystopian', 1949, '978-0451524935', 3),
('Animal Farm', 2, 'Political Satire', 1945, '978-0451526342', 2),
('To Kill a Mockingbird', 3, 'Fiction', 1960, '978-0061120084', 3),
('Go Set a Watchman', 3, 'Fiction', 2015, '978-0062409850', 2),
('The Great Gatsby', 4, 'Classic', 1925, '978-0743273565', 4),
('The Catcher in the Rye', 5, 'Fiction', 1951, '978-0316769488', 3),
('Pride and Prejudice', 6, 'Romance', 1813, '978-0141439518', 5),
('Sense and Sensibility', 6, 'Romance', 1811, '978-0141439662', 4),
('The Hobbit', 7, 'Fantasy', 1937, '978-0547928227', 6),
('The Lord of the Rings: The Fellowship of the Ring', 7, 'Fantasy', 1954, '978-0547928210', 5),
('The Lord of the Rings: The Two Towers', 7, 'Fantasy', 1954, '978-0547928203', 5),
('The Lord of the Rings: The Return of the King', 7, 'Fantasy', 1955, '978-0547928197', 5),
('The Alchemist', 8, 'Adventure', 1988, '978-0062315007', 4),
('The Da Vinci Code', 9, 'Thriller', 2003, '978-0307474278', 3),
('Angels & Demons', 9, 'Thriller', 2000, '978-0671027360', 3),
('The Hunger Games', 10, 'Dystopian', 2008, '978-0439023481', 6),
('Catching Fire', 10, 'Dystopian', 2009, '978-0439023498', 5);


-- Insert admin user (password hashed with bcrypt for `admin123`)
-- Password hash generated with bcrypt: $2b$12$hhy7o1G0LgJV1B1FMyc1FeGJgEuLC2blPIpoJ0qu48MPwSkgCiY6K
INSERT INTO users (username, password, role) VALUES
('admin', '$2b$12$hhy7o1G0LgJV1B1FMyc1FeGJgEuLC2blPIpoJ0qu48MPwSkgCiY6K', 'admin');