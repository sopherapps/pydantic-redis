# Delete

Pydantic-redis can be used to delete model instances from redis.

## Create and register the Model

A model is a class that inherits from `Model` with its `_primary_key_field` attribute set.

In order for the store to know the existence of the given model, 
register it using the `register_model` method of `Store`

```Python hl_lines="5-8 17"
{!../docs_src/tutorials/synchronous/delete.py!}
```

## Delete Records

To delete many records from redis, pass a list of primary keys (`ids`) of the records to the model's `delete` method.

```Python hl_lines="29"
{!../docs_src/tutorials/synchronous/delete.py!}
```

## Run the App

Running the above code in a file `main.py` would produce:

!!! tip
    Probably [FLUSHALL](https://redis.io/commands/flushall/) redis first

<div class="termy">

```console
$ python main.py
pre-delete:
[   Book(title='Jane Eyre', author='Emily Bronte'),
    Book(title='Oliver Twist', author='Charles Dickens'),
    Book(title='Utah Blaine', author="Louis L'Amour"),
    Book(title='Pride and Prejudice', author='Jane Austen')]

post-delete:
[   Book(title='Jane Eyre', author='Emily Bronte'),
    Book(title='Utah Blaine', author="Louis L'Amour")]
```
</div>