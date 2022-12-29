"""Synchronous API for pydantic-redis ORM.

Typical usage example:

```python
# from pydantic_redis import Store, Model, RedisConfig
from pydantic_redis.syncio import Store, Model, RedisConfig

class Book(Model):
    _primary_key_field = 'title'
    title: str

if __name__ == '__main__':
    store = Store(name="sample", redis_config=RedisConfig())
    store.register_model(Book)

    Book.insert(Book(title="Oliver Twist", author="Charles Dickens"))
    Book.update(
        _id="Oliver Twist", data={"author": "Jane Austen"}, life_span_seconds=3600
    )
    results = Book.select()
    Book.delete(ids=["Oliver Twist", "Great Expectations"])
```
"""

from .model import Model
from .store import Store
from ..config import RedisConfig

__all__ = [Model, Store, RedisConfig]
