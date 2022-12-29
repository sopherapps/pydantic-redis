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

    Book.insert(Book(title="Oliver Twist", author="Charles Dickens"))
    Book.insert(
        Book(title="Great Expectations", author="Charles Dickens"),
        life_span_seconds=1800,
    )
    Book.insert(
        [
            Book(title="Jane Eyre", author="Emily Bronte"),
            Book(title="Pride and Prejudice", author="Jane Austen"),
        ]
    )
    Book.insert(
        [
            Book(title="Jane Eyre", author="Emily Bronte"),
            Book(title="Pride and Prejudice", author="Jane Austen"),
        ],
        life_span_seconds=3600,
    )

    response = Book.select()
    pp.pprint(response)
