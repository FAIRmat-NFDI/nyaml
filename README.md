[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nyaml) [![PyPI](https://img.shields.io/pypi/v/nyaml)](https://pypi.org/project/nyaml/)  [![Pytest](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml/badge.svg)](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml)

# Nyaml to nxdl

A tool to convert yaml NeXus application definitions (nyaml) to nexus definitions language (nxdl) and vice versa.

This tool is a simple command line interface and can be used by calling `nyaml2nxdl` or its shortcut `n2n`:

```console
user@box:~$ nyaml2nxdl --help
Usage: nyaml2nxdl [OPTIONS] INPUT_FILE

  Main function that distinguishes the input file format and launches the
  tools.

Options:
  --output-file TEXT   The output file path to write the converted file to
  --check-consistency  Check if yaml and nxdl can be converted from one to
                       another version recursively and get the same version of
                       file. E.g. from NXexample.nxdl.xml to
                       NXexample_consistency.nxdl.xml.
  --do-not-store-nxdl  Whether the input nxdl file will be stored as a comment
                       at the end of output yaml file.
  --verbose            Print in standard output keywords and value types to
                       help possible issues in yaml files
  --help               Show this message and exit.
```

**How the tool works**:
1. Reads the user-specified NeXus instance, either in yaml or xml format.
2. If input is in yaml, creates an instantiated nxdl schema xml tree by walking the dictionary nest.
   If input is in xml, creates a yaml file walking the dictionary nest.
3. Write the tree into a yaml file or a properly formatted nxdl file to disk.
4. Optionally, if --append argument is given,
   the XML or yaml input file is interpreted as an extension of a base class and the entries contained in it
   are appended below a standard NeXus base class.
   You need to specify both your input file (with yaml or xml extension) and NeXus class (with no extension).
   Both .yaml and .nxdl.xml file of the extended class are printed.


## How to install

The tool can be easily installed via pip

```
pip install nyaml
```

or as a development install from this repository

```
git clone https://github.com/FAIRmat-NFDI/nyaml.git
cd nyaml
pip install -e ".[dev]"
```

There is also a [pre-commit hook](https://pre-commit.com/#intro) available which formats the code and checks the
linting before actually commiting.
It can be installed with
```shell
pre-commit install
```
from the root of this repository.

## Documentation

**Rule set**: From transcoding YAML files we need to follow several rules.
* Named NeXus groups, which are instances of NeXus classes especially base or contributed classes. Creating (NXbeam) is a simple example of a request to define a group named according to NeXus default rules. mybeam1(NXbeam) or mybeam2(NXbeam) are examples how to create multiple named instances at the same hierarchy level.
* Members of groups so-called fields or attributes. A simple example of a member is voltage. Here the datatype is implied automatically as the default NeXus NX_CHAR type.  By contrast, voltage(NX_FLOAT) can be used to instantiate a member of class which should be of NeXus type NX_FLOAT.
* And attributes of either groups or fields. The mark '\@' have to precede the name of attributes.
* Optionality: For all fields, groups and attributes in `application definitions` are `required` by default, except anything (`recommended` or `optional`) mentioned.

**Special keywords**: Several keywords can be used as children of groups, fields, and attributes to specify the members of these. Groups, fields and attributes are nodes of the XML tree.
* **doc**:
   - A human-readable description/docstring
   - Doc string may also come as a list of doc parts when user wants to add `reference` for a concept. Or doc string could be a single doc block.
      ```yaml
         energy:  # field
            doc:
               - |
                 Part1 of the entire doc.
                 part1 of the entire doc.
               - |  # Reference for concept
                 xref:
                   spec: <spec>
                   term: <term>
                   url: <url>"
               - |
                 Rest of the doc
                 rest of the doc
         velocity:  # field
            doc: |
               A single block of doc string.
      ```
      Such structure of doc would appear in `nxdl` as
      ```xml
      ...
      <field name="energy">
        <doc>
            Part1 of the entire doc.
            part1 of the entire doc.

                This concept is related to term `&lt;term&gt;`_ of the &lt;spec&gt; standard.
            .. _&lt;term&gt;: &lt;url&gt;

            Rest of the doc
            rest of the doc
        </doc>
      </field>
      <field name="velocity">
        <doc>
            A single block of doc string.
        </doc>
      </field>
      ```



* **exists** Options are recommended, required, [min, 1, max, `infty`] numbers like here 1 can be replaced by any `uint` (unsigned integer), or `infty` to indicate no restriction on how frequently the entry can occur inside the NXDL schema at the same hierarchy level.
* **link** Define links between nodes.
* **units** A statement introducing NeXus-compliant NXDL units arguments, like NX_VOLTAGE
* **dimensions** Details which dimensional arrays to expect
* **dim** Shorthand notation for dimensions, e.g., `(n, )` for an 1D array of length `n` or `(n, m)` for an 2D array of size `n x m`.
* **enumeration** Python list of strings which are considered as recommended entries to choose from.
* **dim_parameters** `dim` which is a child of `dimension` and the `dim` might have several attributes `ref`,
`incr` including `index` and `value`. So while writing `yaml` file schema definition please following structure:
```yaml
dimensions:
   rank: integer value
   dim: [[ind_1, val_1], [ind_2, val_2], ...]
   dim_parameters:
      ref: [ref_value_1, ref_value_2, ...]
      incr: [incr_value_1, incr_value_2, ...]
```
Keep in mind that length of all the lists must have the **same size**.
**Important Note**: The attributes `ref`, `incr`, `index` are deprecated.

## Project roadmap

The NOMAD team is currently working to establish a one-to-one mapping between NeXus definitions and the NOMAD MetaInfo(scientific data model in nomad). As soon as this is in place the YAML files will be annotated with further metadata so that they can serve two purposes. On the one hand they can serve as an instance for a schema to create a GUI representation of a NOMAD Oasis ELN schema. On the other hand the YAML to NXDL converter will skip all those pieces of information which are irrelevant from a NeXus perspective.
