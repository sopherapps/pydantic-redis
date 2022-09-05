"""Tests for the redis orm"""

import unittest
from datetime import date
from typing import List, Tuple, Dict, Any

from pydantic_redis.config import RedisConfig
from pydantic_redis.model import Model
from pydantic_redis.store import Store


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


class ModelWithoutPrimaryKey(Model):
    title: str


class TestRedisOrm(unittest.TestCase):
    """
    Tests for Redis Orm
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.store = Store(name='sample', redis_config=RedisConfig(db=5), life_span_in_seconds=3600)
        cls.store.register_model(Book)
        cls.store.register_model(Author)

    def tearDown(self) -> None:
        """Tear down a few things"""
        keys = [f"book_%&_{book.title}" for book in books] + [f"author_%&_{author.name}" for author in authors.values()]
        self.store.redis_store.delete(*keys)

    def test_register_model_without_primary_key(self):
        """Throws error when a model without the _primary_key_field class variable set is registered"""
        self.assertRaisesRegex(AttributeError, '_primary_key_field', self.store.register_model,
                               ModelWithoutPrimaryKey)
        ModelWithoutPrimaryKey._primary_key_field = None
        self.assertRaisesRegex(Exception, 'should have a _primary_key_field', self.store.register_model,
                               ModelWithoutPrimaryKey)

    def test_bulk_insert(self):
        """Providing a list of Model instances to the insert method inserts the records in redis"""
        book_keys = [f"book_%&_{book.title}" for book in books]
        keys = book_keys + [f"author_%&_{author.name}" for author in authors.values()]
        self.store.redis_store.delete(*keys)

        for key in keys:
            item_in_redis = self.store.redis_store.hgetall(name=key)
            self.assertEqual(item_in_redis, {})

        Book.insert(books)

        pipeline = self.store.redis_store.pipeline()
        for book_key in book_keys:
            pipeline.hgetall(name=book_key)
        books_in_redis = pipeline.execute()
        books_in_redis_as_models = [self.__deserialize_book_data(book) for book in books_in_redis]
        self.assertEqual(books, books_in_redis_as_models)

    def test_bulk_nested_insert(self):
        """Providing a list of Model instances to the insert method also upserts their nested records in redis"""
        book_keys = [f"book_%&_{book.title}" for book in books]
        author_keys = [f"author_%&_{author.name}" for author in authors.values()]
        keys = book_keys + author_keys
        self.store.redis_store.delete(*keys)

        for key in keys:
            item_in_redis = self.store.redis_store.hgetall(name=key)
            self.assertEqual(item_in_redis, {})

        Book.insert(books)

        pipeline = self.store.redis_store.pipeline()
        for key in author_keys:
            pipeline.hgetall(name=key)
        authors_in_redis = pipeline.execute()
        authors_in_redis_as_models = sorted(
            [Author(**Author.deserialize_partially(author)) for author in authors_in_redis], key=lambda x: x.name)
        expected = sorted(authors.values(), key=lambda x: x.name)
        self.assertListEqual(expected, authors_in_redis_as_models)

    def test_insert_single(self):
        """
        Providing a single Model instance inserts that record in redis
        """
        key = f"book_%&_{books[0].title}"
        book = self.store.redis_store.hgetall(name=key)
        self.assertEqual(book, {})

        Book.insert(books[0])

        book = self.store.redis_store.hgetall(name=key)
        book_as_model = self.__deserialize_book_data(book)
        self.assertEqual(books[0], book_as_model)

    def test_insert_single_nested(self):
        """
        Providing a single Model instance upserts also any nested model into redis
        """
        key = f"author_%&_{books[0].author.name}"
        author = self.store.redis_store.hgetall(name=key)
        self.assertEqual(author, {})

        Book.insert(books[0])

        author = self.store.redis_store.hgetall(name=key)
        author_as_model = Author(**Author.deserialize_partially(author))
        self.assertEqual(books[0].author, author_as_model)

    def test_select_default(self):
        """Selecting without arguments returns all the book models"""
        Book.insert(books)
        response = Book.select()
        sorted_books = sorted(books, key=lambda x: x.title)
        sorted_response = sorted(response, key=lambda x: x.title)
        self.assertEqual(sorted_books, sorted_response)

    def test_select_some_columns(self):
        """
        Selecting some columns returns a list of dictionaries of all books models with only those columns
        """
        Book.insert(books)
        books_dict = {book.title: book for book in books}
        columns = ['title', 'author', 'in_stock']
        response = Book.select(columns=['title', 'author', 'in_stock'])
        response_dict = {book['title']: book for book in response}

        for title, book in books_dict.items():
            book_in_response = response_dict[title]
            self.assertIsInstance(book_in_response, dict)
            self.assertEqual(sorted(book_in_response.keys()), sorted(columns))
            for column in columns:
                if column == 'author':
                    self.assertEqual(book_in_response[column], getattr(book, column))
                else:
                    self.assertEqual(f"{book_in_response[column]}", f"{getattr(book, column)}")

    def test_select_some_ids(self):
        """
        Selecting some ids returns only those elements with the given ids
        """
        Book.insert(books)
        ids = [book.title for book in books[:2]]
        response = Book.select(ids=ids)
        self.assertEqual(response, books[:2])

    def test_update(self):
        """
        Updating an item of a given primary key updates it in redis
        """
        Book.insert(books)
        title = books[0].title
        new_in_stock = not books[0].in_stock
        new_author = Author(name='John Doe', active_years=(2000, 2009))
        book_key = f"book_%&_{title}"
        new_author_key = f"author_%&_{new_author.name}"
        old_book_data = self.store.redis_store.hgetall(name=book_key)
        old_book = self.__deserialize_book_data(old_book_data)
        self.assertEqual(old_book, books[0])
        self.assertNotEqual(old_book.author, new_author)

        Book.update(_id=title, data={"author": new_author, "in_stock": new_in_stock})

        book_data = self.store.redis_store.hgetall(name=book_key)
        book = self.__deserialize_book_data(book_data)
        author_data = self.store.redis_store.hgetall(name=new_author_key)
        author = Author(**Author.deserialize_partially(author_data))
        self.assertEqual(book.author, new_author)
        self.assertEqual(author, new_author)
        self.assertEqual(book.title, old_book.title)
        self.assertEqual(book.in_stock, new_in_stock)
        self.assertEqual(book.published_on, old_book.published_on)

    def test_update_nested_model(self):
        """
        Updating a nested model, without changing its primary key, also updates it its collection in redis
        """
        Book.insert(books)

        new_in_stock = not books[0].in_stock
        updated_author = Author(**books[0].author.dict())
        updated_author.active_years = (2020, 2045)
        book_key = f"book_%&_{books[0].title}"
        author_key = f"author_%&_{updated_author.name}"

        old_author_data = self.store.redis_store.hgetall(name=author_key)
        old_author = Author(**Author.deserialize_partially(old_author_data))
        old_book_data = self.store.redis_store.hgetall(name=book_key)
        old_book = self.__deserialize_book_data(old_book_data)
        self.assertEqual(old_book, books[0])
        self.assertEqual(old_author, books[0].author)
        self.assertNotEqual(old_author, updated_author)

        Book.update(_id=books[0].title, data={"author": updated_author, "in_stock": new_in_stock})

        book_data = self.store.redis_store.hgetall(name=book_key)
        book = self.__deserialize_book_data(book_data)
        author_data = self.store.redis_store.hgetall(name=author_key)
        author = Author(**Author.deserialize_partially(author_data))
        self.assertEqual(book.author, updated_author)
        self.assertEqual(author, updated_author)
        self.assertEqual(book.title, old_book.title)
        self.assertEqual(book.in_stock, new_in_stock)
        self.assertEqual(book.published_on, old_book.published_on)

    def test_delete_multiple(self):
        """
        Providing a list of ids to the delete function will remove the items from redis,
        but leave the nested models intact
        """
        Book.insert(books)
        books_to_delete = books[:2]
        books_left_in_db = books[2:]

        ids_to_delete = [book.title for book in books_to_delete]
        ids_to_leave_intact = [book.title for book in books_left_in_db]

        keys_to_delete = [f"book_%&_{_id}" for _id in ids_to_delete]
        book_keys_to_leave_intact = [f"book_%&_{_id}" for _id in ids_to_leave_intact]
        author_keys_to_leave_intact = [f"author_%&_{author.name}" for author in authors.values()]

        Book.delete(ids=ids_to_delete)

        for key in keys_to_delete:
            deleted_book_in_redis = self.store.redis_store.hgetall(name=key)
            self.assertEqual(deleted_book_in_redis, {})

        pipeline = self.store.redis_store.pipeline()
        for key in book_keys_to_leave_intact:
            pipeline.hgetall(name=key)
        books_in_redis = pipeline.execute()
        books_in_redis_as_models = [self.__deserialize_book_data(book) for book in books_in_redis]
        self.assertEqual(books_left_in_db, books_in_redis_as_models)

        pipeline = self.store.redis_store.pipeline()
        for key in author_keys_to_leave_intact:
            pipeline.hgetall(name=key)
        authors_in_redis = pipeline.execute()
        authors_in_redis_as_models = sorted(
            [Author(**Author.deserialize_partially(author)) for author in authors_in_redis], key=lambda x: x.name)
        expected = sorted(authors.values(), key=lambda x: x.name)
        self.assertListEqual(expected, authors_in_redis_as_models)

    @staticmethod
    def __deserialize_book_data(raw_book_data: Dict[bytes, Any]) -> Book:
        """Deserializes the raw book data returning a book instance"""
        data = Book.deserialize_partially(raw_book_data)
        data["author"] = Author.select(ids=[data["__author"]])[0]
        return Book(**data)


if __name__ == '__main__':
    unittest.main()
