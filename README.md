[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nyaml) [![PyPI](https://img.shields.io/pypi/v/nyaml)](https://pypi.org/project/nyaml/)  [![Pytest](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml/badge.svg)](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml)

# Converting nyaml to NXDL

`nyaml` is a versatile tool designed for converting NeXus application definitions from YAML (nyaml) to the Nexus Definitions Language (nxdl) format and vice versa. This command-line interface offers a simple and efficient way to work with NeXus data definitions.

## Installation

You can easily install the tool using `pip`:

```bash
pip install nyaml
```

Alternatively, you can install it as a development package from the GitHub repository:

```bash
git clone https://github.com/FAIRmat-NFDI/nyaml.git
cd nyaml
pip install -e ".[dev]"
```

We also provide a pre-commit hook for code formatting and linting, which you can install with:

```bash
pre-commit install
```

## Usage

The primary commands for using nyaml are `nyaml2nxdl` and its shortcut, `n2n`. Here is an overview of the available options:

```bash
user@box:~$ nyaml2nxdl --help
Usage: nyaml2nxdl [OPTIONS] INPUT_FILE

  Main function that distinguishes the input file format and launches the
  tools.

Options:
  --output-file TEXT   Specify the output file path for the converted file.
  --check-consistency  Check whether YAML and NXDL can be recursively
                       converted, ensuring version consistency.
  --do-not-store-nxdl  Prevent the input NXDL file from being stored as a
                       comment at the end of the output YAML file.
  --verbose            Display keywords and value types in standard output to
                       assist in identifying issues in YAML files.
  --help               Show this message and exit.
```

## How It Works

The tool operates by:

1. Reading the user-specified NeXus definition, either in YAML or XML format.
2. If the input is in YAML, it creates an instantiated NXDL schema XML tree by parsing the YAML dictionary.
3. If the input is in XML, it creates a YAML file by parsing the XML tree.
4. The tool then writes the resulting data structure to either a YAML or NXDL file on disk.

## Documentation

### Rule Set

When transcribing YAML files, it's important to adhere to the following rules:

- **Named NeXus Groups**: Instances of NeXus classes, especially base or contributed classes, are represented as named NeXus groups. For example, creating `(NXbeam)` is a simple example of defining a group according to NeXus default rules. You can create multiple named instances at the same hierarchy level, such as `mybeam1(NXbeam)` or `mybeam2(NXbeam)`.

- **Members of Groups**: Members within groups are referred to as fields or attributes. A simple example is the field `voltage`, where the data type is implied automatically as the default NeXus `NX_CHAR` type. To specify a different type, use `voltage(NX_FLOAT)`.

- **Attributes**: Attributes of groups or fields are preceded by the '@' symbol.

- **Optionality**: By default, all groups, fields, and attributes in application definitions are required, except those explicitly marked as recommended or optional.

- **Special Keywords**: There exists a set of special keywords that can be used as children of groups, fields, and attributes to specify their properties. These elements are nodes of the XML tree.

### Doc Structure

The `doc` keyword is used for adding human-readable descriptions or docstrings. It can be a single block or a list of doc parts. Here's an example:

```yaml
energy:
  doc:
    - |
      Part1 of the entire doc.
      part1 of the entire doc.
    - |
      xref:
        spec: <spec>
        term: <term>
        url: <url>
    - |
      Rest of the doc
      rest of the doc
  velocity:  # field
    doc: |
        A single block of doc string.
```

This structure appears in Nxdl as follows:

```xml
<field name="energy">
    <doc>
          Part1 of the entire doc.
          part1 of the entire doc.

          This concept is related to term `&lt;term&gt;`_ of the &lt;spec&gt; standard.

          .. _&lt;term&gt;: &lt;url&gt;

          Rest of the doc
          rest of the doc
    </doc>
    <field name="velocity">
        <doc>
              A single block of doc string.
        </doc>
    </field>
</field>
```

### Additional Keywords

- **exists**: Options for `exists` can be recommended, required, or specified as `[min, 1, max, infty]`. Replace `1` with any unsigned integer or use `infty` to indicate no restriction on occurrence within the Nxdl schema at the same hierarchy level.

- **link**: Defines [links](https://manual.nexusformat.org/nxdl_desc.html#linktype) between nodes.

- **units**: Introduces [NeXus-compliant `NXDL` units](https://manual.nexusformat.org/nxdl-types.html#nxdl-units) arguments, such as `NX_VOLTAGE`.

- **dimensions**: Details the expected dimensional arrays.

- **dim**: A shorthand notation for dimensions, e.g., `(n, )` for a 1D array of length `n` or `(n, m)` for a 2D array of size `n x m`.

- **enumeration**: A Python list of strings considered as recommended entries.

- **dim_parameters**: A child of `dimension` with attributes like `ref` and `incr`, including `index` and `value`.

Keep in mind that the length of all lists must match. Note that the attributes `ref`, `incr`, and `index` are deprecated.

## Project Roadmap

The NOMAD team is actively working on establishing a one-to-one mapping between NeXus definitions and the [NOMAD schemas](https://nomad-lab.eu/prod/v1/staging/docs/tutorial/custom.html) (scientific data model in NOMAD). Once completed, YAML files will be annotated with additional metadata to serve dual purposes: as an instance for a schema to create a GUI representation of a NOMAD Oasis ELN schema and as a YAML to NXDL converter that ignores irrelevant information from a NeXus perspective.