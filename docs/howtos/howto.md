# Getting started with nyaml

`nyaml` is a Python package that is [published on PyPI](https://pypi.org/project/nyaml/).

## How to Install

install the `nyaml` Python package:
=== "uv"

    ```bash
    uv pip install nyaml
    ```

=== "pip"


    ```bash
    pip install nyaml
    ```

## How to Use

`nyaml` works as a command line tool to convert NeXus application definitions or base classes from YAML file format into the `nxdl.xml` file format and vice-versa. The converter can be called by the command

::: mkdocs-click
    :module: nyaml.cli
    :command: launch_tool
    :prog_name: nyaml2nxdl
    :depth: 2
    :style: table
    :list_subcommands: True

__Brief interpretation of the command line options__:

`--output-file`: The option defines the output file name (including the file extension), if the option is not specified the converter will define the output file name from the input file. Exemplified for a given input file `NXapplication.nxdl.xml (NXapplication.yaml)`, the resultant file will be `NXapplication_parser.yaml (NXapplication.nxdl.xml)`.

`--check-consistency`: With the option `--check-consistency`, `nyaml` produces the same type of file as the input, e.g. for input `NXapplication.nxdl.xml` the output file is `NXapplication_consistency.nxdl.xml`. When converting the `nxdl.xml` file into YAML it also stores the `nxdl.xml` file at the end of YAML file with a hash.

`--do-not-store-nxdl`: The option `--do-not-store-nxdl` prevents the YAML file from storing the original `nxdl.xml` text as comment.

`--verbose`: The `verbose` option is to identify any issues arising from unexpected conversion or syntax errors that occur while converting the file from one to another.

`--help`: The `help` option shows this message and exits.
