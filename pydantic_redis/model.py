"""Module containing the model classes"""
import typing
from typing import Optional, List, Any, Union, Dict

from redis.client import Pipeline

from pydantic_redis.abstract import _AbstractModel

NESTED_MODEL_PREFIX = "__"
IN_LIST_NESTED_MODEL_PREFIX = "__%&l_"


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
    def insert(
        cls,
        data: Union[List[_AbstractModel], _AbstractModel],
        life_span_seconds: Optional[float] = None,
    ):
        """
        Inserts a given row or sets of rows into the table
        """
        life_span = (
            life_span_seconds
            if life_span_seconds is not None
            else cls._store.life_span_in_seconds
        )
        with cls._store.redis_store.pipeline(transaction=True) as pipeline:
            data_list = []

            if isinstance(data, list):
                data_list = data
            elif isinstance(data, _AbstractModel):
                data_list = [data]

            for record in data_list:
                cls.__insert_on_pipeline(
                    _id=None, pipeline=pipeline, record=record, life_span=life_span
                )

            return pipeline.execute()

    @classmethod
    def update(
        cls, _id: Any, data: Dict[str, Any], life_span_seconds: Optional[float] = None
    ):
        """
        Updates a given row or sets of rows in the table
        """
        life_span = (
            life_span_seconds
            if life_span_seconds is not None
            else cls._store.life_span_in_seconds
        )
        with cls._store.redis_store.pipeline(transaction=True) as pipeline:
            if isinstance(data, dict):
                cls.__insert_on_pipeline(
                    _id=_id, pipeline=pipeline, record=data, life_span=life_span
                )

            return pipeline.execute()

    @classmethod
    def delete(cls, ids: Union[Any, List[Any]]):
        """
        deletes a given row or sets of rows in the table
        """
        with cls._store.redis_store.pipeline() as pipeline:
            primary_keys = []

            if isinstance(ids, list):
                primary_keys = ids
            elif ids is not None:
                primary_keys = [ids]

            names = [
                cls.__get_primary_key(primary_key_value=primary_key_value)
                for primary_key_value in primary_keys
            ]
            pipeline.delete(*names)
            # remove the primary keys from the index
            table_index_key = cls.get_table_index_key()
            pipeline.srem(table_index_key, *names)
            return pipeline.execute()

    @classmethod
    def select(
        cls,
        columns: Optional[List[str]] = None,
        ids: Optional[List[Any]] = None,
        pipeline: Optional[Pipeline] = None,
    ):
        """
        Selects given rows or sets of rows in the table
        """
        columns = cls.__get_select_fields(columns)
        if ids is None:
            # get all keys in the table immediately so don't use a pipeline
            table_index_key = cls.get_table_index_key()
            keys = cls._store.redis_store.sscan_iter(name=table_index_key)
        else:
            keys = (
                cls.__get_primary_key(primary_key_value=primary_key)
                for primary_key in ids
            )

        with cls._store.redis_store.pipeline() as pipeline:
            if columns is None:
                for key in keys:
                    pipeline.hgetall(name=key)
            else:
                for key in keys:
                    pipeline.hmget(name=key, keys=columns)

            response = pipeline.execute()

        if len(response) == 0:
            return None
        elif isinstance(response, list) and columns is None:
            return cls.__parse_model_list(response)
        elif isinstance(response, list) and columns is not None:
            return cls.__parse_hmget_response(response, columns=columns)
        elif isinstance(response, dict):
            return cls.__parse_model_list([response])[0]

        return response

    @classmethod
    def __parse_dict_list(cls, data: List[Dict[bytes, Any]]) -> List[Dict[str, Any]]:
        """
        Converts a list of dictionaries straight from Redis into a list of normalized dictionaries
        with foreign keys replaced by model instances
        """
        parsed_data = [
            cls.deserialize_partially(record) for record in data if record != {}
        ]
        if len(parsed_data) > 0:
            field_types = typing.get_type_hints(cls)
            keys = [*parsed_data[0].keys()]

            for k in keys:
                if k.startswith(IN_LIST_NESTED_MODEL_PREFIX):
                    cls.__eager_load_nested_model_lists(
                        prefixed_field=k, data=parsed_data, field_types=field_types
                    )

                elif k.startswith(NESTED_MODEL_PREFIX):
                    cls.__eager_load_nested_models(
                        prefixed_field=k, data=parsed_data, field_types=field_types
                    )
        return parsed_data

    @classmethod
    def __eager_load_nested_model_lists(
        cls,
        prefixed_field: str,
        data: List[Dict[str, Any]],
        field_types: Dict[str, Any],
    ):
        """
        Eagerly loads any properties that have `List[Model]` as their type annotations
        for each item in the data such that primary_key lists are replaced by Model lists
        Note: This mutates the data in-place as a way of optimization
        For example:
        [{"___books": ["id1", "id2"]}] becomes [{"books": [Book{"id": "id1", ...}, Book{"id": "id2", ...}]}]
        """
        field = prefixed_field.lstrip(IN_LIST_NESTED_MODEL_PREFIX)
        model_type = field_types.get(field).__args__[0]

        for record in data:
            ids = record.pop(prefixed_field, None)
            record[field] = model_type.select(ids=ids)

    @classmethod
    def __eager_load_nested_models(
        cls,
        prefixed_field: str,
        data: List[Dict[str, Any]],
        field_types: Dict[str, Any],
    ):
        """
        Eagerly loads any properties that have `Model` as their type annotations
        for each item in the data such that primary_key lists are replaced by Models
        Note: This mutates the data in-place as a way of optimization
        For example:
        [{"__book": "id1"}] becomes [{"book": Book{"id": "id1", ...}}]
        """
        field = prefixed_field.lstrip(NESTED_MODEL_PREFIX)
        model_type = field_types.get(field)

        ids: List[str] = [record.pop(prefixed_field, None) for record in data]
        # a bulk network request might be faster than eagerly loading for each record for many records
        nested_models = model_type.select(ids=ids)

        for record, model in zip(data, nested_models):
            record[field] = model

    @classmethod
    def __parse_hmget_response(
        cls, data: List[List[Any]], columns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Converts the response from redis.hmget (a list of lists ordered identically to ``columns``) into a list of
        normalized dictionaries where foreign keys have been replaced by nested models
        """
        dict_list = [
            {field: record[index] for index, field in enumerate(columns)}
            for record in data
        ]
        return cls.__parse_dict_list(dict_list)

    @classmethod
    def __parse_model_list(cls, data: List[Dict[bytes, Any]]) -> List["Model"]:
        """
        Converts a list of dictionaries straight from Redis into a list of Model instances
        """
        parsed_dict_list = cls.__parse_dict_list(data)
        return [cls(**record) for record in parsed_dict_list]

    @classmethod
    def __insert_on_pipeline(
        cls,
        pipeline: Pipeline,
        _id: Optional[Any],
        record: Union[_AbstractModel, Dict[str, Any]],
        life_span: Optional[Union[float, int]] = None,
    ) -> Any:
        """
        Creates insert commands for the given record on the given pipeline but does not execute
        thus the data is not yet persisted in redis
        Returns the key of the created item
        """
        key = _id if _id is not None else getattr(record, cls._primary_key_field)
        data = cls.__get_serializable_dict(
            pipeline=pipeline, record=record, life_span=life_span
        )
        name = cls.__get_primary_key(primary_key_value=key)
        mapping = cls.serialize_partially(data)
        pipeline.hset(name=name, mapping=mapping)

        if life_span is not None:
            pipeline.expire(name=name, time=life_span)
        # save the primary key in an index
        table_index_key = cls.get_table_index_key()
        pipeline.sadd(table_index_key, name)
        if life_span is not None:
            pipeline.expire(table_index_key, time=life_span)

        return key

    @classmethod
    def __get_serializable_dict(
        cls,
        pipeline: Pipeline,
        record: Union[_AbstractModel, Dict[str, Any]],
        life_span: Optional[Union[float, int]] = None,
    ) -> Dict[str, Any]:
        """
        Returns a dictionary that can be serialized.
        A few cleanups it does include:
          - Upserting any nested records in `record`
          - Replacing the keys of nested records with their NESTED_MODEL_PREFIX suffixed versions e.g. `__author` instead of author
          - Replacing the values of nested records with their foreign keys
        """
        data = record.items() if isinstance(record, dict) else record
        new_data = {}

        for k, v in data:
            key, value = k, v

            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], Model):
                key = f"{IN_LIST_NESTED_MODEL_PREFIX}{key}"
                value = [
                    item.__class__.__insert_on_pipeline(
                        _id=None, pipeline=pipeline, record=item, life_span=life_span
                    )
                    for item in value
                ]

            elif isinstance(v, Model):
                key = f"{NESTED_MODEL_PREFIX}{key}"
                value = v.__class__.__insert_on_pipeline(
                    _id=None, pipeline=pipeline, record=v, life_span=life_span
                )
            new_data[key] = value
        return new_data

    @classmethod
    def __get_select_fields(cls, columns: Optional[List[str]]) -> Optional[List[str]]:
        """
        Gets the fields to be used for selecting HMAP fields in Redis
        It replaces any fields in `columns` that correspond to nested records with their
        `__` suffixed versions
        """
        if columns is None:
            return None

        field_types = typing.get_type_hints(cls)

        fields = []
        for col in columns:
            field_type = field_types.get(col, None)

            if isinstance(field_type, type(Model)):
                fields.append(f"{NESTED_MODEL_PREFIX}{col}")
            elif issubclass(field_type, List) and isinstance(
                field_type.__args__[0], type(Model)
            ):
                fields.append(f"{IN_LIST_NESTED_MODEL_PREFIX}{col}")
            else:
                fields.append(col)

        return fields
