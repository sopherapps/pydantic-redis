"""Module containing the model classes"""
import typing
from typing import Optional, List, Any, Union, Dict, Tuple

from redis.client import Pipeline

from pydantic_redis.abstract import _AbstractModel

NESTED_MODEL_PREFIX = "__"
NESTED_MODEL_LIST_FIELD_PREFIX = "__%&l_"
NESTED_MODEL_TUPLE_FIELD_PREFIX = "__%&t_"


class Model(_AbstractModel):
    """
    The section in the store that saves rows of the same kind
    """

    _nested_model_tuple_fields = {}
    _nested_model_list_fields = {}
    _nested_model_fields = {}
    _field_types = {}

    @classmethod
    def __get_primary_key(cls, primary_key_value: Any):
        """
        Returns the primary key value concatenated to the table name for uniqueness
        """
        return f"{cls.__get_table_prefix()}{primary_key_value}"

    @classmethod
    def __get_table_prefix(cls):
        """
        Returns the prefix of the all the redis keys that are associated with this table
        """
        table_name = cls.__name__.lower()
        return f"{table_name}_%&_"

    @classmethod
    def __get_table_keys_regex(cls):
        """
        Returns the table name regex to get all keys that belong to this table
        """
        return f"{cls.__get_table_prefix()}*"

    @classmethod
    def get_table_index_key(cls):
        """Returns the key in which the primary keys of the given table have been saved"""
        table_name = cls.__name__.lower()
        return f"{table_name}__index"

    @classmethod
    def initialize(cls):
        """Initializes class-wide variables for performance's reasons e.g. it caches the nested model fields"""
        cls._field_types = typing.get_type_hints(cls)

        cls._nested_model_list_fields = {}
        cls._nested_model_tuple_fields = {}
        cls._nested_model_fields = {}

        for field, field_type in cls._field_types.items():
            try:
                # In case the annotation is Optional, an alias of Union[X, None], extract the X
                is_generic = hasattr(field_type, "__origin__")
                if (
                    is_generic
                    and typing_get_origin(field_type) == Union
                    and typing_get_args(field_type)[-1] == None.__class__
                ):
                    field_type = typing_get_args(field_type)[0]
                    is_generic = hasattr(field_type, "__origin__")

                if (
                    is_generic
                    and typing_get_origin(field_type) in (List, list)
                    and issubclass(typing_get_args(field_type)[0], Model)
                ):
                    cls._nested_model_list_fields[field] = typing_get_args(field_type)[
                        0
                    ]

                elif (
                    is_generic
                    and typing_get_origin(field_type) in (Tuple, tuple)
                    and any([issubclass(v, Model) for v in typing_get_args(field_type)])
                ):
                    cls._nested_model_tuple_fields[field] = typing_get_args(field_type)

                elif issubclass(field_type, Model):
                    cls._nested_model_fields[field] = field_type

            except (TypeError, AttributeError) as exp:
                pass

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
        if columns is None and ids is None:
            # all fields, all ids
            table_keys_regex = cls.__get_table_keys_regex()
            args = [table_keys_regex, *cls._nested_model_fields.keys()]
            response = cls._store.select_all_fields_for_all_ids_script(args=args)
        elif columns is None and isinstance(ids, list):
            # all fields, some ids
            table_prefix = cls.__get_table_prefix()
            keys = [f"{table_prefix}{key}" for key in ids]
            response = cls._store.select_all_fields_for_some_ids_script(
                keys=keys, args=cls._nested_model_fields.keys()
            )
        elif isinstance(columns, list) and ids is None:
            # some fields, all ids
            table_keys_regex = cls.__get_table_keys_regex()
            args = [table_keys_regex, *columns, *cls._nested_model_fields.keys()]
            response = cls._store.select_some_fields_for_all_ids_script(args=args)
        elif isinstance(columns, list) and isinstance(ids, list):
            # some fields, some ids
            table_prefix = cls.__get_table_prefix()
            keys = [f"{table_prefix}{key}" for key in ids]
            args = [*columns, *cls._nested_model_fields.keys()]
            response = cls._store.select_some_fields_for_all_ids_script(
                keys=keys, args=args
            )
        else:
            raise ValueError(
                f"columns {columns}, ids: {ids} should be either None or lists"
            )

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
            keys = [*parsed_data[0].keys()]

            for k in keys:
                if k in cls._nested_model_list_fields:
                    cls.__parse_nested_model_lists(field=k, data=parsed_data)

                elif k in cls._nested_model_tuple_fields:
                    cls.__parse_nested_model_tuples(field=k, data=parsed_data)

                elif k in cls._nested_model_fields:
                    cls.__parse_nested_models(field=k, data=parsed_data)
        return parsed_data

    @classmethod
    def __parse_nested_model_lists(
        cls,
        field: str,
        data: List[Dict[str, Any]],
    ):
        """
        Parses lists of dicts that includes fields of lists of nested dicts that represent models,
        turning those nested dicts into models
        NOTE: This parses the data in place for performance reasons.
        """
        field_type = cls._nested_model_list_fields.get(field)

        for record in data:
            nested_values = record[field]
            if nested_values is not None:
                record[field] = [field_type(**item) for item in nested_values]

    @classmethod
    def __parse_nested_model_tuples(
        cls,
        field: str,
        data: List[Dict[str, Any]],
    ):
        """
        Parses lists of dicts that includes fields of tuples of nested dicts that represent models,
        turning those nested dicts into models
        NOTE: This parses the data in place for performance reasons.
        """
        field_types = cls._nested_model_tuple_fields.get(field, ())

        for record in data:
            nested_values = record[field]
            if nested_values is not None:
                record[field] = tuple(
                    field_type(**value)
                    if issubclass(field_type, Model) and value is not None
                    else value
                    for field_type, value in zip(field_types, nested_values)
                )

    @classmethod
    def __parse_nested_models(cls, field: str, data: List[Dict[str, Any]]):
        """
        Parses dicts representing nested models into model instances.
        NOTE: This parses the data in place for performance reasons.
        """
        model_type = cls._nested_model_fields.get(field)
        for record in data:
            nested_value = record[field]
            if nested_value is not None:
                record[field] = model_type(**nested_value)

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
          - Replacing the keys of nested records with their NESTED_MODEL_PREFIX suffixed versions
            e.g. `__author` instead of author
          - Replacing the keys of lists of nested records with their NESTED_MODEL_LIST_FIELD_PREFIX suffixed versions
            e.g. `__%&l_author` instead of author
          - Replacing the keys of tuples of nested records with their NESTED_MODEL_TUPLE_FIELD_PREFIX suffixed versions
            e.g. `__%&l_author` instead of author
          - Replacing the values of nested records with their foreign keys
        """
        data = record.items() if isinstance(record, dict) else record
        new_data = {}

        for k, v in data:
            key, value = k, v

            if key in cls._nested_model_list_fields:
                value = cls.__serialize_nested_model_list_field(
                    value=value, pipeline=pipeline, life_span=life_span
                )
            elif key in cls._nested_model_tuple_fields:
                value = cls.__serialize_nested_model_tuple_field(
                    key=key, value=value, pipeline=pipeline, life_span=life_span
                )
            elif key in cls._nested_model_fields:
                value = cls.__serialize_nested_model_field(
                    value=value, pipeline=pipeline, life_span=life_span
                )

            new_data[key] = value
        return new_data

    @classmethod
    def __serialize_nested_model_tuple_field(
        cls,
        key: str,
        value: Tuple["Model"],
        pipeline: Pipeline,
        life_span: Optional[Union[float, int]],
    ) -> Tuple[str, List[Any]]:
        """Serializes a key-value pair for a field that has a tuple of nested models"""
        try:
            field_types = cls._nested_model_tuple_fields.get(key, ())
            value = [
                field_type.__insert_on_pipeline(
                    _id=None, pipeline=pipeline, record=item, life_span=life_span
                )
                if issubclass(field_type, Model)
                else item
                for field_type, item in zip(field_types, value)
            ]
        except TypeError:
            # In case the value is None, just ignore
            pass

        return value

    @classmethod
    def __serialize_nested_model_list_field(
        cls,
        value: List["Model"],
        pipeline: Pipeline,
        life_span: Optional[Union[float, int]],
    ) -> Tuple[str, List[Any]]:
        """Serializes a key-value pair for a field that has a list of nested models"""
        try:
            value = [
                item.__class__.__insert_on_pipeline(
                    _id=None, pipeline=pipeline, record=item, life_span=life_span
                )
                for item in value
            ]
        except TypeError:
            # In case the value is None, just ignore
            pass

        return value

    @classmethod
    def __serialize_nested_model_field(
        cls,
        value: "Model",
        pipeline: Pipeline,
        life_span: Optional[Union[float, int]],
    ) -> Tuple[str, List[Any]]:
        """Serializes a key-value pair for a field that has a nested model"""
        try:
            value = value.__class__.__insert_on_pipeline(
                _id=None, pipeline=pipeline, record=value, life_span=life_span
            )
        except TypeError:
            # In case the value is None, just ignore
            pass

        return value


def strip_leading(word: str, substring: str) -> str:
    """
    Strips the leading substring if it exists.
    This is contrary to rstrip which can looks at removes each character in the substring
    """
    if word.startswith(substring):
        return word[len(substring) :]
    return word


def typing_get_args(v: Any) -> Tuple[Any, ...]:
    """Gets the __args__ of the annotations of a given typing"""
    try:
        return typing.get_args(v)
    except AttributeError:
        return getattr(v, "__args__", ()) if v is not typing.Generic else typing.Generic


def typing_get_origin(v: Any) -> Optional[Any]:
    """Gets the __origin__ of the annotations of a given typing"""
    try:
        return typing.get_origin(v)
    except AttributeError:
        return getattr(v, "__origin__", None)
