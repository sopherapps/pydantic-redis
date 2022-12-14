# pydantic-redis

[![PyPI version](https://badge.fury.io/py/pydantic-redis.svg)](https://badge.fury.io/py/pydantic-redis) ![CI](https://github.com/sopherapps/pydantic-redis/actions/workflows/ci.yml/badge.svg)

A simple declarative ORM for Redis

*Note: For a faster ORM with similar features, consider [orredis](https://github.com/sopherapps/orredis) which, under the hood, is built in rust*

## Main Dependencies

- [Python +3.6](https://www.python.org)
- [redis](https://pypi.org/project/redis/)
- [pydantic](https://github.com/samuelcolvin/pydantic/)

## Getting Started

- Install the package

  ```bash
  pip install pydantic-redis
  ```

- Import the `Store`, the `RedisConfig` and the `Model` classes and use accordingly

```python
from datetime import date
from typing import Tuple, List
from pydantic_redis import RedisConfig, Model, Store


# Create models as you would create pydantic models i.e. using typings
# the _primary_key_field is mandatory for ease of data querying and updating
class Author(Model):
  _primary_key_field: str = 'name'
  name: str
  active_years: Tuple[int, int]


# Create models as you would create pydantic models i.e. using typings
# the _primary_key_field is mandatory for ease of data querying and updating
class Book(Model):
  _primary_key_field: str = 'title'
  title: str
  author: Author
  # You can even nest models. they will be automatically inserted into their own collection
  # if they don't exist. Any update to these nested models will reflect in future data; thus no stale data.
  # consider this as an actual child-parent relationship
  rating: float
  published_on: date
  tags: List[str] = []
  in_stock: bool = True


class Library(Model):
  # the _primary_key_field is mandatory
  _primary_key_field: str = 'name'
  name: str
  address: str


# Create the store and register your models
store = Store(name='some_name', redis_config=RedisConfig(db=5, host='localhost', port=6379),
              life_span_in_seconds=3600)
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
  Book(title="Oliver Twist", author=authors["charles"], published_on=date(year=1215, month=4, day=4),
       in_stock=False, rating=2, tags=["Classic"]),
  Book(title="Great Expectations", author=authors["charles"], published_on=date(year=1220, month=4, day=4),
       rating=5,
       tags=["Classic"]),
  Book(title="Jane Eyre", author=authors["charles"], published_on=date(year=1225, month=6, day=4), in_stock=False,
       rating=3.4, tags=["Classic", "Romance"]),
  Book(title="Wuthering Heights", author=authors["jane"], published_on=date(year=1600, month=4, day=4),
       rating=4.0,
       tags=["Classic", "Romance"]),
]

# Some library objects
libraries = [
  Library(name="The Grand Library", address="Kinogozi, Hoima, Uganda"),
  Library(name="Christian Library", address="Buhimba, Hoima, Uganda")
]

# Insert them into redis
Book.insert(books)  # (the associated authors will be automatically inserted)
Library.insert(libraries)

# Select all books to view them. A list of Model instances will be returned
all_books = Book.select()
print(
  all_books)  # Will print [Book(title="Oliver Twist", author="Charles Dickens", published_on=date(year=1215, month=4, day=4), in_stock=False), Book(...]

# Or select some books
some_books = Book.select(ids=["Oliver Twist", "Jane Eyre"])
print(some_books)  # Will print only those two books

# Or select some authors
some_authors = Author.select(ids=["Jane Austen"])
print(
  some_authors)  # Will print Jane Austen even though you didn't explicitly insert her in the Author's collection

# Or select some columns. THIS RETURNS DICTIONARIES not MODEL Instances
# The Dictionaries have values in string form so you might need to do some extra work
books_with_few_fields = Book.select(columns=["author", "in_stock"])
print(books_with_few_fields)  # Will print [{"author": "'Charles Dickens", "in_stock": "True"},...]

# Update any book or library
Book.update(_id="Oliver Twist", data={"author": authors["jane"]})
# You could even update a given author's details by nesting their new data in a book update
updated_jane = Author(**authors["jane"].dict())
updated_jane.active_years = (1999, 2008)
Book.update(_id="Oliver Twist", data={"author": updated_jane})
# Trying to retrieve jane directly will return her with the new details
# All other books that have Jane Austen as author will also have their data updated. (like a real relationship)
Author.select(ids=["Jane Austen"])

# Delete any number of items
Library.delete(ids=["The Grand Library"])
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
------------------------------------------------- benchmark: 20 tests -------------------------------------------------
Name (time in us)                                              Mean                 Min                   Max          
-----------------------------------------------------------------------------------------------------------------------
benchmark_select_columns_for_one_id[redis_store-book1]     143.5316 (1.08)     117.4340 (1.0)        347.5900 (1.0)    
benchmark_select_columns_for_one_id[redis_store-book3]     151.6032 (1.14)     117.6690 (1.00)       405.4620 (1.17)   
benchmark_select_columns_for_one_id[redis_store-book0]     133.0856 (1.0)      117.8720 (1.00)       403.9400 (1.16)   
benchmark_select_columns_for_one_id[redis_store-book2]     156.8152 (1.18)     118.7220 (1.01)       569.9800 (1.64)   
benchmark_select_columns_for_some_items[redis_store]       138.0488 (1.04)     120.1550 (1.02)       350.7040 (1.01)   
benchmark_delete[redis_store-Wuthering Heights]            199.9205 (1.50)     127.6990 (1.09)     1,092.2190 (3.14)   
benchmark_bulk_delete[redis_store]                         178.4756 (1.34)     143.7480 (1.22)       647.6660 (1.86)   
benchmark_select_all_for_one_id[redis_store-book1]         245.7787 (1.85)     195.2030 (1.66)       528.9250 (1.52)   
benchmark_select_all_for_one_id[redis_store-book0]         239.1152 (1.80)     199.4360 (1.70)       767.2540 (2.21)   
benchmark_select_all_for_one_id[redis_store-book3]         243.8724 (1.83)     200.8060 (1.71)       535.3640 (1.54)   
benchmark_select_all_for_one_id[redis_store-book2]         256.1625 (1.92)     202.4630 (1.72)       701.3000 (2.02)   
benchmark_update[redis_store-Wuthering Heights-data0]      329.1363 (2.47)     266.9700 (2.27)       742.1360 (2.14)   
benchmark_select_some_items[redis_store]                   301.0471 (2.26)     268.9410 (2.29)       551.1060 (1.59)   
benchmark_select_columns[redis_store]                      313.4356 (2.36)     281.4460 (2.40)       578.7730 (1.67)   
benchmark_single_insert[redis_store-book2]                 348.5624 (2.62)     297.3610 (2.53)       580.8780 (1.67)   
benchmark_single_insert[redis_store-book1]                 342.1879 (2.57)     297.5410 (2.53)       650.5420 (1.87)   
benchmark_single_insert[redis_store-book0]                 366.4513 (2.75)     310.1640 (2.64)       660.5380 (1.90)   
benchmark_single_insert[redis_store-book3]                 377.6208 (2.84)     327.5290 (2.79)       643.4090 (1.85)   
benchmark_select_default[redis_store]                      486.6931 (3.66)     428.8810 (3.65)     1,181.9620 (3.40)   
benchmark_bulk_insert[redis_store]                         897.7862 (6.75)     848.7410 (7.23)     1,188.5160 (3.42)   
-----------------------------------------------------------------------------------------------------------------------
```

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
