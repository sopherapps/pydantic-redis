# Contributing to pydantic-redis

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use github to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow), So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we
use [Github Flow](https://docs.github.com/en/get-started/quickstart/github-flow)). We actively welcome your pull
requests:

1. Fork the repo and create your branch from `master`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software Licenses

In short, when you submit code changes, your submissions are understood to be under the
same [MIT License](./LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/sopherapps/pydantic-redis/issues)

We use GitHub issues to track public bugs. Report a bug
by [opening a new issue](https://github.com/sopherapps/pydantic-redis/issues); it's that easy!

## Write bug reports with detail, background, and sample code

[This is an example](http://stackoverflow.com/q/12488905/180626).
Here's [another example from Craig Hockenberry](http://www.openradar.me/11905408).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

People *love* thorough bug reports. I'm not even kidding.

## Use a Consistent Coding Style

* Use [black](https://pypi.org/project/black/)

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## How to test

- Clone the repo and enter its root folder

  ```bash
  git clone https://github.com/sopherapps/pydantic-redis.git && cd pydantic-redis
  ```

- Create a virtual environment and activate it

  ```bash
  virtualenv -p /usr/bin/python3.8 env && source env/bin/activate
  ```

- Install the dependencies

  ```bash
  pip install -r requirements.txt
  ```

- Run the pre-commit installation

  ```bash
  pre-commit install
  ```

- Run the tests command

  ```bash
  pytest --benchmark-disable
  ```

- Run benchmarks

  ```bash
  pytest --benchmark-compare --benchmark-autosave
  ```

- Or run to get benchmarks summary

  ```shell
  pytest test/test_benchmarks.py --benchmark-columns=mean,min,max --benchmark-name=short
  ```

## References

This document was adapted from [a gist by Brian A. Danielak](https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62) which
was originally adapted from
the open-source contribution guidelines
for [Facebook's Draft](https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md)
