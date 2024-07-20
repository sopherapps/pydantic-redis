"""Exposes the Base `Model` common to both async and sync APIs

Attributes:
    NESTED_MODEL_PREFIX (str): the prefix for fields with single nested models
    NESTED_MODEL_LIST_FIELD_PREFIX (str): the prefix for fields with lists of nested models
    NESTED_MODEL_TUPLE_FIELD_PREFIX (str): the prefix for fields with tuples of nested models
    NESTED_MODEL_DICT_FIELD_PREFIX (str): the prefix for fields with dicts of nested models
"""

import enum
import typing
from typing import Dict, Tuple, Any, Type, Union, List, Optional

from pydantic import ConfigDict, BaseModel

from pydantic_redis._shared.utils import (
    typing_get_origin,
    typing_get_args,
    from_any_to_valid_redis_type,
    from_dict_to_key_value_list,
    from_bytes_to_str,
    from_str_or_bytes_to_any,
    groups_of_n,
)


from ..store import AbstractStore

NESTED_MODEL_PREFIX = "__"
NESTED_MODEL_LIST_FIELD_PREFIX = "___"
NESTED_MODEL_TUPLE_FIELD_PREFIX = "____"
NESTED_MODEL_DICT_FIELD_PREFIX = "_____"


class NestingType(int, enum.Enum):
    """The type of nesting that can happen especially for nested models"""

    ON_ROOT = 0
    IN_LIST = 1
    IN_TUPLE = 2
    IN_DICT = 3
    IN_UNION = 4


# the type describing a tree for traversing types that form an aggregate type with a possibility
#   of nested types and models
#   Note: AbstractModel types are treated special. The first item in the tuple declares if
#         the type on that tree node has a nested model, and of which type of nesting
#
#   Note: (None, (Any)) corresponds to a type that is not a nested model
#         (IN_LIST, (AbstractModel)) corresponds to List[AbstractModel]
#         (None, (str)) corresponds to str
#         (IN_TUPLE, (str, AbstractModel)) corresponds to Tuple[str, AbstractModel]
#         (IN_LIST, (IN_TUPLE, (str, AbstractModel))) corresponds to List[Tuple[str, AbstractModel]]
AggTypeTree = Tuple[Optional[NestingType], Tuple[Union[Type["AbstractModel"], Any], ...]]  # type: ignore


class AbstractModel(BaseModel):
    """A base class for all Models, sync and async alike.

    See the child classes for more.

    Attributes:
        _primary_key_field (str): the field that can uniquely identify each record
            for the current Model
        _field_types (Dict[str, Any]): a mapping of the fields and their types for
            the current model
        _store (AbstractStore): the Store in which the current model is registered.
        _field_type_trees (Dict[str, Optional[AggTypeTree]]): a mapping of
            fields and their associated trees of types forming their aggregate types
        _strict (bool): Whether the model should be very strict on its types. By default, a
            moderate level of strictness is imposed
    """

    _primary_key_field: str
    _field_types: Dict[str, Any] = {}
    _store: AbstractStore
    _field_type_trees: Dict[str, Optional[AggTypeTree]] = {}
    _field_typed_keys: Dict[str, str] = {}
    _strict: bool = False
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def get_store(cls) -> AbstractStore:
        """Gets the Store in which the current model is registered.

        Returns:
             the instance of the store for this model
        """
        return cls._store

    @classmethod
    def get_field_type_trees(cls):
        """Gets the mapping for fields and the trees of the types that form their aggregate types.

        Returns:
             The mapping of field name and type trees of their aggregate types
        """
        return cls._field_type_trees

    @classmethod
    def get_primary_key_field(cls):
        """Gets the field that can uniquely identify each record of current Model

        Returns:
            the field that can be used to uniquely identify each record of current Model
        """
        try:
            return cls._primary_key_field.get_default()
        except AttributeError:
            return cls._primary_key_field

    @classmethod
    def get_field_types(cls) -> Dict[str, Any]:
        """Gets the mapping of field and field_type for current Model.

        Returns:
            the mapping of field and field_type for current Model
        """
        return cls._field_types

    @classmethod
    def get_field_typed_keys(cls) -> Dict[str, Any]:
        """Gets the mapping of field and their type-aware key names for current Model.

        Returns:
            the mapping of field and the type-aware key names for current Model
        """
        return cls._field_typed_keys

    @classmethod
    def initialize(cls):
        """Initializes class-wide variables for performance's reasons.

        This is a performance hack that initializes variables that are common
        to all instances of the current Model e.g. the field types.
        """
        cls._field_types = typing.get_type_hints(cls)

        cls._field_type_trees = {
            field: _generate_field_type_tree(field_type, strict=cls._strict)
            for field, field_type in cls._field_types.items()
            if not field.startswith("_")
        }

        cls._field_typed_keys = {
            field: _get_typed_field_key(field, type_tree=type_tree)
            for field, type_tree in cls._field_type_trees.items()
        }

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
        cls, data: Union[List[Any], Dict[Any, Any]] = (), index: Dict[Any, Any] = None
    ) -> Dict[str, Any]:
        """Casts str or bytes in a dict to expected data types.

        Converts str or bytes to their expected data types

        Args:
            data: flattened list of key-values or dictionary of data to cast.
                Keeping it as potentially a dictionary ensures backward compatibility.
            index: dictionary of the index of nested models potentially present

        Returns:
            the dictionary of properly parsed key-values.
        """
        if index is None:
            index = {}

        if isinstance(data, dict):
            # for backward compatibility
            data = from_dict_to_key_value_list(data)

        parsed_dict = {}

        field_type_trees = cls.get_field_type_trees()

        for k, v in groups_of_n(data, 2):
            # remove the dunders for nested model fields
            key = from_bytes_to_str(k).lstrip("_")
            field_type = cls._field_types.get(key)
            value = from_str_or_bytes_to_any(value=v, field_type=field_type)
            type_tree = field_type_trees.get(key)

            parsed_dict[key] = _cast_by_type_tree(
                value=value, type_tree=type_tree, index=index
            )

        return parsed_dict


