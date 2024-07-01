"""Exposes base Store class common to both sync and async

"""

from typing import Optional, Union, Type, Dict, Any

from pydantic.fields import ModelPrivateAttr
from redis import Redis
from redis.asyncio import Redis as AioRedis
from pydantic import ConfigDict, BaseModel
from redis.commands.core import Script, AsyncScript

from ..config import RedisConfig
from .lua_scripts import (
    SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT,
    SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT,
    SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT,
    SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT,
    PAGINATED_SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT,
    PAGINATED_SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import AbstractModel


class AbstractStore(BaseModel):
    """An abstract class of a store.

    Check the child classes for more definition.
    """

    name: str
    redis_config: RedisConfig
    life_span_in_seconds: Optional[int] = None
    select_all_fields_for_all_ids_script: Optional[Union[AsyncScript, Script]] = None
    paginated_select_all_fields_for_all_ids_script: Optional[
        Union[AsyncScript, Script]
    ] = None
    select_all_fields_for_some_ids_script: Optional[Union[AsyncScript, Script]] = None
    select_some_fields_for_all_ids_script: Optional[Union[AsyncScript, Script]] = None
    paginated_select_some_fields_for_all_ids_script: Optional[
        Union[AsyncScript, Script]
    ] = None
    select_some_fields_for_some_ids_script: Optional[Union[AsyncScript, Script]] = None
    models: Dict[str, Type["AbstractModel"]] = {}
    model_config = ConfigDict(arbitrary_types_allowed=True, from_attributes=True)

    # protected properties
    _redis_store: Optional[Union[Redis, AioRedis]] = None

    def __init__(
        self,
        name: str,
        redis_config: RedisConfig,
        life_span_in_seconds: Optional[int] = None,
        **data: Any,
    ):
        super().__init__(
            name=name,
            redis_config=redis_config,
            life_span_in_seconds=life_span_in_seconds,
            **data,
        )

        self._redis_store = self._connect_to_redis()
        self._register_lua_scripts()

    @property
    def redis_store(self) -> Optional[Union[Redis, AioRedis]]:
        """the redis store for the given store"""
        return self._redis_store

    def _connect_to_redis(self) -> Union[Redis, AioRedis]:
        """Connects the store to redis.

        Connects to the redis database basing on the `redis_config`
        attribute of this instance.

        Returns:
            A connection object to a redis database
        """
        raise NotImplementedError("implement _connect_to_redis first")

    def _register_lua_scripts(self):
        """Registers the lua scripts for this redis instance.

        In order to save on memory and bandwidth, the redis lua scripts
        need to be called using EVALSHA instead of EVAL. The latter transfers
        the scripts to the redis server on every invocation while the former
        saves the script in redis itself and invokes it using a hashed (SHA) value.
        """
        self.select_all_fields_for_all_ids_script = self.redis_store.register_script(
            SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT
        )
        self.paginated_select_all_fields_for_all_ids_script = (
            self.redis_store.register_script(
                PAGINATED_SELECT_ALL_FIELDS_FOR_ALL_IDS_SCRIPT
            )
        )
        self.select_all_fields_for_some_ids_script = self.redis_store.register_script(
            SELECT_ALL_FIELDS_FOR_SOME_IDS_SCRIPT
        )
        self.select_some_fields_for_all_ids_script = self.redis_store.register_script(
            SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT
        )
        self.paginated_select_some_fields_for_all_ids_script = (
            self.redis_store.register_script(
                PAGINATED_SELECT_SOME_FIELDS_FOR_ALL_IDS_SCRIPT
            )
        )
        self.select_some_fields_for_some_ids_script = self.redis_store.register_script(
            SELECT_SOME_FIELDS_FOR_SOME_IDS_SCRIPT
        )

    def register_model(self, model_class: Type["AbstractModel"]):
        """Registers the model to this store.

        Each store manages a number of models. In order to associate
        a model to a redis database, a Store must register it.

        Args:
            model_class: the class which represents a given schema of
                a certain type of records to be saved in redis.
        """
        if not isinstance(model_class.get_primary_key_field(), str):
            raise AttributeError(
                f"{model_class.__name__} should have a _primary_key_field"
            )

        model_class._store = self
        model_class.initialize()
        self.models[model_class.__name__.lower()] = model_class

    def model(self, name: str) -> Type["AbstractModel"]:
        """Gets a model by name. This is case insensitive.

        Args:
            name: the case-insensitive name of the model class

        Returns:
            the class corresponding to the given name
        """
        return self.models[name.lower()]
