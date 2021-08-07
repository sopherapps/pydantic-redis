"""Tests for the redis orm"""
from datetime import date

import pytest

from pydantic_aioredis.config import RedisConfig
from pydantic_aioredis.model import Model
from pydantic_aioredis.store import Store


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
async def redis_store(redis_server):
    """Sets up a redis store using the redis_server fixture and adds the book model to it"""
    store = Store(
        name="sample",
        redis_config=RedisConfig(port=redis_server, db=1),  # nosec
        life_span_in_seconds=3600,
    )
    store.register_model(Book)
    yield store
    keys = [f"book_%&_{book.title}" for book in books]
    await store.redis_store.delete(*keys)


class ModelWithoutPrimaryKey(Model):
    title: str


def test_redis_config_redis_url():
    password = "password"
    config_with_no_pass = RedisConfig()
    config_with_ssl = RedisConfig(ssl=True)
    config_with_pass = RedisConfig(password=password)
    config_with_pass_ssl = RedisConfig(ssl=True, password=password)

    assert config_with_no_pass.redis_url == "redis://localhost:6379/0"
    assert config_with_ssl.redis_url == "rediss://localhost:6379/0"
    assert config_with_pass.redis_url == f"redis://:{password}@localhost:6379/0"
    assert config_with_pass_ssl.redis_url == f"rediss://:{password}@localhost:6379/0"


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


@pytest.mark.asyncio
async def test_bulk_insert(redis_store):
    """Providing a list of Model instances to the insert method inserts the records in redis"""
    keys = [f"book_%&_{book.title}" for book in books]
    await redis_store.redis_store.delete(*keys)

    for key in keys:
        book_in_redis = await redis_store.redis_store.hgetall(name=key)
        assert book_in_redis == {}

    await Book.insert(books)

    async with redis_store.redis_store.pipeline() as pipeline:
        for key in keys:
            pipeline.hgetall(name=key)
        books_in_redis = await pipeline.execute()
    books_in_redis_as_models = [
        Book(**Book.deserialize_partially(book)) for book in books_in_redis
    ]
    assert books == books_in_redis_as_models


@pytest.mark.asyncio
async def test_insert_single(redis_store):
    """
    Providing a single Model instance
    """
    key = f"book_%&_{books[0].title}"
    book = await redis_store.redis_store.hgetall(name=key)
    assert book == {}

    await Book.insert(books[0])

    book = await redis_store.redis_store.hgetall(name=key)
    book_as_model = Book(**Book.deserialize_partially(book))
    assert books[0] == book_as_model


@pytest.mark.asyncio
async def test_select_default(redis_store):
    """Selecting without arguments returns all the book models"""
    await Book.insert(books)
    response = await Book.select()
    sorted_books = sorted(books, key=lambda x: x.title)
    sorted_response = sorted(response, key=lambda x: x.title)
    assert sorted_books == sorted_response


@pytest.mark.asyncio
async def test_select_no_contents(redis_store):
    """Test that we get None when there are no models"""
    await redis_store.redis_store.flushall()
    response = await Book.select()

    assert response is None


@pytest.mark.asyncio
async def test_select_single_content(redis_store):
    """Check returns for a single instance"""
    # await redis_store.redis_store.flushall()
    await Book.insert([books[1]])
    response = await Book.select()
    assert len(response) == 1
    assert response[0] == books[1]

    books_dict = {book.title: book for book in books}
    response = await Book.select(columns=["title", "author", "in_stock"])

    assert response[0]["title"] == books[1].title
    assert response[0]["author"] == books[1].author
    assert response[0]["in_stock"] == str(books[1].in_stock)
    with pytest.raises(KeyError):
        response[0]["published_on"]


@pytest.mark.asyncio
async def test_select_some_columns(redis_store):
    """
    Selecting some columns returns a list of dictionaries of all books models with only those columns
    """
    await Book.insert(books)
    books_dict = {book.title: book for book in books}
    columns = ["title", "author", "in_stock"]
    response = await Book.select(columns=["title", "author", "in_stock"])
    response_dict = {book["title"]: book for book in response}

    for title, book in books_dict.items():
        book_in_response = response_dict[title]
        assert isinstance(book_in_response, dict)
        assert sorted(book_in_response.keys()) == sorted(columns)
        for column in columns:
            assert f"{book_in_response[column]}" == f"{getattr(book, column)}"


@pytest.mark.asyncio
async def test_select_some_ids(redis_store):
    """
    Selecting some ids returns only those elements with the given ids
    """
    await Book.insert(books)
    ids = [book.title for book in books[:2]]
    response = await Book.select(ids=ids)
    assert response == books[:2]


@pytest.mark.asyncio
async def test_select_bad_id(redis_store):
    """
    Selecting some ids returns only those elements with the given ids
    """
    await Book.insert(books)
    response = await Book.select(ids=["Not in there"])
    assert response is None


@pytest.mark.asyncio
async def test_update(redis_store):
    """
    Updating an item of a given primary key updates it in redis
    """
    await Book.insert(books)
    title = books[0].title
    new_author = "John Doe"
    key = f"book_%&_{title}"
    old_book_data = await redis_store.redis_store.hgetall(name=key)
    old_book = Book(**Book.deserialize_partially(old_book_data))
    assert old_book == books[0]
    assert old_book.author != new_author

    await Book.update(_id=title, data={"author": "John Doe"})

    book_data = await redis_store.redis_store.hgetall(name=key)
    book = Book(**Book.deserialize_partially(book_data))
    assert book.author == new_author
    assert book.title == old_book.title
    assert book.in_stock == old_book.in_stock
    assert book.published_on == old_book.published_on


@pytest.mark.asyncio
async def test_delete_single(redis_store):
    """Test deleting a single record"""
    await Book.insert(books)
    book_to_delete = books[1]
    await Book.delete(ids=book_to_delete.title)
    check_for_book = await redis_store.redis_store.hgetall(name=book_to_delete.title)
    assert check_for_book == {}


@pytest.mark.asyncio
async def test_delete_multiple(redis_store):
    """
    Providing a list of ids to the delete function will remove the items from redis
    """
    await Book.insert(books)
    books_to_delete = books[:2]
    books_left_in_db = books[2:]

    ids_to_delete = [book.title for book in books_to_delete]
    ids_to_leave_intact = [book.title for book in books_left_in_db]

    keys_to_delete = [f"book_%&_{_id}" for _id in ids_to_delete]
    keys_to_leave_intact = [f"book_%&_{_id}" for _id in ids_to_leave_intact]

    await Book.delete(ids=ids_to_delete)

    for key in keys_to_delete:
        deleted_book_in_redis = await redis_store.redis_store.hgetall(name=key)
        assert deleted_book_in_redis == {}

    async with redis_store.redis_store.pipeline() as pipeline:
        for key in keys_to_leave_intact:
            pipeline.hgetall(name=key)
        books_in_redis = await pipeline.execute()
    books_in_redis_as_models = [
        Book(**Book.deserialize_partially(book)) for book in books_in_redis
    ]
    assert books_left_in_db == books_in_redis_as_models
