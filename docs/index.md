# Pydantic-redis

A simple declarative ORM for redis based on pydantic

## Features

1. A subclass-able `Model` class to create Object Relational Mapping to redis hashes
2. A redis `Store` class to mutate and query `Model`'s registered in it
3. A `RedisConfig` class to pass to the `Store` constructor to connect to a redis instance
4. A synchronous `syncio` and an asynchronous `asyncio` interface to the above classes

### Installation

```shell
pip install pydantic-redis
```

### Usage

Import the `Store`, the `RedisConfig` and the `Model` classes from `pydantic_redis` and use accordingly

```python
from datetime import date
from typing import Tuple, List, Optional
from pydantic_redis import RedisConfig, Model, Store


class Author(Model):
    """
    An Author model, just like a pydantic model with appropriate 
    type annotations
    NOTE: The `_primary_key_field` is mandatory
    """
    _primary_key_field: str = 'name'
    name: str
    active_years: Tuple[int, int]


class Book(Model):
    """
    A Book model.
    
    Models can have the following field types
    - The usual i.e. float, int, dict, list, date, str, dict, Optional etc
      as long as they are serializable by orjson
    - Nested models e.g. `author: Author` or `author: Optional[Author]`
    - List of nested models e.g. `authors: List[Author]` 
      or `authors: Optional[List[Author]]`
    - Tuples including nested models e.g. `access_log: Tuple[Author, date]` 
      or `access_log: Optional[Tuple[Author, date]]]`
    
    NOTE: 1. Any nested model whether plain or in a list or tuple will automatically 
          inserted into the redis store when the parent model is inserted. 
          e.g. a Book with an author field, when inserted, will also insert
         the author. The author can then be queried directly if that's something 
         one wishes to do.
         
         2. When a parent model is inserted with a nested model instance that 
         already exists, the older nested model instance is overwritten. 
         This is one way of updating nested models. 
         All parent models that contain that nested model instance will see the change. 
    """
    _primary_key_field: str = 'title'
    title: str
    author: Author
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


class Library(Model):
    """
    A library model.
    
    It shows a number of complicated nested models.
    
    About Nested Model Performance
    ---
    To minimize the performance penalty for nesting models, 
    we use REDIS EVALSHA to eagerly load the nested models
    before the response is returned to the client.
    This ensures that only ONE network call is made every time.
    """
    _primary_key_field: str = 'name'
    name: str
    address: str
    books: List[Book] = None
    lost: Optional[List[Book]] = None
    popular: Optional[Tuple[Book, Book]] = None
    new: Tuple[Book, Author, int] = None


# Create the store
store = Store(
    name='some_name',
    redis_config=RedisConfig(db=5, host='localhost', port=6379),
    life_span_in_seconds=3600)

# register your models. DON'T FORGET TO DO THIS.
store.register_model(Book)
store.register_model(Library)
store.register_model(Author)

# sample authors. You can create as many as you wish anywhere in the code
authors = {
    "charles": Author(name="Charles Dickens", active_years=(1220, 1280)),
    "jane": Author(name="Jane Austen", active_years=(1580, 1640)),
}

# Sample books.
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

# Some library objects
libraries = [
    Library(
        name="The Grand Library",
        address="Kinogozi, Hoima, Uganda",
        lost=[books[1]],
    ),
    Library(
        name="Christian Library",
        address="Buhimba, Hoima, Uganda",
        new=(books[0], authors["jane"], 30),
    )
]

# Insert Many. You can given them a TTL (life_span_seconds).
Book.insert(books, life_span_seconds=3600)
Library.insert(libraries)

# Insert One. You can also given it a TTL (life_span_seconds).
Author.insert(Author(name="Jack Myers", active_years=(1240, 1300)))

# Update One. You can also given it a TTL (life_span_seconds).
Book.update(_id="Oliver Twist", data={"author": authors["jane"]})

# Update nested model indirectly
updated_jane = Author(**authors["jane"].dict())
updated_jane.active_years = (1999, 2008)
Book.update(_id="Oliver Twist", data={"author": updated_jane})

# Query the data
# Get all, with all fields shown. Data returned is a list of models instances.
all_books = Book.select()
print(all_books)
# Prints [Book(title="Oliver Twist", author="Charles Dickens", published_on=date(year=1215, month=4, day=4), 
# in_stock=False), Book(...]

# or paginate i.e. skip some books and return only upto a given number
paginated_books = Book.select(skip=2, limit=2)
print(paginated_books)

# Get some, with all fields shown. Data returned is a list of models instances.
some_books = Book.select(ids=["Oliver Twist", "Jane Eyre"])
print(some_books)

# Note: Pagination does not work when ids are provided i.e.
assert some_books == Book.select(ids=["Oliver Twist", "Jane Eyre"], skip=100, limit=10)

# Get all, with only a few fields shown. Data returned is a list of dictionaries.
books_with_few_fields = Book.select(columns=["author", "in_stock"])
print(books_with_few_fields)
# Prints [{"author": "'Charles Dickens", "in_stock": "True"},...]

# or paginate i.e. skip some books and return only upto a given number
paginated_books_with_few_fields = Book.select(columns=["author", "in_stock"], skip=2, limit=2)
print(paginated_books_with_few_fields)

# Get some, with only some fields shown. Data returned is a list of dictionaries.
some_books_with_few_fields = Book.select(ids=["Oliver Twist", "Jane Eyre"], columns=["author", "in_stock"])
print(some_books_with_few_fields)

# Query the nested models directly.
some_authors = Author.select(ids=["Jane Austen"])
print(some_authors)

# Delete any number of items
Library.delete(ids=["The Grand Library"])
```