import pathlib

from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="pydantic-redis",
    version="0.4.3",
    description="This package provides a simple ORM for redis using pydantic-like models.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/sopherapps/pydantic-redis",
    author="Martin Ahindura",
    author_email="team.sopherapps@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=find_packages(exclude=("test",)),
    include_package_data=True,
    install_requires=["pydantic", "redis", "hiredis", "orjson"],
    entry_points={},
)
