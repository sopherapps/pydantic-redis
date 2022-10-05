from datetime import date
from typing import Tuple, List
from pydantic_redis import RedisConfig, Model, Store


class Author(Model):
  _primary_key_field: str = 'name'
  name: str
  active_years: Tuple[int, int]

class Book(Model):
  _primary_key_field: str = 'title'
  title: str
  author: Author
  rating: float
  published_on: date
  tags: List[str] = []
  in_stock: bool = True


store = Store(name='some_name', redis_config=RedisConfig(db=0, host='localhost', port=6379))
store.register_model(Book)
store.register_model(Author)

book =  Book(title="Oliver Twist", author=Author(name="Charles Dickens", active_years=(1220, 1280)), published_on=date(year=1215, month=4, day=4), in_stock=False, rating=2, tags=["Classic"])
Book.insert([book])

# Select all books to view them. A list of Model instances will be returned
all_books = Book.select()
print(all_books)



