# pydantic-redis

[![PyPI version](https://badge.fury.io/py/pydantic-redis.svg)](https://badge.fury.io/py/pydantic-redis) ![CI](https://github.com/sopherapps/pydantic-redis/actions/workflows/ci.yml/badge.svg)

A simple declarative ORM for Redis

## Main Dependencies

- [Python +3.6](https://www.python.org)
- [redis](https://pypi.org/project/redis/)
- [pydantic](https://github.com/samuelcolvin/pydantic/)

## Most Notable Features

- Define business domain objects as [pydantic](https://github.com/samuelcolvin/pydantic/) and automatically get ability
  to save them as is in [redis](https://pypi.org/project/redis/) with an intuitive API of `insert`, `update`, `delete`,
  `select`
- Maintain simple relationships between domain objects by simply nesting them either as single objects or lists, or tuples.
  Any direct or indirect update to a nested object will automatically reflect in all parent objects that have it nested in
  them when queried again from redis.
- Both synchronous and asynchronous APIs available.

## Getting Started (Synchronous Version)

- Install the package

  ```bash
  pip install pydantic-redis
  ```

- Import the `Store`, the `RedisConfig` and the `Model` classes from `pydantic_redis` and use accordingly

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

## Getting Started (Asynchronous Version)

- Install the package

  ```bash
  pip install pydantic-redis
  ```

- Import the `Store`, the `RedisConfig` and the `Model` classes from `pydantic_redis.asyncio` and use accordingly

```python
import asyncio
from datetime import date
from typing import Tuple, List, Optional
from pydantic_redis.asyncio import RedisConfig, Model, Store

# The features are exactly the same as the synchronous version, 
# except for the ability to return coroutines when `insert`, 
# `update`, `select` or `delete` are called.


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


async def run_async():
  """The async coroutine"""
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
  await Book.insert(books, life_span_seconds=3600)
  await Library.insert(libraries)
  
  # Insert One. You can also given it a TTL (life_span_seconds).
  await Author.insert(Author(name="Jack Myers", active_years=(1240, 1300)))
  
  # Update One. You can also given it a TTL (life_span_seconds).
  await Book.update(_id="Oliver Twist", data={"author": authors["jane"]})
  
  # Update nested model indirectly
  updated_jane = Author(**authors["jane"].dict())
  updated_jane.active_years = (1999, 2008)
  await Book.update(_id="Oliver Twist", data={"author": updated_jane})
  
  # Query the data
  # Get all, with all fields shown. Data returned is a list of models instances.
  all_books = await Book.select()
  print(all_books)
  # Prints [Book(title="Oliver Twist", author="Charles Dickens", published_on=date(year=1215, month=4, day=4), 
  # in_stock=False), Book(...]
  
  # or paginate i.e. skip some books and return only upto a given number
  paginated_books = await Book.select(skip=2, limit=2)
  print(paginated_books)
    
  # Get some, with all fields shown. Data returned is a list of models instances.
  some_books = await Book.select(ids=["Oliver Twist", "Jane Eyre"])
  print(some_books)
  
  # Note: Pagination does not work when ids are provided i.e.
  assert some_books == await Book.select(ids=["Oliver Twist", "Jane Eyre"], skip=100, limit=10)
  
  # Get all, with only a few fields shown. Data returned is a list of dictionaries.
  books_with_few_fields = await Book.select(columns=["author", "in_stock"])
  print(books_with_few_fields)
  # Prints [{"author": "'Charles Dickens", "in_stock": "True"},...]
  
  # or paginate i.e. skip some books and return only upto a given number
  paginated_books_with_few_fields = await Book.select(columns=["author", "in_stock"], skip=2, limit=2)
  print(paginated_books_with_few_fields)
  
  # Get some, with only some fields shown. Data returned is a list of dictionaries.
  some_books_with_few_fields = await Book.select(ids=["Oliver Twist", "Jane Eyre"], columns=["author", "in_stock"])
  print(some_books_with_few_fields)
  
  # Query the nested models directly.
  some_authors = await Author.select(ids=["Jane Austen"])
  print(some_authors)
  
  # Delete any number of items
  await Library.delete(ids=["The Grand Library"])


asyncio.run(run_async())
```

## How to test

- Clone the repo and enter its root folder

  ```bash
  git clone https://github.com/sopherapps/pydantic-redis.git && cd pydantic-redis
  ```

- Create a virtual environment and activate it

  ```bash
  virtualenv -p /usr/bin/python3.6 env && source env/bin/activate
  ```

- Install the dependencies

  ```bash
  pip install -r requirements.txt
  ```

- Run the pre-commit installation

  ```bash
  pre-commit install
  ```

- Run the tests command

  ```bash
  pytest --benchmark-disable
  ```

- Run benchmarks

  ```bash
  pytest --benchmark-compare --benchmark-autosave
  ```

- Or run to get benchmarks summary

  ```shell
  pytest test/test_benchmarks.py --benchmark-columns=mean,min,max --benchmark-name=short
  ```

## Benchmarks

On an average PC ~16GB RAM, i7 Core

```
-------------------------------------------------- benchmark: 22 tests --------------------------------------------------
Name (time in us)                                                Mean                 Min                   Max          
-------------------------------------------------------------------------------------------------------------------------
benchmark_select_columns_for_one_id[redis_store-book2]       124.2687 (1.00)     115.4530 (1.0)        331.8030 (1.26)   
benchmark_select_columns_for_one_id[redis_store-book0]       123.7213 (1.0)      115.6680 (1.00)       305.7170 (1.16)   
benchmark_select_columns_for_one_id[redis_store-book3]       124.4495 (1.01)     115.9580 (1.00)       263.4370 (1.0)    
benchmark_select_columns_for_one_id[redis_store-book1]       124.8431 (1.01)     117.4770 (1.02)       310.3140 (1.18)   
benchmark_select_columns_for_some_items[redis_store]         128.0657 (1.04)     118.6380 (1.03)       330.2680 (1.25)   
benchmark_delete[redis_store-Wuthering Heights]              131.8713 (1.07)     125.9920 (1.09)       328.9660 (1.25)   
benchmark_bulk_delete[redis_store]                           148.6963 (1.20)     142.3190 (1.23)       347.4750 (1.32)   
benchmark_select_all_for_one_id[redis_store-book3]           211.6941 (1.71)     195.6520 (1.69)       422.8840 (1.61)   
benchmark_select_all_for_one_id[redis_store-book2]           212.3612 (1.72)     195.9020 (1.70)       447.4910 (1.70)   
benchmark_select_all_for_one_id[redis_store-book1]           212.9524 (1.72)     197.7530 (1.71)       423.3030 (1.61)   
benchmark_select_all_for_one_id[redis_store-book0]           214.9924 (1.74)     198.8280 (1.72)       402.6310 (1.53)   
benchmark_select_columns_paginated[redis_store]              227.9248 (1.84)     211.0610 (1.83)       425.8390 (1.62)   
benchmark_select_some_items[redis_store]                     297.5700 (2.41)     271.1510 (2.35)       572.1220 (2.17)   
benchmark_select_default_paginated[redis_store]              301.7495 (2.44)     282.6500 (2.45)       490.3450 (1.86)   
benchmark_select_columns[redis_store]                        316.2119 (2.56)     290.6110 (2.52)       578.0310 (2.19)   
benchmark_update[redis_store-Wuthering Heights-data0]        346.5816 (2.80)     304.5420 (2.64)       618.0250 (2.35)   
benchmark_single_insert[redis_store-book2]                   378.0613 (3.06)     337.8070 (2.93)       616.4930 (2.34)   
benchmark_single_insert[redis_store-book0]                   396.6513 (3.21)     347.1000 (3.01)       696.1350 (2.64)   
benchmark_single_insert[redis_store-book3]                   395.9082 (3.20)     361.0980 (3.13)       623.8630 (2.37)   
benchmark_single_insert[redis_store-book1]                   401.1377 (3.24)     363.5890 (3.15)       610.4400 (2.32)   
benchmark_select_default[redis_store]                        498.4673 (4.03)     428.1350 (3.71)       769.7640 (2.92)   
benchmark_bulk_insert[redis_store]                         1,025.0436 (8.29)     962.2230 (8.33)     1,200.3840 (4.56)   
-------------------------------------------------------------------------------------------------------------------------
```

## Contributions

Contributions are welcome. The docs have to maintained, the code has to be made cleaner, more idiomatic and faster,
and there might be need for someone else to take over this repo in case I move on to other things. It happens!

When you are ready, look at the [CONTRIBUTIONS GUIDELINES](./CONTRIBUTING.md)

## License

Copyright (c) 2020 [Martin Ahindura](https://github.com/Tinitto) Licensed under the [MIT License](./LICENSE)

## Gratitude

> "There is no condemnation now for those who live in union with Christ Jesus.
> For the law of the Spirit, which brings us life in union with Christ Jesus,
> has set me free from the law of sin and death"
>
> -- Romans 8: 1-2

All glory be to God

<a href="https://www.buymeacoffee.com/martinahinJ" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>
