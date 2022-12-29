import pprint
from datetime import date
from typing import Tuple, List
from pydantic_redis import RedisConfig, Model, Store


class Author(Model):
    _primary_key_field: str = "name"
    name: str
    active_years: Tuple[int, int]


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: Author
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(
        name="some_name",
        redis_config=RedisConfig(db=5, host="localhost", port=6379),
        life_span_in_seconds=3600,
    )

    store.register_model(Book)
    store.register_model(Author)

    authors = {
        "charles": Author(name="Charles Dickens", active_years=(1220, 1280)),
        "jane": Author(name="Jane Austen", active_years=(1580, 1640)),
    }

    books = [
        Book(
            title="Oliver Twist",
            author=authors["charles"],
            published_on=date(year=1215, month=4, day=4),
            in_stock=False,
            rating=2,
            tags=["Classic"],
        ),
        Book(
            title="Great Expectations",
            author=authors["charles"],
            published_on=date(year=1220, month=4, day=4),
            rating=5,
            tags=["Classic"],
        ),
        Book(
            title="Jane Eyre",
            author=authors["charles"],
            published_on=date(year=1225, month=6, day=4),
            in_stock=False,
            rating=3.4,
            tags=["Classic", "Romance"],
        ),
        Book(
            title="Wuthering Heights",
            author=authors["jane"],
            published_on=date(year=1600, month=4, day=4),
            rating=4.0,
            tags=["Classic", "Romance"],
        ),
    ]

    Book.insert(books, life_span_seconds=3600)
    all_books = Book.select()
    paginated_books = Book.select(skip=2, limit=2)
    paginated_books_with_few_fields = Book.select(
        columns=["author", "in_stock"], skip=2, limit=2
    )
    print("All:")
    pp.pprint(all_books)
    print("\nPaginated:")
    pp.pprint(paginated_books)
    print("\nPaginated but with few fields:")
    pp.pprint(paginated_books_with_few_fields)
