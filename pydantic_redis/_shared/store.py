"""Module containing common base store functionality"""
from typing import Optional, Union, Type, Dict, Any

from redis import Redis
from redis.asyncio import Redis as AioRedis
from pydantic import BaseModel
from redis.commands.core import Script, AsyncScript

from .config import RedisConfig
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
    """
    An abstract class of a store
    """

    name: str
    redis_config: RedisConfig
    redis_store: Optional[Union[Redis, AioRedis]] = None
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

    class Config:
        arbitrary_types_allowed = True
        orm_mode = True

    def __init__(
        self,
        name: str,
        redis_config: RedisConfig,
        redis_store: Optional[Union[Redis, AioRedis]] = None,
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

        self.redis_store = self._connect_to_redis()
        self._register_lua_scripts()

    def _connect_to_redis(self) -> Union[Redis, AioRedis]:
        """Connects the store to redis, returning a proper connection"""
        raise NotImplementedError("implement _connect_to_redis first")

    def _register_lua_scripts(self):
        """Registers the lua scripts for this redis instance"""
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
        """Registers the model to this store"""
        if not isinstance(model_class.get_primary_key_field(), str):
            raise NotImplementedError(
                f"{model_class.__name__} should have a _primary_key_field"
            )

        model_class._store = self
        model_class.initialize()
        self.models[model_class.__name__.lower()] = model_class

    def model(self, name: str) -> Type["AbstractModel"]:
        """Gets a model by name: case insensitive"""
        return self.models[name.lower()]
