# redisy

A simple declarative ORM for Redis

## ToDo
- [ ] Add Documentation
- [ ] Package for PyPi
- [ ] Add parsed filtering e.g. title < r
- [ ] Add pubsub such that for each table, there is a channel for each mutation e.g. table_name__insert, table_name__update, table_name__delete such that code can just subscribe to an given table's mutation and be updated each time a mutation occurs