def _generate_field_type_tree(field_type: Any, strict: bool = False) -> AggTypeTree:
    """Gets the tree of types for the given aggregate type of the field

    Args:
        field_type: the type of the field
        strict: whether to raise an error if a given generic type is not supported; default=False

    Returns:
        the type of nested model or None if not a nested model instance,
            and a tuple of the types of its constituent types
    """
    try:
        nesting_type = None
        generic_cls = typing_get_origin(field_type)

        if generic_cls is None:
            if issubclass(field_type, AbstractModel):
                return NestingType.ON_ROOT, (field_type,)
            return None, (field_type,)

        type_args = typing_get_args(field_type)

        if generic_cls is Union:
            nesting_type = NestingType.IN_UNION

        elif generic_cls in (List, list):
            nesting_type = NestingType.IN_LIST

        elif generic_cls in (Tuple, tuple):
            nesting_type = NestingType.IN_TUPLE

        elif generic_cls in (Dict, dict):
            nesting_type = NestingType.IN_DICT

        elif strict:
            raise NotImplementedError(
                f"Generic class type: {generic_cls} not supported for nested models"
            )

        return nesting_type, tuple(
            [_generate_field_type_tree(v, strict) for v in type_args]
        )

    except AttributeError:
        return None, (field_type,)


def _cast_by_type_tree(
    value: Any, type_tree: Optional[AggTypeTree], index: Dict[Any, Any] = None
) -> Any:
    """Casts a given value into a value basing on the tree of its aggregate type

    Args:
        value: the value to be cast basing on the type tree
        type_tree: the tree representing the nested hierarchy of types for the aggregate
            type that the value is to be cast into
        index: dictionary of the index of nested models potentially present

    Returns:
        the parsed value
    """
    if value is None or type_tree is None:
        # return the value as is because it cannot be cast
        return value

    nesting_type, type_args = type_tree

    if nesting_type is NestingType.ON_ROOT:
        _type = type_args[0]
        nested_model_data = value
        if isinstance(value, str):
            # load the nested model if it is not yet loaded
            nested_model_data = index.get(value, value)
        return _type(**_type.deserialize_partially(nested_model_data))

    if nesting_type is NestingType.IN_LIST:
        _type = type_args[0]
        return [_cast_by_type_tree(item, _type, index) for item in value]

    if nesting_type is NestingType.IN_TUPLE:
        return tuple(
            [
                _cast_by_type_tree(item, _type, index)
                for _type, item in zip(type_args, value)
            ]
        )

    if nesting_type is NestingType.IN_DICT:
        _, value_type = type_args
        return {k: _cast_by_type_tree(v, value_type, index) for k, v in value.items()}

    if nesting_type is NestingType.IN_UNION:
        # the value can be any of the types in type_args
        for _type in type_args:
            try:
                parsed_value = _cast_by_type_tree(value, _type, index)
                # return the first successfully parsed value
                # that is not equal to the original value
                if parsed_value != value:
                    return parsed_value
            except Exception:
                pass

    # return the value without any parsing
    return value


def _get_typed_field_key(
    field: str, type_tree: AggTypeTree, initial_prefix: str = ""
) -> str:
    """Returns the key for the given field with extra information of its type

    Args:
        field: the original key
        type_tree: the tree of types that form the aggregate tree for the given key
        initial_prefix: the initial_prefix to add to the field

    Returns:
        the key with extra type information in its string
    """
    if type_tree is None:
        return field

    nesting_type, type_args = type_tree

    if nesting_type is NestingType.ON_ROOT:
        # we have found a NestedModel, so we stop recursion
        if initial_prefix:
            return f"{initial_prefix}{field}"
        return f"{NESTED_MODEL_PREFIX}{field}"

    if nesting_type is NestingType.IN_LIST:
        _type = type_args[0]
        return _get_typed_field_key(
            field, _type, initial_prefix=NESTED_MODEL_LIST_FIELD_PREFIX
        )

    if nesting_type is NestingType.IN_TUPLE:
        for _type in type_args:
            key = _get_typed_field_key(
                field, _type, initial_prefix=NESTED_MODEL_TUPLE_FIELD_PREFIX
            )
            if key != field:
                return key

    if nesting_type is NestingType.IN_DICT:
        _, value_type = type_args
        return _get_typed_field_key(
            field, value_type, initial_prefix=NESTED_MODEL_DICT_FIELD_PREFIX
        )

    if nesting_type is NestingType.IN_UNION:
        # the value can be any of the types in type_args
        for _type in type_args:
            try:
                key = _get_typed_field_key(field, type_tree=_type)
                # return the first successful value
                # that is not equal to the original value
                # FIXME: Note that this is not comprehensive enough because
                #   it is possible to have Union[AbstractModel, List[AbstractModel]]
                #   but that would be a complicated type to parse/serialize
                #   Moral of story: Don't use it :-)
                if key != field:
                    return key
            except Exception:
                pass

    return field
