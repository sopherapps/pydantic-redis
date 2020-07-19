# redisy

A simple declarative ORM for Redis

## Main Dependencies

- [Python +3.6](https://www.python.org)
- [redis](https://pypi.org/project/redis/)
- [pydantic](https://github.com/samuelcolvin/pydantic/)

## How to test

- Clone the repo and enter its root folder

  ```bash
  git clone https://github.com/sopherapps/redisy.git && cd redisy
  ```

- Ensure you have redis server installed and running at port 6379 on your development machine. Follow the [quick start guide](https://redis.io/topics/quickstart) from redis.
- Create a virtual environment and activate it

  ```bash
  virtualenv -p /usr/bin/python3.6 env && source env/bin/activate
  ```

- Install the dependencies

  ```bash
  pip install -r requirements.txt
  ```

- Run the test command

  ```bash
  python -m unittest
  ```

## ToDo

- [ ] Add Documentation
- [ ] Package for PyPi
- [ ] Add parsed filtering e.g. title < r
- [ ] Add pubsub such that for each table, there is a channel for each mutation e.g. table_name**insert, table_name**update, table_name\_\_delete such that code can just subscribe to an given table's mutation and be updated each time a mutation occurs

## License

Copyright (c) 2020 [Martin Ahindura](https://github.com/Tinitto) Licensed under the [MIT License](./LICENSE)
