# Insert

Pydantic-redis can be used to insert new model instances into redis.

## Create and register the Model

A model is a class that inherits from `Model` with its `_primary_key_field` attribute set.

In order for the store to know the existence of the given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="5-8 17"
{!../docs_src/tutorials/synchronous/insert.py!}
```

## Insert One Record

To add a single record to the redis instance, pass that model's instance as first argument to the model's `insert` 
method

```Python hl_lines="19"
{!../docs_src/tutorials/synchronous/insert.py!}
```

## Insert One Record With TTL

To make the record added to redis temporary, add a `life_span_seconds` (Time To Live i.e. TTL) key-word argument 
when calling the model's `insert` method.

!!! info
    When the `life_span_seconds` argument is not specified, the `life_span_in_seconds` passed to the store during
    initialization is used.
    
    The `life_span_in_seconds` in both cases is `None` by default. This means records never expire by default.

```Python hl_lines="20-23"
{!../docs_src/tutorials/synchronous/insert.py!}
```

## Insert Many Records

To add many records to the redis instance, pass a list of that model's instances as first argument to the model's
`insert` method.

!!! info
    Adding many records at once is more performant than adding one record at a time repeatedly because less network requests
    are made in the former.

```Python hl_lines="24-29"
{!../docs_src/tutorials/synchronous/insert.py!}
```

## Insert Many Records With TTL

To add temporary records to redis, add a `life_span_seconds` (Time To Live i.e. TTL) argument 
when calling the model's `insert` method.

!!! info
    When the `life_span_seconds` argument is not specified, the `life_span_in_seconds` passed to the store during
    initialization is used.
    
    The `life_span_in_seconds` in both cases is `None` by default. This means records never expire by default.

```Python hl_lines="30-36"
{!../docs_src/tutorials/synchronous/insert.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
[   Book(title='Jane Eyre', author='Emily Bronte'),
    Book(title='Great Expectations', author='Charles Dickens'),
    Book(title='Oliver Twist', author='Charles Dickens'),
    Book(title='Pride and Prejudice', author='Jane Austen')]
```
</div>