import asyncio
import pprint
from datetime import date
from typing import List, Tuple

from pydantic_redis.asyncio import Model, Store, RedisConfig


class Author(Model):
    _primary_key_field: str = "name"
    name: str
    active_years: Tuple[int, int]


class Book(Model):
    _primary_key_field: str = "title"
    title: str
    author: Author
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

    store.register_model(Author)
    store.register_model(Book)

    await Book.insert(
        Book(
            title="Oliver Twist",
            author=Author(name="Charles Dickens", active_years=(1999, 2007)),
            published_on=date(year=1215, month=4, day=4),
            in_stock=False,
            rating=2,
            tags=["Classic"],
        )
    )

    book_response = await Book.select(ids=["Oliver Twist"])
    author_response = await Author.select(ids=["Charles Dickens"])

    await Author.update(_id="Charles Dickens", data={"active_years": (1227, 1277)})
    updated_book_response = await Book.select(ids=["Oliver Twist"])

    await Book.update(
        _id="Oliver Twist",
        data={"author": Author(name="Charles Dickens", active_years=(1969, 1999))},
    )
    updated_author_response = await Author.select(ids=["Charles Dickens"])

    print("book:")
    pp.pprint(book_response)
    print("\nauthor:")
    pp.pprint(author_response)

    print("\nindirectly updated book:")
    pp.pprint(updated_book_response)
    print("\nindirectly updated author:")
    pp.pprint(updated_author_response)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
