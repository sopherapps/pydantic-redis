# Intro

This tutorial shows you how to use **pydantic-redis** step by step.

There are two tutorials: Synchronous API and Asynchronous API.

In either tutorials, each child section gradually builds on the previous one. These child sections are separate topics
so that one can go directly to a specific topic, just like a reference.

## Synchronous API

In case you are looking to use pydantic-redis without async/await, you can read the **Synchronous API** version of this
tutorial.

!!! info
    This is the default API for pydantic-redis.

## Asynchronous API

In case you are looking to use pydantic-redis with async/await, e.g. in [FastAPI](https://fastapi.tiangolo.com)
or [asyncio](https://docs.python.org/3/library/asyncio.html) , you can read the **Asynchronous API** version of this
tutorial.

## Install Python

Pydantic-redis requires python 3.8 and above. The latest stable python version is the recommended version.

You can install python from [the official python downloads site](https://www.python.org/downloads/).

## Install Redis

In order to use pydantic-redis, you need a redis server instance running. You can install a local instance
via [the official redis stack](https://redis.io/docs/stack/get-started/install/) instructions.

!!! info
    You may also need a visual client to view the data in redis. The recommended app to use
    is [RedisInsight](https://redis.com/redis-enterprise/redis-insight/).

## Run the Code

All the code blocks can be copied and used directly.

To run any of the examples, copy the code to a file `main.py`, and run the command below in your terminal:

<div class="termy">

```console
$ python main.py
```

</div>

## Install Pydantic-redis

First install pydantic-redis

<div class="termy">

```console
$ pip install pydantic-redis

---> 100%
```

</div>
