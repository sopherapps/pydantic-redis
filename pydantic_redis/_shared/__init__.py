"""Shared utilities and base classes for pydantic-redis

This includes basic functionality of mutating and querying
redis via the pydantic-redis ORM regardless of whether this
is done asynchronously or synchronously.
This is a private package.

Available subpackages
---------------------
model
    defines the base `AbstractModel` class to be extended by async
    and sync versions of the `Model` class

Available modules
-----------------
config
    defines the `RedisConfig` class to be used to make a
    connection to a redis server
lua_scripts
    defines the lua scripts to be used in querying redis
store
    defines the base `AbstractStore` class to be extended by the
    async and sync versions of the `Store` class
utils
    defines utility functions used across the project
"""
