"""Module containing the store classes"""
from typing import Dict, Optional, Any

import redis

from pydantic_redis.abstract import _AbstractStore
from pydantic_redis.config import RedisConfig
from pydantic_redis.model import Model

SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT = """
local filtered = {}
local cursor = '0'
local table_unpack = table.unpack or unpack
local columns = {  }
local nested_columns = {}
local args_tracker = {}

for i, k in ipairs(ARGV) do
    if i > 1 then
        if args_tracker[k] then
            nested_columns[k] = true
        else
            table.insert(columns, k)
            args_tracker[k] = true
        end
    end
end

repeat
    local result = redis.call('SCAN', cursor, 'MATCH', ARGV[1])
    for _, key in ipairs(result[2]) do
        if redis.call('TYPE', key).ok == 'hash' then
            local data = redis.call('HMGET', key, table_unpack(columns))
            local parsed_data = {}

            for i, v in ipairs(data) do
                table.insert(parsed_data, columns[i])

                if nested_columns[columns[i]] then
                    v = redis.call('HGETALL', v)
                end

                table.insert(parsed_data, v)
            end

            table.insert(filtered, parsed_data)
        end
    end
    cursor = result[1]
until (cursor == '0')
return filtered
"""
SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT = """
local filtered = {}
local cursor = '0'
local nested_fields = {}

for i, key in ipairs(ARGV) do
    if i > 1 then
        nested_fields[key] = true
    end
end

repeat
    local result = redis.call('SCAN', cursor, 'MATCH', ARGV[1])
    for _, key in ipairs(result[2]) do
        if redis.call('TYPE', key).ok == 'hash' then
            local parent = redis.call('HGETALL', key)

            for i, k in ipairs(parent) do
                if nested_fields[k] then
                    local nested = redis.call('HGETALL', parent[i + 1])
                    parent[i + 1] = nested
                end
            end

            table.insert(filtered, parent)
        end
    end
    cursor = result[1]
until (cursor == '0')
return filtered
"""
SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT = """
local result = {}
local nested_fields = {}

for _, key in ipairs(ARGV) do
    nested_fields[key] = true
end

for _, key in ipairs(KEYS) do
    local parent = redis.call('HGETALL', key)

    for i, k in ipairs(parent) do
        if nested_fields[k] then
            local nested = redis.call('HGETALL', parent[i + 1])
            parent[i + 1] = nested
        end
    end

    table.insert(result, parent)
end
return result
"""
SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT = """
local result = {}
local table_unpack = table.unpack or unpack
local columns = {  }
local nested_columns = {}
local args_tracker = {}

for i, k in ipairs(ARGV) do
    if args_tracker[k] then
        nested_columns[k] = true
    else
        table.insert(columns, k)
        args_tracker[k] = true
    end
end

for _, key in ipairs(KEYS) do
    local data = redis.call('HMGET', key, table_unpack(columns))
    local parsed_data = {}

    for i, v in ipairs(data) do
        if v then
            table.insert(parsed_data, columns[i])

            if nested_columns[columns[i]] then
                v = redis.call('HGETALL', v)
            end

            table.insert(parsed_data, v)
        end
    end

    table.insert(result, parsed_data)
end
return result
"""


class Store(_AbstractStore):
    """
    A store that allows a declarative way of querying for data in redis
    """

    models: Dict[str, type(Model)] = {}

    def __init__(
        self,
        name: str,
        redis_config: RedisConfig,
        redis_store: Optional[redis.Redis] = None,
        life_span_in_seconds: Optional[int] = None,
        **data: Any,
    ):
        super().__init__(
            name=name,
            redis_config=redis_config,
            redis_store=redis_store,
            life_span_in_seconds=life_span_in_seconds,
            **data,
        )

        self.redis_store = redis.from_url(
            self.redis_config.redis_url,
            encoding=self.redis_config.encoding,
            decode_responses=True,
        )

        # register lua scripts
        self.select_all_fields_for_all_ids_script = self.redis_store.register_script(
            SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT
        )
        self.select_all_fields_for_some_ids_script = self.redis_store.register_script(
            SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT
        )
        self.select_some_fields_for_all_ids_script = self.redis_store.register_script(
            SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT
        )
        self.select_some_fields_for_some_ids_script = self.redis_store.register_script(
            SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT
        )

    def register_model(self, model_class: type(Model)):
        """Registers the model to this store"""
        if not isinstance(model_class.get_primary_key_field(), str):
            raise NotImplementedError(
                f"{model_class.__name__} should have a _primary_key_field"
            )

        model_class._store = self
        model_class.initialize()
        self.models[model_class.__name__.lower()] = model_class

    def model(self, name: str) -> Model:
        """Gets a model by name: case insensitive"""
        return self.models[name.lower()]
