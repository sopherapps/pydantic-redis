# Pydantic-redis

A simple declarative ORM for redis based on pydantic

## Features

1. A subclass-able `Model` class to create Object Relational Mapping to redis hashes
2. A redis `Store` class to mutate and query `Model`'s registered in it
3. A `RedisConfig` class to pass to the `Store` constructor to connect to a redis instance
4. A synchronous `syncio` and an asynchronous `asyncio` interface to the above classes

### Installation
<div class="termy">

```console
$ pip install pydantic-redis

---> 100%
```
</div>

### Synchronous Example

#### Create it

- Create a file `main.py` with:

```Python
{!../docs_src/index/sync_main.py!}
```

#### Run it

Run the example with:

<div class="termy">

```console
$ python main.py
All:
[   Book(title='Wuthering Heights', author=Author(name='Jane Austen', active_years=(1580, 1640)), rating=4.0, published_on=datetime.date(1600, 4, 4), tags=['Classic', 'Romance'], in_stock=True),
    Book(title='Oliver Twist', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=2.0, published_on=datetime.date(1215, 4, 4), tags=['Classic'], in_stock=False),
    Book(title='Jane Eyre', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=3.4, published_on=datetime.date(1225, 6, 4), tags=['Classic', 'Romance'], in_stock=False),
    Book(title='Great Expectations', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=5.0, published_on=datetime.date(1220, 4, 4), tags=['Classic'], in_stock=True)]

Paginated:
[   Book(title='Jane Eyre', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=3.4, published_on=datetime.date(1225, 6, 4), tags=['Classic', 'Romance'], in_stock=False),
    Book(title='Wuthering Heights', author=Author(name='Jane Austen', active_years=(1580, 1640)), rating=4.0, published_on=datetime.date(1600, 4, 4), tags=['Classic', 'Romance'], in_stock=True)]

Paginated but with few fields:
[   {   'author': Author(name='Charles Dickens', active_years=(1220, 1280)),
        'in_stock': False},
    {   'author': Author(name='Jane Austen', active_years=(1580, 1640)),
        'in_stock': True}]
```
</div>

### Asynchronous Example

#### Create it

- Create a file `main.py` with:

```Python
{!../docs_src/index/async_main.py!}
```

#### Run it

Run the example with:

<div class="termy">

```console
$ python main.py
All:
[   Book(title='Wuthering Heights', author=Author(name='Jane Austen', active_years=(1580, 1640)), rating=4.0, published_on=datetime.date(1600, 4, 4), tags=['Classic', 'Romance'], in_stock=True),
    Book(title='Oliver Twist', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=2.0, published_on=datetime.date(1215, 4, 4), tags=['Classic'], in_stock=False),
    Book(title='Jane Eyre', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=3.4, published_on=datetime.date(1225, 6, 4), tags=['Classic', 'Romance'], in_stock=False),
    Book(title='Great Expectations', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=5.0, published_on=datetime.date(1220, 4, 4), tags=['Classic'], in_stock=True)]

Paginated:
[   Book(title='Jane Eyre', author=Author(name='Charles Dickens', active_years=(1220, 1280)), rating=3.4, published_on=datetime.date(1225, 6, 4), tags=['Classic', 'Romance'], in_stock=False),
    Book(title='Wuthering Heights', author=Author(name='Jane Austen', active_years=(1580, 1640)), rating=4.0, published_on=datetime.date(1600, 4, 4), tags=['Classic', 'Romance'], in_stock=True)]

Paginated but with few fields:
[   {   'author': Author(name='Charles Dickens', active_years=(1220, 1280)),
        'in_stock': False},
    {   'author': Author(name='Jane Austen', active_years=(1580, 1640)),
        'in_stock': True}]
```
</div>
