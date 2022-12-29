# Lists of Nested Models

Sometimes, one might need to have models (schemas) that have lists of other models (schemas).

An example is a `Folder` model that can have child `Folder`'s and `File`'s.

This can easily be pulled off with pydantic-redis.

## Import Pydantic-redis' `Model`

First, import `pydantic-redis.asyncio`'s `Model`

!!! warning
    The imports are from `pydantic_redis.asyncio` NOT `pydantic_redis`

```Python hl_lines="6"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Create the Child Model

Next, declare a new model as a class that inherits from `Model`.

Use standard Python types for all attributes.

```Python hl_lines="15-18"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Set the `_primary_key_field` of the Child Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the Model.

!!! example
    In this case, there can be no two `File`'s with the same `path`.

```Python hl_lines="16"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Create the Parent Model

Next, declare another model as a class that inherits from `Model`.

Use standard Python types for all attributes, as before.

```Python hl_lines="21-25"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Add the Nested Model List to the Parent Model

Annotate the field that is to hold the child model list with the List of child class. 

!!! example
    In this case, the field `files` is annotated with `List[File]`.
    
    And the field `folders` is annotated with `"Folder"` class i.e. itself.

```Python hl_lines="24-25"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Set the `_primary_key_field` of the Parent Model

Set the `_primary_key_field` attribute to the name of the attribute
that is to act as a unique identifier for each instance of the parent Model.

!!! example
    In this case, there can be no two `Folder`'s with the same `path`.

```Python hl_lines="22"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Register the Models in the Store

Then, in order for the store to know the existence of each given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="36-37"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
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

```Python hl_lines="39-61"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Use the Child Model Independently

You can also use the child model independently.

!!! info
    Any mutation on the child model will also be reflected in the any parent model instances 
    fetched from redis after that mutation.

```Python hl_lines="63-68"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Indirectly Update Child Model

A child model can be indirectly updated via the parent model.

Set the attribute containing the child model list with a list of instances of the child model 

If there is any new instance of the child model that has a pre-existing primary key, it will be updated in redis.

```Python hl_lines="63-66"
{!../docs_src/tutorials/asynchronous/list-of-nested-models.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
parent folder:
[   Folder(path='path/to/parent-folder', files=[File(path='path/to/bar.txt', type=<FileType.TEXT: 'text'>), File(path='path/to/bar.jpg', type=<FileType.IMAGE: 'image'>)], folders=[Folder(path='path/to/child-folder', files=[File(path='path/to/foo.txt', type=<FileType.TEXT: 'text'>), File(path='path/to/foo.jpg', type=<FileType.IMAGE: 'image'>)], folders=[])])]

files:
[   File(path='path/to/foo.txt', type=<FileType.TEXT: 'text'>),
    File(path='path/to/foo.jpg', type=<FileType.IMAGE: 'image'>),
    File(path='path/to/bar.txt', type=<FileType.TEXT: 'text'>),
    File(path='path/to/bar.jpg', type=<FileType.IMAGE: 'image'>)]

indirectly updated parent folder:
[   Folder(path='path/to/parent-folder', files=[File(path='path/to/bar.txt', type=<FileType.TEXT: 'text'>), File(path='path/to/bar.jpg', type=<FileType.IMAGE: 'image'>)], folders=[Folder(path='path/to/child-folder', files=[File(path='path/to/foo.txt', type=<FileType.EXEC: 'executable'>)], folders=[])])]

indirectly updated files:
[File(path='path/to/foo.txt', type=<FileType.EXEC: 'executable'>)]
```
</div>
