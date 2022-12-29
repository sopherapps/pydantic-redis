import asyncio
import pprint
from datetime import date
from typing import List

from pydantic_redis.asyncio import Model, Store, RedisConfig


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: str
    rating: float
    published_on: date
    tags: List[str] = []
    in_stock: bool = True


async def main():
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(
        name="some_name",
        redis_config=RedisConfig(db=5, host="localhost", port=6379),
        life_span_in_seconds=3600,
    )

    store.register_model(Book)

    await Book.insert(
        Book(
            title="Oliver Twist",
            author="Charles Dickens",
            published_on=date(year=1215, month=4, day=4),
            in_stock=False,
            rating=2,
            tags=["Classic"],
        )
    )

    response = await Book.select(ids=["Oliver Twist"])
    pp.pprint(response)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
