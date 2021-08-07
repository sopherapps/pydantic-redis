"""Tests for the redis orm"""
from datetime import date

import pytest

from pydantic_redis.config import RedisConfig
from pydantic_redis.model import Model
from pydantic_redis.store import Store


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: str
    published_on: date
    in_stock: bool = True


books = [
    Book(
        title="Oliver Twist",
        author="Charles Dickens",
        published_on=date(year=1215, month=4, day=4),
        in_stock=False,
    ),
    Book(
        title="Great Expectations",
        author="Charles Dickens",
        published_on=date(year=1220, month=4, day=4),
    ),
    Book(
        title="Jane Eyre",
        author="Charles Dickens",
        published_on=date(year=1225, month=6, day=4),
        in_stock=False,
    ),
    Book(
        title="Wuthering Heights",
        author="Jane Austen",
        published_on=date(year=1600, month=4, day=4),
    ),
]


@pytest.fixture()
def redis_store(redis_server):
    """Sets up a redis store using the redis_server fixture and adds the book model to it"""
    store = Store(
        name="sample",
        redis_config=RedisConfig(password="password", db=1),  # nosec
        life_span_in_seconds=3600,
    )
    store.register_model(Book)
    yield store
    keys = [f"book_%&_{book.title}" for book in books]
    store.redis_store.delete(*keys)


class ModelWithoutPrimaryKey(Model):
    title: str


def test_register_model_without_primary_key(redis_store):
    """Throws error when a model without the _primary_key_field class variable set is registered"""
    with pytest.raises(AttributeError, match=r"_primary_key_field"):
        redis_store.register_model(ModelWithoutPrimaryKey)

    ModelWithoutPrimaryKey._primary_key_field = None

    with pytest.raises(Exception, match=r"should have a _primary_key_field"):
        redis_store.register_model(ModelWithoutPrimaryKey)


def test_store_model(redis_store):
    """Tests the model method in store"""
    assert redis_store.model("Book") == Book

    with pytest.raises(KeyError):
        redis_store.model("Notabook")


def test_bulk_insert(redis_store):
    """Providing a list of Model instances to the insert method inserts the records in redis"""
    keys = [f"book_%&_{book.title}" for book in books]
    redis_store.redis_store.delete(*keys)

    for key in keys:
        book_in_redis = redis_store.redis_store.hgetall(name=key)
        assert book_in_redis == {}

    Book.insert(books)

    pipeline = redis_store.redis_store.pipeline()
    for key in keys:
        pipeline.hgetall(name=key)
    books_in_redis = pipeline.execute()
    books_in_redis_as_models = [
        Book(**Book.deserialize_partially(book)) for book in books_in_redis
    ]
    assert books == books_in_redis_as_models


def test_insert_single(redis_store):
    """
    Providing a single Model instance
    """
    key = f"book_%&_{books[0].title}"
    book = redis_store.redis_store.hgetall(name=key)
    assert book == {}

    Book.insert(books[0])

    book = redis_store.redis_store.hgetall(name=key)
    book_as_model = Book(**Book.deserialize_partially(book))
    assert books[0] == book_as_model


def test_select_default(redis_store):
    """Selecting without arguments returns all the book models"""
    Book.insert(books)
    response = Book.select()
    sorted_books = sorted(books, key=lambda x: x.title)
    sorted_response = sorted(response, key=lambda x: x.title)
    assert sorted_books == sorted_response


def test_select_no_contents(redis_store):
    """Test that we get None when there are no models"""
    redis_store.redis_store.flushall()
    response = Book.select()

    assert response is None


def test_select_single_content(redis_store):
    """Check returns for a single instance"""
    redis_store.redis_store.flushall()
    Book.insert([books[1]])
    response = Book.select()
    assert len(response) == 1
    assert response[0] == books[1]


def test_select_some_columns(redis_store):
    """
    Selecting some columns returns a list of dictionaries of all books models with only those columns
    """
    Book.insert(books)
    books_dict = {book.title: book for book in books}
    columns = ["title", "author", "in_stock"]
    response = Book.select(columns=["title", "author", "in_stock"])
    response_dict = {book["title"]: book for book in response}

    for title, book in books_dict.items():
        book_in_response = response_dict[title]
        assert isinstance(book_in_response, dict)
        assert sorted(book_in_response.keys()) == sorted(columns)
        for column in columns:
            assert f"{book_in_response[column]}" == f"{getattr(book, column)}"


def test_select_some_ids(redis_store):
    """
    Selecting some ids returns only those elements with the given ids
    """
    Book.insert(books)
    ids = [book.title for book in books[:2]]
    response = Book.select(ids=ids)
    assert response == books[:2]


def test_update(redis_store):
    """
    Updating an item of a given primary key updates it in redis
    """
    Book.insert(books)
    title = books[0].title
    new_author = "John Doe"
    key = f"book_%&_{title}"
    old_book_data = redis_store.redis_store.hgetall(name=key)
    old_book = Book(**Book.deserialize_partially(old_book_data))
    assert old_book == books[0]
    assert old_book.author != new_author

    Book.update(_id=title, data={"author": "John Doe"})

    book_data = redis_store.redis_store.hgetall(name=key)
    book = Book(**Book.deserialize_partially(book_data))
    assert book.author == new_author
    assert book.title == old_book.title
    assert book.in_stock == old_book.in_stock
    assert book.published_on == old_book.published_on


def test_delete_single(redis_store):
    """Test deleting a single record"""
    Book.insert(books)
    book_to_delete = books[1]
    Book.delete(ids=book_to_delete.title)
    check_for_book = redis_store.redis_store.hgetall(name=book_to_delete.title)
    assert check_for_book == {}


def test_delete_multiple(redis_store):
    """
    Providing a list of ids to the delete function will remove the items from redis
    """
    Book.insert(books)
    books_to_delete = books[:2]
    books_left_in_db = books[2:]

    ids_to_delete = [book.title for book in books_to_delete]
    ids_to_leave_intact = [book.title for book in books_left_in_db]

    keys_to_delete = [f"book_%&_{_id}" for _id in ids_to_delete]
    keys_to_leave_intact = [f"book_%&_{_id}" for _id in ids_to_leave_intact]

    Book.delete(ids=ids_to_delete)

    for key in keys_to_delete:
        deleted_book_in_redis = redis_store.redis_store.hgetall(name=key)
        assert deleted_book_in_redis == {}

    pipeline = redis_store.redis_store.pipeline()
    for key in keys_to_leave_intact:
        pipeline.hgetall(name=key)
    books_in_redis = pipeline.execute()
    books_in_redis_as_models = [
        Book(**Book.deserialize_partially(book)) for book in books_in_redis
    ]
    assert books_left_in_db == books_in_redis_as_models
