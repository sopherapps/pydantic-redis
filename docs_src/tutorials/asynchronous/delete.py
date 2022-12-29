import asyncio
import pprint
from pydantic_redis.asyncio import Model, Store, RedisConfig


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: str


async def main():
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(
        name="some_name", redis_config=RedisConfig(), life_span_in_seconds=86400
    )

    store.register_model(Book)

    await Book.insert(
        [
            Book(title="Oliver Twist", author="Charles Dickens"),
            Book(title="Jane Eyre", author="Emily Bronte"),
            Book(title="Pride and Prejudice", author="Jane Austen"),
            Book(title="Utah Blaine", author="Louis L'Amour"),
        ]
    )
    pre_delete_response = await Book.select()

    await Book.delete(ids=["Oliver Twist", "Pride and Prejudice"])
    post_delete_response = await Book.select()

    print("pre-delete:")
    pp.pprint(pre_delete_response)

    print("\npost-delete:")
    pp.pprint(post_delete_response)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
