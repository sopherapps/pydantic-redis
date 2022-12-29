# Tuples of Nested Models

Sometimes, one might need to have models (schemas) that have tuples of other models (schemas).

An example is a `ScoreBoard` model that can have Tuples of player name and `Scores`'.

This can easily be pulled off with pydantic-redis.

## Import Pydantic-redis' `Model`

First, import pydantic-redis' `Model`

```Python hl_lines="3"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Create the Child Model

Next, declare a new model as a class that inherits from `Model`.

Use standard Python types for all attributes.

```Python hl_lines="6-9"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Set the `_primary_key_field` of the Child Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the Model.

!!! example
    In this case, there can be no two `Score`'s with the same `id`.

```Python hl_lines="7"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Create the Parent Model

Next, declare another model as a class that inherits from `Model`.

Use standard Python types for all attributes, as before.

```Python hl_lines="12-15"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Add the Nested Model Tuple to the Parent Model

Annotate the field that is to hold the tuple of child models with the Tuple of child class. 

!!! example
    In this case, the field `scores` is annotated with `Tuple[str, Score]` class.

!!! info
    The `str` is the player's name.

```Python hl_lines="15"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Set the `_primary_key_field` of the Parent Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the parent Model.

!!! example
    In this case, there can be no two `ScoreBoard`'s with the same `id`.

```Python hl_lines="13"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Register the Models in the Store

Then, in order for the store to know the existence of each given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="22-23"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Use the Parent Model

Then you can use the parent model class to:

- `insert` into the store
- `update` an instance of the model
- `delete` from store
- `select` from store

!!! info
    The child models will be automatically inserted, or updated if they already exist

!!! info
    The store is connected to the Redis instance, so any changes you make will
    reflect in redis itself.

```Python hl_lines="25-35"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Use the Child Model Independently

You can also use the child model independently.

!!! info
    Any mutation on the child model will also be reflected in the any parent model instances 
    fetched from redis after that mutation.

```Python hl_lines="37-38"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Indirectly Update Child Model

A child model can be indirectly updated via the parent model.

Set the attribute containing the child model tuple with a tuple of instances of the child model 

If there is any new instance of the child model that has a pre-existing primary key, it will be updated in redis.

```Python hl_lines="40-49"
{!../docs_src/tutorials/synchronous/tuple-of-nested-models.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
score board:
[ScoreBoard(id='test', scores=('mark', Score(id='some id', total=50)))]

scores:
[Score(id='some id', total=50)]

indirectly updated score board:
[ScoreBoard(id='test', scores=('mark', Score(id='some id', total=78)))]

indirectly updated score:
[Score(id='some id', total=60)]
```
</div>
