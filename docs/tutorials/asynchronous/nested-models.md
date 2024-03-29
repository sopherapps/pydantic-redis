# Nested Models

The very first thing you need to create for pydantic-redis are the models (or schemas) that
the data you are to save in redis is to be based on.

It is possible to refer one model in another model in a parent-child relationship.

## Import Pydantic-redis' `Model`

First, import `pydantic-redis.asyncio`'s `Model`.

!!! warning
    The imports are from `pydantic_redis.asyncio` NOT `pydantic_redis`

```Python hl_lines="6"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Create the Child Model

Next, declare a new model as a class that inherits from `Model`.

Use standard Python types for all attributes.

```Python hl_lines="9-12"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Set the `_primary_key_field` of the Child Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the Model.

!!! example
    In this case, there can be no two authors with the same `name`.

```Python hl_lines="10"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Create the Parent Model

Next, declare another model as a class that inherits from `Model`.

Use standard Python types for all attributes, as before.

```Python hl_lines="15-22"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Add the Nested Model to the Parent Model

Annotate the field that is to hold the child model with the child class. 

!!! example
    In this case, the field `author` is annotated with `Author` class.

```Python hl_lines="18"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Set the `_primary_key_field` of the Parent Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the parent Model.

!!! example
    In this case, there can be no two books with the same `title`.

```Python hl_lines="16"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Register the Models in the Store

Then, in order for the store to know the existence of each given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="33-34"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Use the Parent Model

Then you can use the parent model class to:

- `insert` into the store
- `update` an instance of the model
- `delete` from store
- `select` from store

!!! note
    The child model will be automatically inserted, or updated if it already exists

!!! info
    The store is connected to the Redis instance, so any changes you make will
    reflect in redis itself.

```Python hl_lines="36-48"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Use the Child Model Independently

You can also use the child model independently.

!!! info
    Any mutation on the child model will also be reflected in the any parent model instances 
    fetched from redis after that mutation.

```Python hl_lines="50-51"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Indirectly Update Child Model

A child model can be indirectly updated via the parent model.

Set the attribute containing the child model with an instance of the child model

!!! note
    The new instance of the child model should have the **SAME** primary key as the original
    child model.

```Python hl_lines="53-57"
{!../docs_src/tutorials/asynchronous/nested-models.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
book:
[   Book(title='Oliver Twist', author=Author(name='Charles Dickens', active_years=(1999, 2007)), rating=2.0, published_on=datetime.date(1215, 4, 4), tags=['Classic'], in_stock=False)]

author:
[Author(name='Charles Dickens', active_years=(1999, 2007))]

indirectly updated book:
[   Book(title='Oliver Twist', author=Author(name='Charles Dickens', active_years=(1227, 1277)), rating=2.0, published_on=datetime.date(1215, 4, 4), tags=['Classic'], in_stock=False)]

indirectly updated author:
[Author(name='Charles Dickens', active_years=(1969, 1999))]
```
</div>
