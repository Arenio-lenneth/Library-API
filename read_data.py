import json

with open('library.json', 'r') as file:
    data = json.load(file)

for book in data['library_db']:
    book_id = book['book_id']
    title = book['title']
    author = book['author']
    year = book['year']
    genre = book.get('genre', 'N/A')
    date = book.get('date', 'N/A')

    print(f"Book ID: {book_id}")
    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Year: {year}")
    print(f"Genre: {genre}")
    print(f"Date Added: {date}")
    print("-" * 20)

