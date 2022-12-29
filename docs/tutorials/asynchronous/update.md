# Update

Pydantic-redis can be used to update model instances in redis.

## Create and register the Model

A model is a class that inherits from `Model` with its `_primary_key_field` attribute set.

In order for the store to know the existence of the given model, 
register it using the `register_model` method of `Store`.

!!! warning
    The imports are from `pydantic_redis.asyncio` NOT `pydantic_redis`

```Python hl_lines="6-9 18"
{!../docs_src/tutorials/asynchronous/update.py!}
```

## Update One Record

To update a single record in redis, pass the primary key (`_id`) of that record and the new changes to the model's `update` 
method

```Python hl_lines="27"
{!../docs_src/tutorials/asynchronous/update.py!}
```

## Update One Record With TTL

To update the record's time-to-live (TTL) also, pass the `life_span_seconds` argument to the model's `update` method.

!!! info
    When the `life_span_seconds` argument is not specified, the `life_span_in_seconds` passed to the store during
    initialization is used.
    
    The `life_span_in_seconds` in both cases is `None` by default. This means records never expire by default.

```Python hl_lines="28-30"
{!../docs_src/tutorials/asynchronous/update.py!}
```

## Update/Upsert Many Records

To update many records in redis, pass a list of that model's instances as first argument to the model's
`insert` method.

Technically, this will insert any records that don't exist and overwrite any that exist already.

!!! info
    Updating many records at once is more performant than adding one record at a time repeatedly because less network requests
    are made in the former.

!!! warning
    Calling `insert` always overwrites the time-to-live of the records updated. 

    When the `life_span_seconds` argument is not specified, the `life_span_in_seconds` passed to the store during
    initialization is used. 

    By default `life_span_seconds` is `None` i.e. the time-to-live is removed and the updated records never expire.

```Python hl_lines="33-40"
{!../docs_src/tutorials/asynchronous/update.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
single update:
[   Book(title='Jane Eyre', author='Daniel McKenzie'),
    Book(title='Oliver Twist', author='Charlie Ickens'),
    Book(title='Pride and Prejudice', author='Jane Austen')]

multi update:
[   Book(title='Jane Eyre', author='Emiliano Bronte'),
    Book(title='Oliver Twist', author='Chuck Dickens'),
    Book(title='Pride and Prejudice', author='Janey Austen')]
```
</div>