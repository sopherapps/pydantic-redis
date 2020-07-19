"""Tests for the redis orm"""

import unittest
from datetime import date

from pydantic_redis.config import RedisConfig
from pydantic_redis.model import Model
from pydantic_redis.store import Store


class Book(Model):
    _primary_key_field: str = 'title'
    title: str
    author: str
    published_on: date
    in_stock: bool = True


books = [
    Book(title="Oliver Twist", author='Charles Dickens', published_on=date(year=1215, month=4, day=4),
         in_stock=False),
    Book(title="Great Expectations", author='Charles Dickens', published_on=date(year=1220, month=4, day=4)),
    Book(title="Jane Eyre", author='Charles Dickens', published_on=date(year=1225, month=6, day=4), in_stock=False),
    Book(title="Wuthering Heights", author='Jane Austen', published_on=date(year=1600, month=4, day=4)),
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

    def tearDown(self) -> None:
        """Tear down a few things"""
        keys = [f"book_%&_{book.title}" for book in books]
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
        keys = [f"book_%&_{book.title}" for book in books]
        self.store.redis_store.delete(*keys)

        for key in keys:
            book_in_redis = self.store.redis_store.hgetall(name=key)
            self.assertEqual(book_in_redis, {})

        Book.insert(books)

        pipeline = self.store.redis_store.pipeline()
        for key in keys:
            pipeline.hgetall(name=key)
        books_in_redis = pipeline.execute()
        books_in_redis_as_models = [Book(**Book.deserialize_partially(book)) for book in books_in_redis]
        self.assertEqual(books, books_in_redis_as_models)

    def test_insert_single(self):
        """
        Providing a single Model instance
        """
        key = f"book_%&_{books[0].title}"
        book = self.store.redis_store.hgetall(name=key)
        self.assertEqual(book, {})

        Book.insert(books[0])

        book = self.store.redis_store.hgetall(name=key)
        book_as_model = Book(**Book.deserialize_partially(book))
        self.assertEqual(books[0], book_as_model)

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
        new_author = 'John Doe'
        key = f"book_%&_{title}"
        old_book_data = self.store.redis_store.hgetall(name=key)
        old_book = Book(**Book.deserialize_partially(old_book_data))
        self.assertEqual(old_book, books[0])
        self.assertNotEqual(old_book.author, new_author)

        Book.update(_id=title, data={"author": "John Doe"})

        book_data = self.store.redis_store.hgetall(name=key)
        book = Book(**Book.deserialize_partially(book_data))
        self.assertEqual(book.author, new_author)
        self.assertEqual(book.title, old_book.title)
        self.assertEqual(book.in_stock, old_book.in_stock)
        self.assertEqual(book.published_on, old_book.published_on)

    def test_delete_multiple(self):
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
            deleted_book_in_redis = self.store.redis_store.hgetall(name=key)
            self.assertEqual(deleted_book_in_redis, {})

        pipeline = self.store.redis_store.pipeline()
        for key in keys_to_leave_intact:
            pipeline.hgetall(name=key)
        books_in_redis = pipeline.execute()
        books_in_redis_as_models = [Book(**Book.deserialize_partially(book)) for book in books_in_redis]
        self.assertEqual(books_left_in_db, books_in_redis_as_models)


if __name__ == '__main__':
    unittest.main()
