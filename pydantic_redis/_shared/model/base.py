"""Exposes the Base `Model` common to both async and sync APIs

"""
import typing
from typing import Dict, Tuple, Any, Type, Union, List, Optional

from pydantic import BaseModel

from pydantic_redis._shared.utils import (
    typing_get_origin,
    typing_get_args,
    from_any_to_valid_redis_type,
    from_dict_to_key_value_list,
    from_bytes_to_str,
    from_str_or_bytes_to_any,
)


from ..store import AbstractStore


class AbstractModel(BaseModel):
    """A base class for all Models, sync and async alike.

    See the child classes for more.

    Attributes:
        _primary_key_field (str): the field that can uniquely identify each record
            for the current Model
        _field_types (Dict[str, Any]): a mapping of the fields and their types for
            the current model
        _store (AbstractStore): the Store in which the current model is registered.
        _nested_model_tuple_fields (Dict[str, Tuple[Any, ...]]): a mapping of
            fields and their types for fields that have tuples of nested models
        _nested_model_list_fields (Dict[str, Type["AbstractModel"]]): a mapping of
            fields and their associated nested models for fields that have
            lists of nested models
        _nested_model_fields (Dict[str, Type["AbstractModel"]]): a mapping of
            fields and their associated nested models for fields that have nested models
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
        """Gets the Store in which the current model is registered.

        Returns:
             the instance of the store for this model
        """
        return cls._store

    @classmethod
    def get_nested_model_tuple_fields(cls):
        """Gets the mapping for fields that have tuples of nested models.

        Returns:
             The mapping of field name and field type of a form similar to
              `Tuple[str, Book, date]`
        """
        return cls._nested_model_tuple_fields

    @classmethod
    def get_nested_model_list_fields(cls):
        """Gets the mapping for fields that have lists of nested models.

        Returns:
             The mapping of field name and model class nested in that field.
        """
        return cls._nested_model_list_fields

    @classmethod
    def get_nested_model_fields(cls):
        """Gets the mapping for fields that have nested models.

        Returns:
             The mapping of field name and model class nested in that field.
        """
        return cls._nested_model_fields

    @classmethod
    def get_primary_key_field(cls):
        """Gets the field that can uniquely identify each record of current Model

        Returns:
            the field that can be used to uniquely identify each record of current Model
        """
        return cls._primary_key_field

    @classmethod
    def get_field_types(cls) -> Dict[str, Any]:
        """Gets the mapping of field and field_type for current Model.

        Returns:
            the mapping of field and field_type for current Model
        """
        return cls._field_types

    @classmethod
    def initialize(cls):
        """Initializes class-wide variables for performance's reasons.

        This is a performance hack that initializes an variables that are common
        to all instances of the current Model e.g. the field types.
        """
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
        """Casts complex data types within a given dictionary to valid redis types.

        Args:
            data: the dictionary containing data with complex data types

        Returns:
            the transformed dictionary
        """
        return {key: from_any_to_valid_redis_type(value) for key, value in data.items()}

    @classmethod
    def deserialize_partially(
        cls, data: Union[List[Any], Dict[Any, Any]] = ()
    ) -> Dict[str, Any]:
        """Casts str or bytes in a dict or flattened key-value list to expected data types.

        Converts str or bytes to their expected data types

        Args:
            data: flattened list of key-values or dictionary of data to cast.
                Keeping it as potentially a dictionary ensures backward compatibility.

        Returns:
            the dictionary of properly parsed key-values.
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
                value = _cast_lists(value, nested_model_list_fields[key])

            elif key in nested_model_tuple_fields and value is not None:
                value = _cast_tuples(value, nested_model_tuple_fields[key])

            elif key in nested_model_fields and value is not None:
                value = _cast_to_model(value=value, model=nested_model_fields[key])

            parsed_dict[key] = value

        return parsed_dict


def _cast_lists(value: List[Any], _type: Type[AbstractModel]) -> List[AbstractModel]:
    """Casts a list of flattened key-value lists into a list of _type.

    Args:
        _type: the type to cast the records to.
        value: the value to convert

    Returns:
        a list of records of the given _type
    """
    return [_type(**_type.deserialize_partially(item)) for item in value]


def _cast_tuples(value: List[Any], _type: Tuple[Any, ...]) -> Tuple[Any, ...]:
    """Casts a list of flattened key-value lists into a list of tuple of _type,.

    Args:
        _type: the tuple signature type to cast the records to
            e.g. Tuple[str, Book, int]
        value: the value to convert

    Returns:
        a list of records of tuple signature specified by `_type`
    """
    items = []
    for field_type, value in zip(_type, value):
        if issubclass(field_type, AbstractModel) and value is not None:
            value = field_type(**field_type.deserialize_partially(value))
        items.append(value)

    return tuple(items)


def _cast_to_model(value: List[Any], model: Type[AbstractModel]) -> AbstractModel:
    """Converts a list of flattened key-value lists into a list of models,.

    Args:
        model: the model class to cast to
        value: the value to cast

    Returns:
        a list of model instances of type `model`
    """
    return model(**model.deserialize_partially(value))
