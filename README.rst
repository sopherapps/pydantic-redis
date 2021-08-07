
pydantic-redis
==============

A simple declarative ORM for Redis, using aioredis. Use your Pydantic models like an ORM, storing data in Redis!

Inspired by `pydantic-redis <https://github.com/sopherapps/pydantic-redis>`_ by `Martin Ahindura <https://github.com/Tinitto>`_


.. image:: https://codecov.io/gh/andrewthetechie/pydantic-aioredis/branch/master/graph/badge.svg?token=HXSNB1D4M3
   :target: https://codecov.io/gh/andrewthetechie/pydantic-aioredis
    


Main Dependencies
-----------------


* `Python +3.6 <https://www.python.org>`_\ , 3.7, 3.8, 3.9
* `aioredis 2.0 <https://aioredis.readthedocs.io/en/latest/>`_
* `pydantic <https://github.com/samuelcolvin/pydantic/>`_

Getting Started
---------------


* 
  Install the package

  .. code-block:: bash

     pip install pydantic-redis

* 
  Import the ``Store``\ , the ``RedisConfig`` and the ``Model`` classes and use accordingly

  .. code-block:: python

     from pydantic_aioredis import RedisConfig, Model, Store

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

     async def work_with_orm():
       # Insert them into redis
       await Book.insert(books)
       await Library.insert(libraries)

       # Select all books to view them. A list of Model instances will be returned
       all_books = await Book.select()
       print(all_books) # Will print [Book(title="Oliver Twist", author="Charles Dickens", published_on=date(year=1215, month=4, day=4), in_stock=False), Book(...]

       # Or select some of the books
       some_books = await Book.select(ids=["Oliver Twist", "Jane Eyre"])
       print(some_books) # Will return only those two books

       # Or select some of the columns. THIS RETURNS DICTIONARIES not MODEL Instances
       # The Dictionaries have values in string form so you might need to do some extra work
       books_with_few_fields = await Book.select(columns=["author", "in_stock"])
       print(books_with_few_fields) # Will print [{"author": "'Charles Dickens", "in_stock": "True"},...]

       # Update any book or library
       await Book.update(_id="Oliver Twist", data={"author": "John Doe"})

       # Delete any number of items
       await Library.delete(ids=["The Grand Library"])

How to test
-----------


* 
  Clone the repo and enter its root folder

  .. code-block:: bash

     git clone https://github.com/sopherapps/pydantic-redis.git && cd pydantic-redis


* 
  Create a python 3.9 virtual environment and activate it. We suggest using `pyenv <https://github.com/pyenv/pyenv>`_ to easily setup multiple python environments on multiple versions.

  .. code-block:: bash

     # We use the extra python version (3.6, 3.7, 3.8) for tox testing
     pyenv install 3.9.6 3.6.9 3.7.11 3.8.11
     pyenv virtualenv 3.9.6 python-aioredis
     pyenv local python-aioredis 3.6.9 3.7.11 3.8.11

* 
  Install the dependencies

  .. code-block:: bash

     make setup

* 
  Run the test command to run tests on only python 3.9

  .. code-block:: bash

     make test

  or

  .. code-block:: bash

     pytest

* 
  Run the tox command to run all python version tests

  .. code-block:: bash

     make tox

  or

  .. code-block::

     tox

License
-------

Licensed under the `MIT License <./LICENSE>`_
