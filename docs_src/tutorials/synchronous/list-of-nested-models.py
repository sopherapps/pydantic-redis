import pprint
from enum import Enum
from typing import List

from pydantic_redis import Model, Store, RedisConfig


class FileType(Enum):
    TEXT = "text"
    IMAGE = "image"
    EXEC = "executable"


class File(Model):
    _primary_key_field: str = "path"
    path: str
    type: FileType


class Folder(Model):
    _primary_key_field: str = "path"
    path: str
    files: List[File] = []
    folders: List["Folder"] = []


if __name__ == "__main__":
    pp = pprint.PrettyPrinter(indent=4)
    store = Store(
        name="some_name",
        redis_config=RedisConfig(db=5, host="localhost", port=6379),
        life_span_in_seconds=3600,
    )

    store.register_model(File)
    store.register_model(Folder)

    child_folder = Folder(
        path="path/to/child-folder",
        files=[
            File(path="path/to/foo.txt", type=FileType.TEXT),
            File(path="path/to/foo.jpg", type=FileType.IMAGE),
        ],
    )

    Folder.insert(
        Folder(
            path="path/to/parent-folder",
            files=[
                File(path="path/to/bar.txt", type=FileType.TEXT),
                File(path="path/to/bar.jpg", type=FileType.IMAGE),
            ],
            folders=[child_folder],
        )
    )

    parent_folder_response = Folder.select(ids=["path/to/parent-folder"])
    files_response = File.select(
        ids=["path/to/foo.txt", "path/to/foo.jpg", "path/to/bar.txt", "path/to/bar.jpg"]
    )

    Folder.update(
        _id="path/to/child-folder",
        data={"files": [File(path="path/to/foo.txt", type=FileType.EXEC)]},
    )
    updated_parent_folder_response = Folder.select(ids=["path/to/parent-folder"])
    updated_file_response = File.select(ids=["path/to/foo.txt"])

    print("parent folder:")
    pp.pprint(parent_folder_response)
    print("\nfiles:")
    pp.pprint(files_response)

    print("\nindirectly updated parent folder:")
    pp.pprint(updated_parent_folder_response)
    print("\nindirectly updated files:")
    pp.pprint(updated_file_response)
