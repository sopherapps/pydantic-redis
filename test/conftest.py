import socket
from datetime import date
from typing import Tuple, List, Optional, Dict

import pytest
import pytest_asyncio
import redislite
from pytest_lazyfixture import lazy_fixture

from pydantic_redis import syncio as syn, asyncio as asy


aio_pytest_fixture = getattr(pytest_asyncio, "fixture", pytest.fixture())


class Author(syn.Model):
    _primary_key_field: str = "name"
    name: str
    active_years: Tuple[int, int]
    genre: Optional[str] = None


class AsyncAuthor(asy.Model):
    _primary_key_field: str = "name"
    name: str
    active_years: Tuple[int, int]
    genre: Optional[str] = None


class Book(syn.Model):
    _primary_key_field: str = "title"
    title: str
    author: Author
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


class AsyncBook(asy.Model):
    _primary_key_field: str = "title"
    title: str
    author: AsyncAuthor
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


class Library(syn.Model):
    # the _primary_key_field is mandatory
    _primary_key_field: str = "name"
    name: str
    address: str
    books: List[Book] = []
    lost: Optional[List[Book]] = None
    popular: Optional[Tuple[Book, Book]] = None
    new: Optional[Tuple[Book, Author, Book, int]] = None
    list_of_tuples: Optional[List[Tuple[str, Book]]] = None
    dict_of_models: Optional[Dict[str, Book]] = None
    optional_nested: Optional[Book] = None


class AsyncLibrary(asy.Model):
    # the _primary_key_field is mandatory
    _primary_key_field: str = "name"
    name: str
    address: str
    books: List[AsyncBook] = []
    lost: Optional[List[AsyncBook]] = None
    popular: Optional[Tuple[AsyncBook, AsyncBook]] = None
    new: Optional[Tuple[AsyncBook, AsyncAuthor, AsyncBook, int]] = None


authors = {
    "charles": Author(name="Charles Dickens", active_years=(1220, 1280)),
    "jane": Author(name="Jane Austen", active_years=(1580, 1640), genre="romance"),
}

async_authors = {
    "charles": AsyncAuthor(name="Charles Dickens", active_years=(1220, 1280)),
    "jane": AsyncAuthor(name="Jane Austen", active_years=(1580, 1640), genre="romance"),
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

async_books = [
    AsyncBook(
        title="Oliver Twist",
        author=async_authors["charles"],
        published_on=date(year=1215, month=4, day=4),
        in_stock=False,
        rating=2,
        tags=["Classic"],
    ),
    AsyncBook(
        title="Great Expectations",
        author=async_authors["charles"],
        published_on=date(year=1220, month=4, day=4),
        rating=5,
        tags=["Classic"],
    ),
    AsyncBook(
        title="Jane Eyre",
        author=async_authors["charles"],
        published_on=date(year=1225, month=6, day=4),
        in_stock=False,
        rating=3.4,
        tags=["Classic", "Romance"],
    ),
    AsyncBook(
        title="Wuthering Heights",
        author=async_authors["jane"],
        published_on=date(year=1600, month=4, day=4),
        rating=4.0,
        tags=["Classic", "Romance"],
    ),
]

# sync fixtures
redis_store_fixture = [(lazy_fixture("redis_store"))]
books_fixture = [(lazy_fixture("redis_store"), book) for book in books]
update_books_fixture = [
    (
        lazy_fixture("redis_store"),
        book.title,
        {"author": authors["jane"], "in_stock": not book.in_stock},
    )
    for book in books[-1:]
]
delete_books_fixture = [
    (lazy_fixture("redis_store"), book.title) for book in books[-1:]
]

# async fixtures
async_redis_store_fixture = [(lazy_fixture("async_redis_store"))]


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
    store = syn.Store(
        name="sample",
        redis_config=syn.RedisConfig(port=redis_server, db=1),
        life_span_in_seconds=3600,
    )
    store.register_model(Book)
    store.register_model(Author)
    store.register_model(Library)
    yield store
    store.redis_store.flushall()


@aio_pytest_fixture
async def async_redis_store(redis_server):
    """Sets up a redis store using the redis_server fixture and adds the book model to it"""
    store = asy.Store(
        name="sample",
        redis_config=syn.RedisConfig(port=redis_server, db=1),
        life_span_in_seconds=3600,
    )
    store.register_model(AsyncBook)
    store.register_model(AsyncAuthor)
    store.register_model(AsyncLibrary)
    yield store
    await store.redis_store.flushall()
