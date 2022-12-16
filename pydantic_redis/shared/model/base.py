"""Module containing the base model"""
import typing
from typing import Dict, Tuple, Any, Type, Union, List, Optional

from pydantic import BaseModel

from pydantic_redis.shared.utils import (
    typing_get_origin,
    typing_get_args,
    from_any_to_str_or_bytes,
    from_dict_to_key_value_list,
    from_bytes_to_str,
    from_str_or_bytes_to_any,
)


from ..store import AbstractStore


class AbstractModel(BaseModel):
    """
    An abstract class to help with typings for Model class
    """

    _primary_key_field: str
    _field_types: Dict[str, Any] = {}
    _store: AbstractStore
    _nested_model_tuple_fields: Dict[str, Tuple[Any, ...]] = {}
    _nested_model_list_fields: Dict[str, Type["AbstractModel"]] = {}
    _nested_model_fields: Dict[str, Type["AbstractModel"]] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def get_store(cls) -> AbstractStore:
        """Returns the instance of the store for this model"""
        return cls._store

    @classmethod
    def get_nested_model_tuple_fields(cls):
        """Returns the fields that have tuples of nested models"""
        return cls._nested_model_tuple_fields

    @classmethod
    def get_nested_model_list_fields(cls):
        """Returns the fields that have list of nested models"""
        return cls._nested_model_list_fields

    @classmethod
    def get_nested_model_fields(cls):
        """Returns the fields that have nested models"""
        return cls._nested_model_fields

    @classmethod
    def get_primary_key_field(cls):
        """Gets the protected _primary_key_field"""
        return cls._primary_key_field

    @classmethod
    def get_field_types(cls) -> Dict[str, Any]:
        """Returns the fields types of this model"""
        return cls._field_types

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
                    and issubclass(typing_get_args(field_type)[0], AbstractModel)
                ):
                    cls._nested_model_list_fields[field] = typing_get_args(field_type)[
                        0
                    ]

                elif (
                    is_generic
                    and typing_get_origin(field_type) in (Tuple, tuple)
                    and any(
                        [
                            issubclass(v, AbstractModel)
                            for v in typing_get_args(field_type)
                        ]
                    )
                ):
                    cls._nested_model_tuple_fields[field] = typing_get_args(field_type)

                elif issubclass(field_type, AbstractModel):
                    cls._nested_model_fields[field] = field_type

            except (TypeError, AttributeError):
                pass

    @classmethod
    def serialize_partially(cls, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts non primitive data types into str"""
        return {key: from_any_to_str_or_bytes(value) for key, value in data.items()}

    @classmethod
    def deserialize_partially(
        cls, data: Union[List[Any], Dict[Any, Any]] = ()
    ) -> Dict[str, Any]:
        """
        Converts str or bytes to their expected data types, given a list of properties got from the
        list of lists got after calling EVAL on redis.

        EVAL returns a List of Lists of key, values where the value for a given key is in the position
        just after the key e.g. [["foo", "bar", "head", 9]] => [{"foo": "bar", "head": 9}]

        Note: For backward compatibility, data can also be a dict.
        """
        if isinstance(data, dict):
            # for backward compatibility
            data = from_dict_to_key_value_list(data)

        parsed_dict = {}

        nested_model_list_fields = cls.get_nested_model_list_fields()
        nested_model_tuple_fields = cls.get_nested_model_tuple_fields()
        nested_model_fields = cls.get_nested_model_fields()

        for i in range(0, len(data), 2):
            key = from_bytes_to_str(data[i])
            field_type = cls._field_types.get(key)
            value = from_str_or_bytes_to_any(value=data[i + 1], field_type=field_type)

            if key in nested_model_list_fields and value is not None:
                value = deserialize_nested_model_list(
                    field_type=nested_model_list_fields[key], value=value
                )

            elif key in nested_model_tuple_fields and value is not None:
                value = deserialize_nested_model_tuple(
                    field_types=nested_model_tuple_fields[key], value=value
                )

            elif key in nested_model_fields and value is not None:
                value = deserialize_nested_model(
                    field_type=nested_model_fields[key], value=value
                )

            parsed_dict[key] = value

        return parsed_dict


def deserialize_nested_model_list(
    field_type: Type[AbstractModel], value: List[Any]
) -> List[AbstractModel]:
    """Deserializes a list of key values for the given field returning a list of nested models"""
    return [field_type(**field_type.deserialize_partially(item)) for item in value]


def deserialize_nested_model_tuple(
    field_types: Tuple[Any, ...], value: List[Any]
) -> Tuple[Any, ...]:
    """Deserializes a list of key values for the given field returning a tuple of nested models among others"""
    items = []
    for field_type, value in zip(field_types, value):
        if issubclass(field_type, AbstractModel) and value is not None:
            value = field_type(**field_type.deserialize_partially(value))
        items.append(value)

    return tuple(items)


def deserialize_nested_model(
    field_type: Type[AbstractModel], value: List[Any]
) -> AbstractModel:
    """Deserializes a list of key values for the given field returning the nested model"""
    return field_type(**field_type.deserialize_partially(value))
