# Select

Pydantic-redis can be used to retrieve model instances from redis.

## Create and register the Model

A model is a class that inherits from `Model` with its `_primary_key_field` attribute set.

In order for the store to know the existence of the given model, 
register it using the `register_model` method of `Store`.

!!! warning
    The imports are from `pydantic_redis.asyncio` NOT `pydantic_redis`

```Python hl_lines="6-9 18"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Select All Records

To select all records for the given model in redis, call the model's `select` method without any arguments.

```Python hl_lines="29"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Select Some Fields for All Records

To select some fields for all records for the given model in redis, pass the desired fields (`columns`) to the model's 
`select` method.

!!! info
    This returns dictionaries instead of Model instances.

```Python hl_lines="34"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Select Some Records

To select some records for the given model in redis, pass a list of the primary keys (`ids`) of the desired records to 
the model's `select` method.

```Python hl_lines="30-32"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Select Some Fields for Some Records

We can go further and limit the fields returned for the desired records.

We pass the desired fields (`columns`) to the model's `select` method, together with the list of the primary keys 
(`ids`) of the desired records.

!!! info
    This returns dictionaries instead of Model instances.

```Python hl_lines="35-37"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Select Records Page by Page 

In order to avoid overwhelming the server's memory resources, we can get the records one page at a time i.e. pagination.

We do this by specifying the number of records per page (`limit`) and the number of records to skip (`skip`) 
when calling the model's `select` method

!!! info
    Records are ordered by timestamp of their insert into redis. 
    
    For batch inserts, the time difference is quite small but consistent. 

!!! tip
    You don't have to pass the `skip` if you wish to get the first records. `skip` defaults to 0.
    
    `limit`, however is mandatory.

!!! warning
    When both `ids` and `limit` are supplied, pagination is ignored. 

    It wouldn't make any sense otherwise.

```Python hl_lines="39-42"
{!../docs_src/tutorials/asynchronous/select-records.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
all:
[   Book(title='Oliver Twist', author='Charles Dickens'),
    Book(title='Utah Blaine', author="Louis L'Amour"),
    Book(title='Jane Eyre', author='Emily Bronte'),
    Book(title='Pride and Prejudice', author='Jane Austen')]

by id:
[   Book(title='Oliver Twist', author='Charles Dickens'),
    Book(title='Pride and Prejudice', author='Jane Austen')]

some fields for all:
[   {'author': 'Charles Dickens'},
    {'author': "Louis L'Amour"},
    {'author': 'Emily Bronte'},
    {'author': 'Jane Austen'}]

some fields for given ids:
[{'author': 'Charles Dickens'}, {'author': 'Jane Austen'}]

paginated; skip: 0, limit: 2:
[   Book(title='Oliver Twist', author='Charles Dickens'),
    Book(title='Jane Eyre', author='Emily Bronte')]

paginated returning some fields for each; skip: 2, limit: 2:
[{'author': 'Jane Austen'}, {'author': "Louis L'Amour"}]
```
</div>