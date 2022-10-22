import socket
from datetime import date
from typing import Set, Tuple, List

import pytest
import redislite
from pytest_lazyfixture import lazy_fixture

from pydantic_redis import Store, RedisConfig, Model


class Author(Model):
    _primary_key_field: str = 'name'
    name: str
    active_years: Tuple[int, int]


class Book(Model):
    _primary_key_field: str = 'title'
    title: str
    author: Author
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


class Library(Model):
  # the _primary_key_field is mandatory
  _primary_key_field: str = 'name'
  name: str
  address: str
  books: List[Book]

class BooksToRead(Model):
 _primary_key_field: str = 'name'
 name: str
 books: Set[Book]

class BooksBasket(Model):
 _primary_key_field: str = 'name'
 name: str
 books: Tuple[Book, ...]


authors = {
    "charles": Author(name="Charles Dickens", active_years=(1220, 1280)),
    "jane": Author(name="Jane Austen", active_years=(1580, 1640)),
}

books = [
    Book(title="Oliver Twist", author=authors["charles"], published_on=date(year=1215, month=4, day=4),
         in_stock=False, rating=2, tags=["Classic"]),
    Book(title="Great Expectations", author=authors["charles"], published_on=date(year=1220, month=4, day=4), rating=5,
         tags=["Classic"]),
    Book(title="Jane Eyre", author=authors["charles"], published_on=date(year=1225, month=6, day=4), in_stock=False,
         rating=3.4, tags=["Classic", "Romance"]),
    Book(title="Wuthering Heights", author=authors["jane"], published_on=date(year=1600, month=4, day=4), rating=4.0,
         tags=["Classic", "Romance"]),
]

library = Library(name='Babel Library', address='In a book', books=books)

books_to_read = BooksToRead(name='Book of Charles', books={books[0], books[1], books[2]})

books_basket = BooksBasket(name='Shopping from the library', books=(books[0], books[2], books[3]))

redis_store_fixture = [(lazy_fixture("redis_store"))]
books_fixture = [(lazy_fixture("redis_store"), book) for book in books]
library_fixture = [(lazy_fixture("redis_store"), library)]
update_books_fixture = [
    (lazy_fixture("redis_store"), book.title, {"author": authors["jane"], "in_stock": not book.in_stock})
    for book in books
]
delete_books_fixture = [(lazy_fixture("redis_store"), book.title) for book in books]


@pytest.fixture()
def unused_tcp_port():
    """Creates an unused TCP port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = f"{sock.getsockname()[1]}"
    sock.close()
    yield port


@pytest.fixture()
def redis_server(unused_tcp_port):
    """Sets up a fake redis server we can use for tests"""
    instance = redislite.Redis(serverconfig={"port": unused_tcp_port})
    yield unused_tcp_port
    instance.shutdown()


@pytest.fixture()
def redis_store(redis_server):
    """Sets up a redis store using the redis_server fixture and adds the book model to it"""
    store = Store(
        name="sample",
        redis_config=RedisConfig(port=redis_server, db=1),
        life_span_in_seconds=3600,
    )
    store.register_model(Book)
    store.register_model(Author)
    store.register_model(Library)
    store.register_model(BooksToRead)
    store.register_model(BooksBasket)
    yield store
    store.redis_store.flushall()
