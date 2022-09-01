"""Module containing the model classes"""
import typing
import uuid
from typing import Optional, List, Any, Union, Dict, Tuple

from redis.client import Pipeline

from pydantic_redis.abstract import _AbstractModel


class Model(_AbstractModel):
    """
    The section in the store that saves rows of the same kind
    """

    @classmethod
    def __get_primary_key(cls, primary_key_value: Any):
        """
        Returns the primary key value concatenated to the table name for uniqueness
        """
        table_name = cls.__name__.lower()
        return f"{table_name}_%&_{primary_key_value}"

    @classmethod
    def get_table_index_key(cls):
        """Returns the key in which the primary keys of the given table have been saved"""
        table_name = cls.__name__.lower()
        return f"{table_name}__index"

    @classmethod
    def insert(cls, data: Union[List[_AbstractModel], _AbstractModel], life_span_seconds: Optional[float] = None):
        """
        Inserts a given row or sets of rows into the table
        """
        life_span = life_span_seconds if life_span_seconds is not None else cls._store.life_span_in_seconds
        pipeline = cls._store.redis_store.pipeline()
        data_list = []

        if isinstance(data, list):
            data_list = data
        elif isinstance(data, _AbstractModel):
            data_list = [data]

        for record in data_list:
            cls.__insert_on_pipeline(_id=None, pipeline=pipeline, record=record, life_span=life_span)

        return pipeline.execute()

    @classmethod
    def update(cls, _id: Any, data: Dict[str, Any],
               life_span_seconds: Optional[float] = None):
        """
        Updates a given row or sets of rows in the table
        """
        life_span = life_span_seconds if life_span_seconds is not None else cls._store.life_span_in_seconds
        pipeline = cls._store.redis_store.pipeline()

        if isinstance(data, dict):
            cls.__insert_on_pipeline(_id=_id, pipeline=pipeline, record=data, life_span=life_span)

        return pipeline.execute()

    @classmethod
    def delete(cls, ids: Union[Any, List[Any]]):
        """
        deletes a given row or sets of rows in the table
        """
        pipeline = cls._store.redis_store.pipeline()
        primary_keys = []

        if isinstance(ids, list):
            primary_keys = ids
        elif ids is not None:
            primary_keys = [ids]

        names = [cls.__get_primary_key(primary_key_value=primary_key_value) for primary_key_value in primary_keys]
        pipeline.delete(*names)
        # remove the primary keys from the index
        table_index_key = cls.get_table_index_key()
        pipeline.srem(table_index_key, *names)
        return pipeline.execute()

    @classmethod
    def select(cls, columns: Optional[List[str]] = None, ids: Optional[List[Any]] = None,
               pipeline: Optional[Pipeline] = None):
        """
        Selects given rows or sets of rows in the table
        """
        pipeline = cls._store.redis_store.pipeline() if pipeline is None else pipeline
        columns = cls.__replace_nested_record_fields_with_foreign_key_fields(columns)

        if ids is None:
            # get all keys in the table immediately so don't use a pipeline
            table_index_key = cls.get_table_index_key()
            keys = cls._store.redis_store.sscan_iter(name=table_index_key)
        else:
            keys = (cls.__get_primary_key(primary_key_value=primary_key) for primary_key in ids)

        for key in keys:
            if columns is None:
                pipeline.hgetall(name=key)
            else:
                pipeline.hmget(name=key, keys=columns)
        response = pipeline.execute()

        if len(response) == 0:
            return None

        if isinstance(response, list) and columns is None:
            return [cls(**cls.deserialize_partially(record, pipeline=pipeline)) for record in response]
        elif isinstance(response, list) and columns is not None:
            raw_data = [{field: record[index] for index, field in enumerate(columns)}
                        for record in response]

            return [cls.deserialize_partially(record, pipeline=pipeline) for record in raw_data]
        return cls(**cls.deserialize_partially(response, pipeline=pipeline)) if isinstance(response, dict) else response

    @classmethod
    def deserialize_partially(cls, data: Optional[Dict[bytes, Any]], pipeline: Optional[Pipeline] = None) -> Dict[
        str, Any]:
        data = super().deserialize_partially(data)

        if pipeline is None and hasattr(cls, "_store"):
            pipeline = cls._store.redis_store.pipeline()

        cls.__replace_foreign_keys_with_nested_records_in_place(data, pipeline=pipeline)
        return data

    @staticmethod
    def __select_fields_from_dict(data: Dict[str, Any], fields: List[str]):
        """Returns a dictionary that has only a subset of the given fields"""
        return {k: data.get(k, None) for k in fields}

    @classmethod
    def __insert_on_pipeline(cls,
                             _id: Optional[Any],
                             pipeline: Pipeline,
                             record: Union[_AbstractModel, Dict[str, Any]],
                             life_span: Optional[Union[float, int]] = None
                             ) -> Any:
        """
        Creates insert commands for the given record on the given pipeline but does not execute
        thus the data is not yet persisted in redis
        Returns the key of the created item
        """
        foreign_key_list = cls.__insert_nested_records(pipeline=pipeline, record=record, life_span=life_span)
        key = _id if _id is not None else getattr(record, cls._primary_key_field, str(uuid.uuid4()))
        data = record.dict() if isinstance(record, _AbstractModel) else record
        cls.__replace_nested_records_with_foreign_keys_in_place(data=data, foreign_key_list=foreign_key_list)

        name = cls.__get_primary_key(primary_key_value=key)
        mapping = cls.serialize_partially(data)
        pipeline.hset(name=name, mapping=mapping)
        pipeline.expire(name=name, time=life_span)
        # save the primary key in an index
        table_index_key = cls.get_table_index_key()
        pipeline.sadd(table_index_key, name)
        pipeline.expire(table_index_key, time=life_span)

        return key

    @classmethod
    def __insert_nested_records(cls,
                                pipeline: Pipeline,
                                record: Union[_AbstractModel, Dict[str, Any]],
                                life_span: Optional[Union[float, int]] = None) -> List[Tuple[str, Any]]:
        """Inserts all nested records for the given data, with the given life span"""
        data = record.items() if isinstance(record, dict) else record
        foreign_key_list = []

        for k, v in data:
            if isinstance(v, Model):
                foreign_key = v.__class__.__insert_on_pipeline(
                    _id=None, pipeline=pipeline, record=v, life_span=life_span)
                foreign_key_list.append((k, foreign_key))

        return foreign_key_list

    @staticmethod
    def __replace_nested_records_with_foreign_keys_in_place(data: Dict[str, Any],
                                                            foreign_key_list: List[Tuple[str, Any]]):
        """Replaces nested records with foreign keys to save the raw data in redis"""
        for k, v in foreign_key_list:
            data[f"__{k}"] = v
            del data[k]

    @classmethod
    def __replace_foreign_keys_with_nested_records_in_place(cls, data: Optional[Dict[str, Any]],
                                                            pipeline: Optional[Pipeline] = None):
        """Replaces all foreign keys with nested records (loads stuff eagerly)"""
        field_types = typing.get_type_hints(cls)
        has_pipeline = isinstance(pipeline, Pipeline)

        if not has_pipeline:
            # it is impossible to eagerly load without a pipeline
            return

        for k, v in data.items():
            if k.startswith("__"):
                key = k.lstrip("__")
                foreign_model = field_types.get(key, None)

                if issubclass(foreign_model, Model):
                    values = foreign_model.select(ids=[v], pipeline=pipeline)
                    try:
                        data[key] = values[0]
                    except IndexError:
                        raise ValueError(f"The associated {foreign_model.__class__} of key {key} does not exist")

                del data[k]

    @classmethod
    def __replace_nested_record_fields_with_foreign_key_fields(cls, columns: Optional[List[str]]) -> Optional[
        List[str]]:
        """Replaces the nested record field names with foreign key field names"""
        if columns is None:
            return None

        field_types = typing.get_type_hints(cls)
        result = []
        for k in columns:
            foreign_model = field_types.get(k, None)
            if issubclass(foreign_model, Model):
                k = f"__{k}"

            result.append(k)

        return result
