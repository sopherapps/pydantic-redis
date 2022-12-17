"""Module containing the lua scripts used in select queries"""

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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
end

repeat
    local result = redis_call('SCAN', cursor, 'MATCH', ARGV[1])
    for _, key in ipairs(result[2]) do
        if redis_call('TYPE', key).ok == 'hash' then
            table_insert(filtered, get_obj(key))
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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
end

local table_index_key = ARGV[1]
local start = ARGV[2]
local stop = ARGV[3] + start - 1
local result = {}

local ids = redis_call('ZRANGE', table_index_key, start, stop)

for _, key in ipairs(ids) do
    local value = get_obj(key)
    if type(value) == 'table' then
        table_insert(result, value)
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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
end

for _, key in ipairs(KEYS) do
    local value = get_obj(key)
    if type(value) == 'table' then
        table_insert(result, value)
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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
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

            for i, v in ipairs(data) do
                table_insert(parsed_data, trim_dunder(columns[i]))
                table_insert(parsed_data, get_obj(v))
            end

            table_insert(filtered, parsed_data)
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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
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

    for i, v in ipairs(data) do
        if v then
            table_insert(parsed_data, trim_dunder(columns[i]))
            table_insert(parsed_data, get_obj(v))
        end
    end

    table_insert(result, parsed_data)
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

local function trim_dunder(s)
    return s:match '^_*(.-)$'
end

local function get_obj(id)
    local value = redis_call('HGETALL', id)

    for i, k in ipairs(value) do
        if not (i % 2 == 0) then
            if startswith(k, '___') or startswith(k, '____') then
                local nested = {}

                for v in s_gmatch(value[i + 1], '([^%[^,^%]^\"]+)') do
                    table_insert(nested, get_obj(v))
                end

                value[i + 1] = nested
                value[i] = trim_dunder(k)
            elseif startswith(k, '__') then
                value[i + 1] = get_obj(value[i + 1])
                value[i] = trim_dunder(k)
            end
        end
    end

    if next(value) == nil then
        return id
    end

    return value
end

for _, k in ipairs(ARGV) do
    table_insert(columns, k)
end

for _, key in ipairs(KEYS) do
    local data = redis_call('HMGET', key, table_unpack(columns))
    local parsed_data = {}

    for i, v in ipairs(data) do
        if v then
            table_insert(parsed_data, trim_dunder(columns[i]))
            table_insert(parsed_data, get_obj(v))
        end
    end

    table_insert(result, parsed_data)
end
return result
"""
