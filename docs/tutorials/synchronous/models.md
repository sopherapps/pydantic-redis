# Models

The very first thing you need to create for pydantic-redis are the models (or schemas) that
the data you are to save in redis is to be based on.

These models are derived from [pydantic's](https://docs.pydantic.dev/) `BaseModel`.

## Import Pydantic-redis' `Model`

First, import pydantic-redis' `Model`

```Python hl_lines="5"
{!../docs_src/tutorials/synchronous/models.py!}
```

## Create the Model

Next, declare a new model as a class that inherits from `Model`.

Use standard Python types for all attributes.

```Python hl_lines="8-15"
{!../docs_src/tutorials/synchronous/models.py!}
```

## Specify the `_primary_key_field` Attribute

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the Model.

In this case, there can be no two books with the same `title`.

```Python hl_lines="9"
{!../docs_src/tutorials/synchronous/models.py!}
```

## Register the Model in the Store

Then, in order for the store to know the existence of the given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="26"
{!../docs_src/tutorials/synchronous/models.py!}
```

## Use the Model

Then you can use the model class to:

- `insert` into the store
- `update` an instance of the model
- `delete` from store
- `select` from store

The store is connected to the Redis instance, so any changes you make will
reflect in redis itself.

```Python hl_lines="28-39"
{!../docs_src/tutorials/synchronous/models.py!}
```

## Run the App

Running the above code in a file `main.py` would produce
(Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first)::

<div class="termy">

```console
$ python main.py
[   Book(title='Oliver Twist', author='Charles Dickens', rating=2.0, published_on=datetime.date(1215, 4, 4), tags=['Classic'], in_stock=False)]
```
</div>