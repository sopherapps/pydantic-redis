"""Asynchronous API for pydantic-redis ORM.

Typical usage example:

```python
import asyncio
from pydantic_redis.asyncio import Store, Model, RedisConfig

class Book(Model):
    _primary_key_field = 'title'
    title: str

async def main():
    store = Store(name="sample", redis_config=RedisConfig())
    store.register_model(Book)

    await Book.insert(Book(title="Oliver Twist", author="Charles Dickens"))
    await Book.update(
        _id="Oliver Twist", data={"author": "Jane Austen"}, life_span_seconds=3600
    )
    results = await Book.select()
    await Book.delete(ids=["Oliver Twist", "Great Expectations"])

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```
"""

from .model import Model
from .store import Store
from ..config import RedisConfig

__all__ = [Model, Store, RedisConfig]
