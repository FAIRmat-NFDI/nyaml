# Installation guide

This tutorial serves as a guide to getting started with the `nyaml` software.

## What should you should know before this tutorial?

Nothing! We'll guide you through the installation step-by-step.

## What you will know at the end of this tutorial?

You will know

- how to install `nyaml`
- how to call the `nyaml2nxdl` command line tool

## Setup

It is recommended to use python 3.11+ with a dedicated virtual environment for this package. Learn how to manage [python versions](https://github.com/pyenv/pyenv) and [virtual environments](https://realpython.com/python-virtual-environments-a-primer/).

There are many alternatives to managing virtual environments and package dependencies (requirements). We recommend using [`uv`](https://github.com/astral-sh/uv), an extremely fast manager Python package and project manager. In this tutorial, you will find paralleled descriptions, using either `uv` or a more classical approach using `venv` and `pip`.

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
That command creates a new virtual environment in a directory called `.venv`.

## Installation

Install the latest stable version of this package from PyPI with

=== "uv"

    ```bash
    uv pip install nyaml
    ```

=== "pip"


    ```bash
    pip install nyaml
    ```

You can also install the latest _development_ version with

=== "uv"

    ```bash
    uv pip install git+https://github.com/FAIRmat-NFDI/nyaml.git
    ```

=== "pip"


    ```bash
    pip install git+https://github.com/FAIRmat-NFDI/nyaml.git
    ```

## Testing your installation

The nyaml `nyaml` package install a command line tool called `nyaml2nxdl` that can be used
to convert between XML and YAML representations of NeXus definitions written in the
NeXus Definition Language (NXDL).

Run `nyaml2nxdl help` to check that the installation was successful:

```bash exec="on" source="material-block" result="ini"
nyaml2nxdl --help
```

## Start using `nyaml`

That's it! You can now use `nyaml` and the plugins that you have installed!