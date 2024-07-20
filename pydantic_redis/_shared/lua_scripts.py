"""Exposes the redis lua scripts to be used in select queries.

These scripts always return a list of tuples of [record, index] where the index is a flat list of nested models
for that record

Attributes:
    SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT: the script for selecting all records from redis
    PAGINATED_SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT: the script for selecting a slice of all records from redis,
        given a `limit` maximum number of records to return and a `skip` number of records to skip.
    SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT: the script for selecting some records from redis, given a bunch of `ids`
    SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT: the script for selecting all records, but returning only a subset of
        the fields in each record.
    PAGINATED_SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT: the script for selecting a slice of all records from redis,
        given a `limit` maximum number of records to return and a `skip` number of records to skip, but returning
        only a subset of the fields in each record.
    SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT: the script for selecting some records from redis, given a bunch of `ids`,
        but returning only a subset of the fields in each record.
"""

# What if instead of constructing tables, we return obj as a JSON string

SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call

local filtered = {}
local cursor = '0'

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
            
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

repeat
    local result = redis_call('SCAN', cursor, 'MATCH', ARGV[1])
    for _, key in ipairs(result[2]) do
        if redis_call('TYPE', key).ok == 'hash' then
            local value, idx = get_obj_and_index(key)
            if type(value) == 'table' then
                table_insert(filtered, {value, idx})
            end
        end
    end
    cursor = result[1]
until (cursor == '0')
return filtered
"""

PAGINATED_SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

local table_index_key = ARGV[1]
local start = ARGV[2]
local stop = ARGV[3] + start - 1
local result = {}

local ids = redis_call('ZRANGE', table_index_key, start, stop)

for _, key in ipairs(ids) do
    local value, idx = get_obj_and_index(key)
    if type(value) == 'table' then
        table_insert(result, {value, idx})
    end
end

return result
"""

SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call

local result = {}

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

for _, key in ipairs(KEYS) do
    local value, idx = get_obj_and_index(key)
    if type(value) == 'table' then
        table_insert(result, {value, idx})
    end
end

return result
"""

SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call
local table_unpack = table.unpack or unpack

local filtered = {}
local cursor = '0'
local columns = {}

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

for i, k in ipairs(ARGV) do
    if i > 1 then
        table_insert(columns, k)
    end
end

repeat
    local result = redis_call('SCAN', cursor, 'MATCH', ARGV[1])
    for _, key in ipairs(result[2]) do
        if redis_call('TYPE', key).ok == 'hash' then
            local data = redis_call('HMGET', key, table_unpack(columns))
            local parsed_data = {}
            local index = {}

            for i, v in ipairs(data) do
                table_insert(parsed_data, columns[i])
                table_insert(parsed_data, v)
                    
                local value, idx = get_obj_and_index(v)
                if type(idx) == 'table' then
                    table_insert(index, v)
                    table_insert(index, {value, idx})
                end
            end
        
            table_insert(filtered, {parsed_data, index})
        end
    end
    cursor = result[1]
until (cursor == '0')
return filtered
"""

PAGINATED_SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call
local table_unpack = table.unpack or unpack

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

local result = {}
local columns = {}
local table_index_key = ARGV[1]
local start = ARGV[2]
local stop = ARGV[3] + start - 1

for i, k in ipairs(ARGV) do
    if i > 3 then
        table_insert(columns, k)
    end
end

local ids = redis_call('ZRANGE', table_index_key, start, stop)

for _, key in ipairs(ids) do
    local data = redis_call('HMGET', key, table_unpack(columns))
    local parsed_data = {}
    local index = {}

    for i, v in ipairs(data) do
        if v then
            table_insert(parsed_data, columns[i])
            table_insert(parsed_data, v)
            
            local value, idx = get_obj_and_index(v)
            if type(idx) == 'table' then
                table_insert(index, v)
                table_insert(index, {value, idx})
            end
        end
    end

    table_insert(result, {parsed_data, index})

end

return result
"""

SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT = """
local s_find = string.find
local s_gmatch = string.gmatch
local ipairs = ipairs
local table_insert = table.insert
local next = next
local redis_call = redis.call
local table_unpack = table.unpack or unpack

local result = {}
local columns = {}

local function startswith(s, prefix)
    return s_find(s, prefix, 1, true) == 1
end

local function get_obj_and_index(id)
    local value = redis_call('HGETALL', id)
    local idx = {}

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if value[i + 1] == 'null' then
            elseif startswith(k, '___') then
               for v in s_gmatch(value[i + 1], '\"([%w_]+_%%&_[^\"%[%]]+)\"') do
                   table_insert(idx, v)
                   table_insert(idx, {get_obj_and_index(v)})
               end
            elseif startswith(k, '__') then
               table_insert(idx, value[i + 1])
               table_insert(idx, {get_obj_and_index(value[i + 1])})
            end
       end
    end

    if next(value) == nil then
        return id, nil
    end
    return value, idx
end

for _, k in ipairs(ARGV) do
    table_insert(columns, k)
end

for _, key in ipairs(KEYS) do
    local data = redis_call('HMGET', key, table_unpack(columns))
    local parsed_data = {}
    local index = {}

    for i, v in ipairs(data) do
        if v then
            table_insert(parsed_data, columns[i])
            table_insert(parsed_data, v)
            
            local value, idx = get_obj_and_index(v)
            if type(idx) == 'table' then
                table_insert(index, v)
                table_insert(index, {value, idx})
            end
        end
    end

    table_insert(result, {parsed_data, index})
end
return result
"""
