import json

# Load JSON file
with open('library.json', 'r') as file:
    data = json.load(file)

# Loop through all books
for book in data['books']:
    book_id = book['book_id']
    title = book['title']
    author = book['author']
    genre = book['genre']
    publish_year = book['publish_year']
    isbn = book['isbn']
    available_copies = book['available_copies']

    # Use get() so it doesn't error when date_added is missing
    date_added = book.get('date_added', 'N/A')

    print(f"Book ID: {book_id}")
    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Genre: {genre}")
    print(f"Publish Year: {publish_year}")
    print(f"ISBN: {isbn}")
    print(f"Available Copies: {available_copies}")
    print(f"Date Added: {date_added}")
    print("-" * 25)
