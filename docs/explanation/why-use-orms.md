# Why Use ORMs

An object-relational-mapping (ORM) makes writing business logic intuitive 
because the data representation is closer to what the real-life situation is. 
It helps decouple the way such data is programmed from the way such data is 
actually persisted in any of the data persistence technologies we have, 
typically a database.

Take the example of a book.
In code, one will represent a book as an object with a number of properties such as "title", "edition", "author" etc.

```python
class Book(Model):
  title: str
  edition: int
  author: Author
```

However, in the underlying data store, the same book could be saved as say,
a row in a table for a relational database like PostgreSQL,
or as a document in a document-based NoSQL databases like MongoDB 
or as a hashmap in redis.
Of these, the document-based NoSQL databases are the closest to the definition in code.

For MongoDB, the same book might be represented as the object below:

```json
{
  "id": "some-random-string",
  "title": "the title of the book",
  "edition": 2,
  "author": {
    "name": "Charles Payne",
    "yearsActive": [
      1992,
      2008
    ]
  }
}
```

As you can see, it is still quite different.

However, for redis, the representation is even going to be further off.
It will most likely be saved as hashmap, with a given key. 
The properties of book will be 'fields' for that hashmap.

In order to interact with the book representation in the redis server, 
one has to write commands like:

```shell
# to save the book in the data store
HSET "some key" "title" "the title of the book" "edition" 2 "author" "{\"name\":\"Charles Payne\",\"yearsActive\":[1992,2008]}"
# to retrieve the entire book
HGETALL "some key"
# to retrieve just a few details of the book
HMGET "some key" "title" "edition"
# to update the book - see the confusion? are you saving a new book or updating one?
HSET "some key" "edition" 2
# to delete the book
DEL "some key"
```

The above is so unrelated to the business logic that most of us 
will take a number of minutes or hours trying to understand what 
kind of data is even being saved. 

Is it a book or some random stuff?

Now consider something like this:

```python
book = Book(title="some title", edition=2, author=Author(name="Charles Payne", years_active=(1992, 2008)))
store = Store(url="redis://localhost:6379/0", pool_size=5, default_ttl=3000, timeout=1)
store.register_model(Book)

Book.insert(data=book)
response = Book.select(ids=["some title"])
Book.update(_id="some title", data={"edition": 1})
Book.delete(ids=["some title", "another title"])
```

Beautiful, isn't it?
