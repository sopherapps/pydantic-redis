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
            Book(title="Utah Blaine", author="Louis L'Amour"),
        ]
    )

    select_all_response = Book.select()
    select_by_id_response = Book.select(ids=["Oliver Twist", "Pride and Prejudice"])

    select_some_fields_response = Book.select(columns=["author"])
    select_some_fields_for_ids_response = Book.select(
        ids=["Oliver Twist", "Pride and Prejudice"], columns=["author"]
    )

    paginated_select_all_response = Book.select(skip=0, limit=2)
    paginated_select_some_fields_response = Book.select(
        columns=["author"], skip=2, limit=2
    )

    print("all:")
    pp.pprint(select_all_response)
    print("\nby id:")
    pp.pprint(select_by_id_response)
    print("\nsome fields for all:")
    pp.pprint(select_some_fields_response)
    print("\nsome fields for given ids:")
    pp.pprint(select_some_fields_for_ids_response)
    print("\npaginated; skip: 0, limit: 2:")
    pp.pprint(paginated_select_all_response)
    print("\npaginated returning some fields for each; skip: 2, limit: 2:")
    pp.pprint(paginated_select_some_fields_response)
