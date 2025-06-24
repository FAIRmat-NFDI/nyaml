[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nyaml) [![PyPI](https://img.shields.io/pypi/v/nyaml)](https://pypi.org/project/nyaml/) [![Pytest](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml/badge.svg)](https://github.com/FAIRmat-NFDI/nyaml/actions/workflows/pytest.yaml)[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1323437.svg)](https://doi.org/10.5281/zenodo.13860810)

# Table of Contents

1. [Introduction](#introduction)
2. [nyaml Workflow](#nyaml-workflow)
3. [How to Use nyaml Tool](#how-to-use-nyaml-tool)
4. [Conversion from YAML to XML](#conversion-from-yaml-to-xml)
5. [Design of NeXus Ontology and Terms in YAML](#design-of-nexus-dataformat-and-terms-in-yaml)
   - [Root section for base classes and application definitions](#root-section-for-base-classes-and-application-definitions)
   - [NeXus Group](#nexus-group)
   - [NeXus Field and NeXus Attrubute](#nexus-field-and-nexus-attrubute)
   - [NeXus Link](#nexus-link)
   - [NeXus Choice](#nexus-choice)
6. [Special Keywords in YAML](#special-keywords-in-yaml)
   - [Keyword `exists`](#keyword-exists)
   - [Keyword `unit`](#keyword-unit)
   - [Keyword `dimensions`](#keyword-dimensions)
   - [Keyword `enumeration`](#keyword-enumeration)
   - [Keyword `xref`](#keyword-xref)
7. [How to Install nyaml](#how-to-use-nyaml-tool)
8. [Conclusion](#conclusion)
9. [References](#references)

# nyaml Tool for NeXus
The `nyaml` tool is a Python package that provides a command line interface for converting NeXus application definitions or base classes from `yaml` file format into the `nxdl.xml` file format and vice-versa. The converter can be called by the command `nyaml2nxdl`.

Check full documentation of the tool in [gh] https://fairmat-nfdi.github.io/nyaml/