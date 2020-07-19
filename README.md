# redisy

A simple declarative ORM for Redis

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
  from pydantic_redis import RedisConfig, Model, Store

  # Create models as you would create pydantic models i.e. using typings
  class Book(Model):
      _primary_key_field: str = 'title'
      title: str
      author: str
      published_on: date
      in_stock: bool = True

  # Do note that there is no concept of relationships here
  class Library(Model):
      # the _primary_key_field is mandatory
      _primary_key_field: str = 'name'
      name: str
      address: str

  # Create the store and register your models
  store = Store(name='some_name', redis_config=RedisConfig(db=5, host='localhost', port=6379),life_span_in_seconds=3600)
  store.register_model(Book)
  store.register_model(Library)

  # Sample books. You can create as many as you wish anywhere in the code
  books = [
      Book(title="Oliver Twist", author='Charles Dickens', published_on=date(year=1215, month=4, day=4),
          in_stock=False),
      Book(title="Great Expectations", author='Charles Dickens', published_on=date(year=1220, month=4, day=4)),
      Book(title="Jane Eyre", author='Charles Dickens', published_on=date(year=1225, month=6, day=4), in_stock=False),
      Book(title="Wuthering Heights", author='Jane Austen', published_on=date(year=1600, month=4, day=4)),
  ]
  # Some library objects
  libraries = [
      Library(name="The Grand Library", address="Kinogozi, Hoima, Uganda"),
      Library(name="Christian Library", address="Buhimba, Hoima, Uganda")
  ]

  # Insert them into redis
  Book.insert(books)
  Library.insert(libraries)

  # Select all books to view them. A list of Model instances will be returned
  all_books = Book.select()
  print(all_books) # Will print [Book(title="Oliver Twist", author="Charles Dickens", published_on=date(year=1215, month=4, day=4), in_stock=False), Book(...]

  # Or select some of the books
  some_books = Book.select(ids=["Oliver Twist", "Jane Eyre"])
  print(some_books) # Will return only those two books

  # Or select some of the columns. THIS RETURNS DICTIONARIES not MODEL Instances
  # The Dictionaries have values in string form so you might need to do some extra work
  books_with_few_fields = Book.select(columns=["author", "in_stock"])
  print(books_with_few_fields) # Will print [{"author": "'Charles Dickens", "in_stock": "True"},...]

  # Update any book or library
  Book.update(_id="Oliver Twist", data={"author": "John Doe"})

  # Delete any number of items
  Library.delete(ids=["The Grand Library"])

  ```

## How to test

- Clone the repo and enter its root folder

  ```bash
  git clone https://github.com/sopherapps/redisy.git && cd redisy
  ```

- Ensure you have redis server installed and running at port 6379 on your development machine. Follow the [quick start guide](https://redis.io/topics/quickstart) from redis.
- Create a virtual environment and activate it

  ```bash
  virtualenv -p /usr/bin/python3.6 env && source env/bin/activate
  ```

- Install the dependencies

  ```bash
  pip install -r requirements.txt
  ```

- Run the test command

  ```bash
  python -m unittest
  ```

## ToDo

- [ ] Add parsed filtering e.g. title < r
- [ ] Add pubsub such that for each table, there is a channel for each mutation e.g. table_name**insert, table_name**update, table_name\_\_delete such that code can just subscribe to an given table's mutation and be updated each time a mutation occurs

## License

Copyright (c) 2020 [Martin Ahindura](https://github.com/Tinitto) Licensed under the [MIT License](./LICENSE)
