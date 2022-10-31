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
