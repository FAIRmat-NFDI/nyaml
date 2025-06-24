# nyaml Installation and Command
`nyaml` is a Python package [published on PyPI](https://pypi.org/project/nyaml/).

## How to Install nyaml
The tool is published to `PyPI` and available for pip install
```bash
$ pip install nyaml
```

To contribute to the tool or to install it in development mode
```bash
$ git clone https://github.com/FAIRmat-NFDI/nyaml.git
$ cd nyaml
$ pip install -e ".[dev]"
```

There is also a [pre-commit hook](https://pre-commit.com/#intro) available which formats the code and checks the linting before actually commiting. It can be installed with
```bash
$ pre-commit install
```

## How to Use the nyaml Tool
The `nyaml` works as a command line tool to convert NeXus application definition or base class from `yaml` file format into the `nxdl.xml` file format and vice-versa. The converter can be called by the command

```bash
$ nyaml2nxdl [OPTIONS] [INPUT_FILE]
```
with the available options:
```output
  --output-file TEXT   Specify the output file path for the converted file.
  --check-consistency  Check whether YAML and NXDL can be recursively
                       converted, ensuring version consistency.
  --do-not-store-nxdl  Prevent the input NXDL file from being stored as a
                       comment at the end of the output YAML file.
  --verbose            Display keywords and value types in standard output to
                       assist in identifying issues in YAML files.
  --help               Show this message and exit.
```
The `--output-file` option defines the output file name (including the fle extension), otherwise the converter will define the output file name from the input file, e.g., for a input file `NXapplication.nxdl.xml (NXapplication.yaml)`, the resultant file will be `NXapplication_parser.yaml (NXapplication.nxdl.xml)`. With the option `--check-consistency` *the nyaml produces the same type of file as the input, e.g. for input `NXapplication.nxdl.xml` the output file is `NXapplication_consistency.nxd.xml`. The intention for this option is to verify proper conversion and version conversion of the file. When converting the `nxdl.xml` file into `yaml` it also stores the `nxdl.xml` file at the end of `yaml` file with a hash. The option `--do-not-store-nxdl` prevents the `yaml` file from storing the original `nxdl.xml` text as comment. The `verbose` option is to identify any issues arising from unexpected conversion or syntax errors that occur while converting the file from one to another.
