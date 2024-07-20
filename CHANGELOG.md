# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added

### Changed

- Added support for deeply nested models beyond level-1 deep including:
  - dictionaries of lists of ... of nested models
  - lists of tuples of lists .... of nested models

### Fixed


## [0.6.0] - 2024-07-01

### Added

### Changed

- [BREAKING CHANGE] Removed the 'redis_store' argument from the `Store` constructor
- [BREAKING CHANGE] Made the 'redis_store' property of the `Store` readonly

### Fixed

- Fixed the rendering of the reference docs from the docstrings

## [0.5.0] - 2024-02-10

### Added

### Changed

- Upgraded to pydantic v2.

### Fixed

- Fixed orjson.JSONDecodeError when models have optional string fields
- Fixed ModuleNotFoundError: No module named 'mkdocstrings_handlers'

## [0.4.3] - 2022-12-29

### Added

- Added mkdocs documentation

### Changed

- Exposed `RedisConfig` via `pydantic_redis.config`, especially for documentation.

### Fixed

- Fixed docs building in CI

## [0.4.2] - 2022-12-29

### Added

### Changed

### Fixed

- Fixed unexpected data error when selecting some columns for some records

## [0.4.1] - 2022-12-29

### Added

### Changed

### Fixed

## [0.4.0] - 2022-12-17

### Added

- Added pagination

### Changed

- Changed redis index to use sorted sets instead of ordinary sets

### Fixed

## [0.3.0] - 2022-12-15

### Added

- Added asyncio support, to be got from the `pydantic_redis.asyncio` module

### Changed

- Moved the synchronous version to the `pydantic_redis.syncio` module, but kept its contents exposed in pydantic_redis
  for backward-compatibility

### Fixed

## [0.2.0] - 2022-12-15

### Added

### Changed

- Changed the `NESTED_MODEL_LIST_FIELD_PREFIX` to `___` and `NESTED_MODEL_TUPLE_FIELD_PREFIX` to `____`
- Changed all queries (selects) to use lua scripts
- Changed `Model.deserialize_partially` to receive data either as a dict or as a flattened list of key-values

### Fixed

## [0.1.8] - 2022-12-13

### Added

- Add support for model fields that are tuples of nested models 

### Changed

### Fixed

## [0.1.7] - 2022-12-12

### Added

### Changed

### Fixed

- Fixed support for model properties that are *Optional* lists of nested models 
- Fixed issue with field names being disfigured by `lstrip` when attempting to strip nested-mode-prefixes 

## [0.1.6] - 2022-11-01

### Added

- Support for model properties that are lists of nested models 

### Changed

### Fixed
