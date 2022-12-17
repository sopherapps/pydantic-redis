"""Tests for the redis orm"""
from collections import namedtuple
from typing import Dict, Any

import pytest

from pydantic_redis.shared.model.prop_utils import NESTED_MODEL_PREFIX
from pydantic_redis.shared.utils import strip_leading
from pydantic_redis.asyncio import Model, RedisConfig
from test.conftest import (
    async_redis_store_fixture,
    AsyncBook,
    async_books,
    AsyncAuthor,
    async_authors,
    AsyncLibrary,
)


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


def test_register_model_without_primary_key(async_redis_store):
    """Throws error when a model without the _primary_key_field class variable set is registered"""

    class ModelWithoutPrimaryKey(Model):
        title: str

    with pytest.raises(AttributeError, match=r"_primary_key_field"):
        async_redis_store.register_model(ModelWithoutPrimaryKey)

    ModelWithoutPrimaryKey._primary_key_field = None

    with pytest.raises(Exception, match=r"should have a _primary_key_field"):
        async_redis_store.register_model(ModelWithoutPrimaryKey)


def test_store_model(async_redis_store):
    """Tests the model method in store"""
    assert async_redis_store.model("AsyncBook") == AsyncBook

    with pytest.raises(KeyError):
        async_redis_store.model("Notabook")


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_bulk_insert(store):
    """Providing a list of Model instances to the insert method inserts the records in redis"""
    book_keys = [f"asyncbook_%&_{book.title}" for book in async_books]
    keys = book_keys + [
        f"asyncauthor_%&_{author.name}" for author in async_authors.values()
    ]
    await store.redis_store.delete(*keys)

    for key in keys:
        item_in_redis = await store.redis_store.hgetall(name=key)
        assert item_in_redis == {}

    await AsyncBook.insert(async_books)

    async with store.redis_store.pipeline() as pipeline:
        for book_key in book_keys:
            pipeline.hgetall(name=book_key)
        async_books_in_redis = await pipeline.execute()

    async_books_in_redis_as_models = [
        await __deserialize_book_data(book) for book in async_books_in_redis
    ]
    assert async_books == async_books_in_redis_as_models


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_bulk_nested_insert(store):
    """Providing a list of Model instances to the insert method also upserts their nested records in redis"""
    book_keys = [f"asyncbook_%&_{book.title}" for book in async_books]
    author_keys = [f"asyncauthor_%&_{author.name}" for author in async_authors.values()]
    keys = book_keys + author_keys

    for key in keys:
        item_in_redis = await store.redis_store.hgetall(name=key)
        assert item_in_redis == {}

    await AsyncBook.insert(async_books)

    async with store.redis_store.pipeline() as pipeline:
        for key in author_keys:
            pipeline.hgetall(name=key)
        async_authors_in_redis = await pipeline.execute()
    async_authors_in_redis_as_models = sorted(
        [
            AsyncAuthor(**AsyncAuthor.deserialize_partially(author))
            for author in async_authors_in_redis
        ],
        key=lambda x: x.name,
    )
    expected = sorted(async_authors.values(), key=lambda x: x.name)
    assert expected == async_authors_in_redis_as_models


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_insert_single(store):
    """
    Providing a single Model instance inserts that record in redis
    """
    key = f"asyncbook_%&_{async_books[0].title}"
    book = await store.redis_store.hgetall(name=key)
    assert book == {}

    await AsyncBook.insert(async_books[0])

    book = await store.redis_store.hgetall(name=key)
    book_as_model = await __deserialize_book_data(book)
    assert async_books[0] == book_as_model


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_insert_single_nested(store):
    """
    Providing a single Model instance upserts also any nested model into redis
    """
    key = f"asyncauthor_%&_{async_books[0].author.name}"
    author = await store.redis_store.hgetall(name=key)
    assert author == {}

    await AsyncBook.insert(async_books[0])

    author = await store.redis_store.hgetall(name=key)
    author_as_model = AsyncAuthor(**AsyncAuthor.deserialize_partially(author))
    assert async_books[0].author == author_as_model


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update_nested_list_of_models(store):
    data = [
        AsyncLibrary(name="Babel AsyncLibrary", address="In a book", books=async_books)
    ]
    await AsyncLibrary.insert(data)
    # the list of nested models is automatically inserted
    got = sorted(await AsyncBook.select(), key=lambda x: x.title)
    expected = sorted(async_books, key=lambda x: x.title)
    assert expected == got

    got = sorted(await AsyncLibrary.select(), key=lambda x: x.name)
    expected = sorted(data, key=lambda x: x.name)
    assert got == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update_optional_nested_list_of_models(store):
    data = [
        AsyncLibrary(name="Babel AsyncLibrary", address="In a book", lost=async_books)
    ]
    await AsyncLibrary.insert(data)
    # the list of nested models is automatically inserted
    got = sorted(await AsyncBook.select(), key=lambda x: x.title)
    expected = sorted(async_books, key=lambda x: x.title)
    assert expected == got

    got = sorted(await AsyncLibrary.select(), key=lambda x: x.name)
    expected = sorted(data, key=lambda x: x.name)
    assert got == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update_nested_tuple_of_models(store):
    jane = async_authors["jane"]
    new_stuff = (async_books[0], jane, async_books[1], 8)
    data = [AsyncLibrary(name="Babel AsyncLibrary", address="In a book", new=new_stuff)]
    await AsyncLibrary.insert(data)
    # the tuple of nested models is automatically inserted
    got = sorted(await AsyncBook.select(), key=lambda x: x.title)
    expected = sorted([async_books[0], async_books[1]], key=lambda x: x.title)
    assert expected == got

    got = sorted(await AsyncAuthor.select(), key=lambda x: x.name)
    expected = sorted([async_books[0].author, jane], key=lambda x: x.name)
    assert expected == got

    got = sorted(await AsyncLibrary.select(), key=lambda x: x.name)
    expected = sorted(data, key=lambda x: x.name)
    assert got == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update_optional_nested_tuple_of_models(store):
    popular_async_books = (async_books[0], async_books[2])
    data = [
        AsyncLibrary(
            name="Babel AsyncLibrary", address="In a book", popular=popular_async_books
        )
    ]
    await AsyncLibrary.insert(data)
    # the tuple of nested models is automatically inserted
    got = sorted(await AsyncBook.select(), key=lambda x: x.title)
    expected = sorted(popular_async_books, key=lambda x: x.title)
    assert expected == got

    got = sorted(await AsyncLibrary.select(), key=lambda x: x.name)
    expected = sorted(data, key=lambda x: x.name)
    assert got == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_select_default(store):
    """Selecting without arguments returns all the book models"""
    await AsyncBook.insert(async_books)
    response = await AsyncBook.select()
    sorted_async_books = sorted(async_books, key=lambda x: x.title)
    sorted_response = sorted(response, key=lambda x: x.title)
    assert sorted_async_books == sorted_response


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_select_default_paginated(store):
    """
    Selecting without arguments returns the book models after
    skipping `skip` number of models and returning upto `limit` number of items
    """
    await AsyncBook.insert(async_books)
    Record = namedtuple("Record", ["skip", "limit", "expected"])
    test_data = [
        Record(0, 2, sorted(async_books[:2], key=lambda x: x.title)),
        Record(None, 2, sorted(async_books[:2], key=lambda x: x.title)),
        Record(2, 2, sorted(async_books[2:4], key=lambda x: x.title)),
        Record(3, 2, sorted(async_books[3:5], key=lambda x: x.title)),
        Record(0, 3, sorted(async_books[:3], key=lambda x: x.title)),
    ]
    for record in test_data:
        response = await AsyncBook.select(skip=record.skip, limit=record.limit)
        sorted_response = sorted(response, key=lambda x: x.title)
        assert record.expected == sorted_response


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_select_some_columns(store):
    """
    Selecting some columns returns a list of dictionaries of all async_books models with only those columns
    """
    await AsyncBook.insert(async_books)
    async_books_dict = {book.title: book for book in async_books}
    columns = ["title", "author", "in_stock"]
    response = await AsyncBook.select(columns=columns)
    response_dict = {book["title"]: book for book in response}

    for title, book in async_books_dict.items():
        book_in_response = response_dict[title]
        assert isinstance(book_in_response, dict)
        assert sorted(book_in_response.keys()) == sorted(columns)

        for column in columns:
            if column == "author":
                assert book_in_response[column] == getattr(book, column)
            else:
                assert f"{book_in_response[column]}" == f"{getattr(book, column)}"


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_select_some_columns_paginated(store):
    """
    Selecting some columns returns a list of dictionaries of all books models with only those columns
    skipping `skip` number of models and returning upto `limit` number of items
    """
    await AsyncBook.insert(async_books)
    columns = ["title", "author", "in_stock"]

    Record = namedtuple("Record", ["skip", "limit", "expected"])
    test_data = [
        Record(0, 2, sorted(async_books[:2], key=lambda x: x.title)),
        Record(None, 2, sorted(async_books[:2], key=lambda x: x.title)),
        Record(2, 2, sorted(async_books[2:4], key=lambda x: x.title)),
        Record(3, 2, sorted(async_books[3:5], key=lambda x: x.title)),
        Record(0, 3, sorted(async_books[:3], key=lambda x: x.title)),
    ]
    for record in test_data:
        response = await AsyncBook.select(
            columns=columns, skip=record.skip, limit=record.limit
        )
        response_dict = {book["title"]: book for book in response}
        books_dict = {book.title: book for book in record.expected}
        assert len(record.expected) == len(response_dict)

        for title, book in books_dict.items():
            book_in_response = response_dict[title]
            assert isinstance(book_in_response, dict)
            assert sorted(book_in_response.keys()) == sorted(columns)

            for column in columns:
                if column == "author":
                    assert book_in_response[column] == getattr(book, column)
                else:
                    assert f"{book_in_response[column]}" == f"{getattr(book, column)}"


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_select_some_ids(store):
    """
    Selecting some ids returns only those elements with the given ids
    """
    await AsyncBook.insert(async_books)
    ids = [book.title for book in async_books[:2]]
    response = await AsyncBook.select(ids=ids)
    assert response == async_books[:2]


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update(store):
    """
    Updating an item of a given primary key updates it in redis
    """
    await AsyncBook.insert(async_books)
    title = async_books[0].title
    new_in_stock = not async_books[0].in_stock
    new_author = AsyncAuthor(name="John Doe", active_years=(2000, 2009))
    book_key = f"asyncbook_%&_{title}"
    new_author_key = f"asyncauthor_%&_{new_author.name}"
    old_book_data = await store.redis_store.hgetall(name=book_key)
    old_book = await __deserialize_book_data(old_book_data)
    assert old_book == async_books[0]
    assert old_book.author != new_author

    await AsyncBook.update(
        _id=title, data={"author": new_author, "in_stock": new_in_stock}
    )

    book_data = await store.redis_store.hgetall(name=book_key)
    book = await __deserialize_book_data(book_data)
    author_data = await store.redis_store.hgetall(name=new_author_key)
    author = AsyncAuthor(**AsyncAuthor.deserialize_partially(author_data))
    assert book.author == new_author
    assert author == new_author
    assert book.title == old_book.title
    assert book.in_stock == new_in_stock
    assert book.published_on == old_book.published_on


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_update_nested_model(store):
    """
    Updating a nested model, without changing its primary key, also updates it its collection in redis
    """
    await AsyncBook.insert(async_books)

    new_in_stock = not async_books[0].in_stock
    updated_author = AsyncAuthor(**async_books[0].author.dict())
    updated_author.active_years = (2020, 2045)
    book_key = f"asyncbook_%&_{async_books[0].title}"
    author_key = f"asyncauthor_%&_{updated_author.name}"

    old_author_data = await store.redis_store.hgetall(name=author_key)
    old_author = AsyncAuthor(**AsyncAuthor.deserialize_partially(old_author_data))
    old_book_data = await store.redis_store.hgetall(name=book_key)
    old_book = await __deserialize_book_data(old_book_data)
    assert old_book == async_books[0]
    assert old_author == async_books[0].author
    assert old_author != updated_author

    await AsyncBook.update(
        _id=async_books[0].title,
        data={"author": updated_author, "in_stock": new_in_stock},
    )

    book_data = await store.redis_store.hgetall(name=book_key)
    book = await __deserialize_book_data(book_data)
    author_data = await store.redis_store.hgetall(name=author_key)
    author = AsyncAuthor(**AsyncAuthor.deserialize_partially(author_data))
    assert book.author == updated_author
    assert author == updated_author
    assert book.title == old_book.title
    assert book.in_stock == new_in_stock
    assert book.published_on == old_book.published_on


