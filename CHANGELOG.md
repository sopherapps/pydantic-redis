# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

## [0.2.0] - 2022-12-15

### Added

### Changed

- Changed the `NESTED_MODEL_LIST_FIELD_PREFIX` to "___" and `NESTED_MODEL_TUPLE_FIELD_PREFIX` to "____"
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
