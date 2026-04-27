# Development guide

This tutorial will guide you through how to set up a working environment for developing `nyaml`.

## What should you know before this tutorial?

- You should read the [installation tutorial](installation.md).

## What you will know at the end of this tutorial?

You will know

- how to set up your environment for developing `nyaml`
- how to make changes to the software
- how to test the software
- how to contribute on GitHub
- how to use nyaml as a NOMAD plugin

## Contributing

??? info "Structure of the `nyaml` repository"
    The software tools are located inside [`src/nyaml`](https://github.com/FAIRmat-NFDI/nyaml/tree/main/src/nyaml). They are shipped with unit tests located in [`tests`](https://github.com/FAIRmat-NFDI/nyaml/tree/main/tests).

### Setup

It is recommended to use Python 3.11+ with a dedicated virtual environment for this package. Learn how to manage [python versions](https://github.com/pyenv/pyenv) and [virtual environments](https://realpython.com/python-virtual-environments-a-primer/). We recommend using [`uv`](https://github.com/astral-sh/uv), an extremely fast Python package and project manager. In this tutorial, you will find paralleled instrctions, using either `uv` or a more classical approach using `venv` and `pip`.

Start by creating a virtual environment:

=== "uv"
    `uv` is capable of creating a virtual environment and install the required Python version at the same time.

    ```bash
    uv venv --python 3.12
    ```

=== "venv"

    Note that you will need to install the Python version manually beforehand.

    ```bash
    python -m venv .venv
    ```

That command creates a new virtual environment in a directory called .venv.

### Development installation

We start by cloning the repository:

```console
git clone https://github.com/FAIRmat-NFDI/nyaml.git
cd nyaml
```
Next, we install the package in editable mode (together with its dependencies):

=== "uv"

    ```bash
    uv pip install -e ".[dev]"
    ```

=== "pip"

    Note that you will need to install the Python version manually beforehand.

    ```bash
    pip install --upgrade pip
    pip install -e ".[dev]"
    ```

### Linting and formatting

We are using ruff and mypy for linting, formatting, and type checking. It is recommended to use the [pre-commit hook](https://pre-commit.com/#intro) available for ruff which formats the code and runs linting checks before actually making a Git commit.

Install the pre-commit hook by running

```console
pre-commit install
```

from the root of this repository.

### Testing

There exist unit tests for the software written in [pytest](https://docs.pytest.org/en/stable/) which can be used as follows:

```console
pytest -sv tests
```

### Editing the documentation

We are using [`mkdocs`](https://www.mkdocs.org/) for the documentation. If you edit the documentation, you can build it locally. For this, you need to install an additional set of dependencies:

=== "uv"

    ```bash
    uv pip install -e ".[docs]"
    ```

=== "pip"

    ```bash
    pip install -e ".[docs]"
    ```
You can then serve the documentation locally by running

```console
mkdocs serve
```

### Contributing to the package on GitHub

Once you are happy with the changes, please commit them on a feature branch on a fork of the original repository and create a pull request on GitHub. We run a number of GitHub actions that check code formatting and linting, run the tests in an isolated environment, and build the documentation. Once these actions pass and a peer review of the code has occurred, your code will be accepted.

## Reporting issues and seeking support

If you face any issues with the tool or when setting up the development environment, please create a new [GitHub Issue](https://github.com/FAIRmat-NFDI/nyaml/issues/new?template=bug.yaml).

For general questions or support, see our [contact page](../contact.md) or join the [NOMAD Discord channel](https://discord.gg/Gyzx3ukUw8).
