# Getting started with nyaml

`nyaml` is a command line tool that converts NeXus definitions between YAML and NXDL XML format. It is [published on PyPI](https://pypi.org/project/nyaml/){:target="_blank" rel="noopener"}.

!!! note
    `nyaml` is a *transcoding* tool that converts between YAML and XML representations of NeXus definitions. Validation of the resulting NXDL files against the NeXus design principle [official NeXus](https://manual.nexusformat.org/design.html){:target="_blank" rel="noopener"} is not handled by `nyaml`, but can instead be done  through the CI/CD pipeline provided by the [official NeXus definitions repository](https://github.com/nexusformat/definitions){:target="_blank" rel="noopener"}.

## How to install

Install the `nyaml` Python package:

=== "uv"

    ```bash
    uv pip install nyaml
    ```

=== "pip"

    ```bash
    pip install nyaml
    ```

## How to use

`nyaml` works as a command line tool to convert NeXus application definitions or base classes from YAML file format into the `nxdl.xml` file format and vice-versa. The converter can be called by the command

::: mkdocs-click
    :module: nyaml.cli
    :command: launch_tool
    :prog_name: nyaml2nxdl
    :depth: 2
    :style: table
    :list_subcommands: True

**Brief interpretation of the command line options**:

`--output-file`: Defines the output file name (including the file extension). If not specified, the converter derives the output file name from the input file. For example, given input `NXapplication.nxdl.xml` (`NXapplication.yaml`), the output will be `NXapplication_parser.yaml` (`NXapplication.nxdl.xml`).

`--check-consistency`: Produces the same file type as the input. For input `NXapplication.nxdl.xml` the output is `NXapplication_consistency.nxdl.xml`. When converting an `nxdl.xml` file to YAML it also stores the `nxdl.xml` text at the end of the YAML file with a hash.

`--do-not-store-nxdl`: Prevents the YAML file from storing the original `nxdl.xml` text as a comment.

`--verbose`: Identifies any issues arising from unexpected conversion or syntax errors that occur while converting between formats.

`--help`: Shows the help message and exits.

## After conversion: validating your definition

`nyaml` converts your definition between formats but does not validate it against the NeXus schema. To validate, fork the [official NeXus definitions repository](https://github.com/nexusformat/definitions){:target="_blank" rel="noopener"} and open a pull request. The repository runs an automated validation workflow on every pull request. Once approved, your definition is contributed to the shared NeXus definitions catalogue.
