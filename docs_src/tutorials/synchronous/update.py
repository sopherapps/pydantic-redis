import pprint
from pydantic_redis import Model, Store, RedisConfig


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: str


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(
        name="some_name", redis_config=RedisConfig(), life_span_in_seconds=86400
    )

    store.register_model(Book)

    Book.insert(
        [
            Book(title="Oliver Twist", author="Charles Dickens"),
            Book(title="Jane Eyre", author="Emily Bronte"),
            Book(title="Pride and Prejudice", author="Jane Austen"),
        ]
    )
    Book.update(_id="Oliver Twist", data={"author": "Charlie Ickens"})
    Book.update(
        _id="Jane Eyre", data={"author": "Daniel McKenzie"}, life_span_seconds=1800
    )
    single_update_response = Book.select()

    Book.insert(
        [
            Book(title="Oliver Twist", author="Chuck Dickens"),
            Book(title="Jane Eyre", author="Emiliano Bronte"),
            Book(title="Pride and Prejudice", author="Janey Austen"),
        ],
        life_span_seconds=3600,
    )
    multi_update_response = Book.select()

    print("single update:")
    pp.pprint(single_update_response)

    print("\nmulti update:")
    pp.pprint(multi_update_response)