@pytest.mark.asyncio
@pytest.mark.parametrize("store", async_redis_store_fixture)
async def test_delete_multiple(store):
    """
    Providing a list of ids to the delete function will remove the items from redis,
    but leave the nested models intact
    """
    await AsyncBook.insert(async_books)
    async_books_to_delete = async_books[:2]
    async_books_left_in_db = async_books[2:]

    ids_to_delete = [book.title for book in async_books_to_delete]
    ids_to_leave_intact = [book.title for book in async_books_left_in_db]

    keys_to_delete = [f"asyncbook_%&_{_id}" for _id in ids_to_delete]
    book_keys_to_leave_intact = [f"asyncbook_%&_{_id}" for _id in ids_to_leave_intact]
    author_keys_to_leave_intact = [
        f"asyncauthor_%&_{author.name}" for author in async_authors.values()
    ]

    await AsyncBook.delete(ids=ids_to_delete)

    for key in keys_to_delete:
        deleted_book_in_redis = await store.redis_store.hgetall(name=key)
        assert deleted_book_in_redis == {}

    async with store.redis_store.pipeline() as pipeline:
        for key in book_keys_to_leave_intact:
            pipeline.hgetall(name=key)
        async_books_in_redis = await pipeline.execute()
        async_books_in_redis_as_models = [
            await __deserialize_book_data(book) for book in async_books_in_redis
        ]
        assert async_books_left_in_db == async_books_in_redis_as_models

        for key in author_keys_to_leave_intact:
            pipeline.hgetall(name=key)
        async_authors_in_redis = await pipeline.execute()
        async_authors_in_redis_as_models = sorted(
            [
                AsyncAuthor(**AsyncAuthor.deserialize_partially(author))
                for author in async_authors_in_redis
            ],
            key=lambda x: x.name,
        )
        expected = sorted(async_authors.values(), key=lambda x: x.name)
        assert expected == async_authors_in_redis_as_models


async def __deserialize_book_data(raw_book_data: Dict[str, Any]) -> AsyncBook:
    """Deserializes the raw book data returning a book instance"""
    author_id = raw_book_data.pop(f"{NESTED_MODEL_PREFIX}author")
    author_id = strip_leading(author_id, "asyncauthor_%&_")

    data = AsyncBook.deserialize_partially(raw_book_data)

    data["author"] = (await AsyncAuthor.select(ids=[author_id]))[0]
    return AsyncBook(**data)
