---
title: "nyaml: Format Converter for the NeXus Data Model"
tags:
  - Python
  - NeXus
  - NXDL
  - YAML
  - XML

authors:
  - given-names: Rubel
    surname: Mozumder
    orcid: https://orcid.org/0009-0007-5926-6646
    affiliation: 1
    equal-contrib: true
  - given-names: Lukas
    surname: Pielsticker
    orcid: https://orcid.org/0000-0001-9361-8333
    affiliation: "1,3"
    equal-contrib: true
  - given-names: Markus
    surname: Kühbach
    orcid: https://orcid.org/0000-0002-7117-5196
    affiliation: 1
    equal-contrib: true
  - given-names: Andrea
    surname: Albino
    orcid: https://orcid.org/0000-0001-9280-7431
    affiliation: 1
    equal-contrib: true
  - given-names: Florian
    surname: Dobener
    orcid: https://orcid.org/0000-0003-1987-6224
    affiliation: 1
    equal-contrib: true
  - given-names: Sherjeel
    surname: Shabih
    orcid: https://orcid.org/0009-0008-6635-4465
    affiliation: 1
    equal-contrib: true
  - given-names: Christoph
    surname: Koch
    orcid: https://orcid.org/0000-0002-3984-1523
    affiliation: 1
  - given-names: Heiko B.
    surname: Weber
    orcid: https://orcid.org/0000-0002-6403-9022
    affiliation: 2
  - given-names: José Antonio
    surname: Márquez Prieto
    orcid: https://orcid.org/0000-0002-8173-2566
    affiliation: 1
  - given-names: Claudia
    surname: Draxl
    orcid: https://orcid.org/0000-0003-3523-6657
    affiliation: 1
  - given-names: Sandor
    surname: Brockhauser
    orcid: https://orcid.org/0000-0002-9700-4803
    affiliation: 1
    equal-contrib: true

affiliations:
  - name: Physics Department and CSMB, Humboldt-Universität zu Berlin, Berlin, Germany
    index: 1
  - name: Lehrstuhl für Angewandte Physik, Friedrich-Alexander-Universität Erlangen-Nürnberg, Erlangen, Germany
    index: 2
  - name: Department Heterogeneous Reactions, Max Planck Institute for Chemical Energy Conversion, Mülheim an der Ruhr, Germany
    index: 3

date: 01 July 2025
bibliography: paper.bib
---

# Summary

The NeXus scientific data format standard [@Koennecke:2015], which was originally introduced for neutron, X-ray, and muon science, has in recent years seen a significant enhancement across diverse scientific domains such as materials science. NeXus definitions specify the hierarchical structure and semantics of valid NeXus files and are written in XML [@xml10] using the NeXus Definition Language (NXDL), which itself is specified using XSD (XML Schema Definition).

__nyaml__ is a Python-based tool with both a command-line interface and an importable API that facilitates the conversion between NXDL XML and a simplified YAML [@YAML2009] representation. YAML's indentation-based syntax enhances human readability and simplifies manual editing. By providing a reliable, lossless round-trip conversion between XML and YAML, __nyaml__ enables developers to edit NeXus definitions more efficiently without sacrificing structural or semantic fidelity.

# Statement of need
With the embrace from diverse scientific domains, the growth of both the standard and the number of NeXus definition developers makes it all the more important to ensure that the development process is both user-friendly and resilient to errors. The existing representation of NeXus definitions in XML offers structural rigor through the NeXus Definition Language (NXDL) and a well-defined hierarchy for metadata and data types. However, it is verbose and can be difficult to edit by hand. Writing and maintaining NXDL files often involves dealing with deeply nested elements and strict syntax, which can be error-prone and time-consuming, especially for users who are not familiar with XML development. __nyaml__ addresses these challenges by enabling the development of NeXus definitions in a cleaner, YAML-based format while preserving the full structure, semantics, and developer comments of the original XML.


# nyaml Converter

The __nyaml__ tool is a Python package, containing the several modules, that provides a command line interface for converting NeXus application definitions or base classes from YAML format (file with a __.yaml__ extension) into the XML format (file with a __.nxdl.xml__ extension) and vice-versa. To write a NeXus application defintion or a base class in YAML format, the __nyaml__ package introduces a set of the keywords and syntactic rules (see [Documentation](https://fairmat-nfdi.github.io/nyaml)) that are specific to the NXDL (NeXus Definition Language) in the YAML format.

 The __nyaml__ package is designed to be used as a command line tool, but it can also be utilised as a Python module for programmatic use. The package in published in PyPI and therefore can be installed using python package manager __pip__. The converter command is invoked by the __nyaml2nxdl__ registered in the __nyaml.cli__ module [@Click:2025]. In that module, the function __launch_tool__ decides upon the input file type which conversion (either from YAML to XML or XML to YAML) will be invoked and execute the corresponding pipline of the data workflow (\autoref{fig:nyaml_workflow}).

![Converter workflow for nyaml tool, XML to YAML and vice-versa \label{fig:nyaml_workflow}](assets/workflow-1.pdf){ width=75% }

## YAML to XML

The module __nyaml.nyaml2nxdl__ contains the necessary functions, classes, and methods to implement the algorithm for converting the NXDL schema from YAML to XML. The function __nyaml2nxdl__ is the main entry point for executing the conversion from YAML to XML with the execution in three sequential tasks:

1. Using __PyYAML__ [@PyYAML:2024] it collects and tracks comments in YAML file,
2. It parses the YAML file into a Python dictionary object, and finally,
3. It writes the XML tree in a file in accordance with the NXDL concepts including the comments from the first step.

The conversion algorithm interprets the specific keywords and syntactic rules to read the NXDL in the YAML format to transcode from the YAML to the XML representation. Taking leverage of the NeXus NXDL rules, the conversion detect the possible inconveniences in the YAML content and raises an error or warning if the NXDL rules are not properly followed in YAML.

## XML to YAML

The __nyaml.nxdl2yaml__ module provides the core functionality for converting NXDL schemas from XML to YAML format. The main component, the __Nxdl2yaml__ class, orchestrates the conversion process through several key steps:

1. It uses the __lxml__ library [@lxml:2025] to parse the XML file and build an XML tree structure.
2. It generates a YAML file from this XML tree, applying YAML-specific keywords and formatting rules.
3. It computes a SHA256 hash of the generated YAML content and appends both the hash and the original XML content as comments at the end of the YAML file.

By attaching the XML content and its hash to the YAML output, the tool enables lossless round-trip conversions, provided the YAML content remains unchanged (since the SHA256 hash will match). This caching approach streamlines the XML → YAML → XML workflow and facilitates straightforward comparisons of XML files in version control systems such as Git.

# Evaluation from NIAC

The NeXus International Advisory Committee (NIAC) is the governing body responsible for overseeing the development and maintenance of the NeXus data standard. A core responsibility of the NIAC is the stewardship of the NeXus Definition Language (NXDL), the XML-based schema that defines the hierarchical structure and semantics of NeXus data files [Koennecke:2015]. As part of its mission to facilitate the standardization of NeXus definitions in NXDL, NIAC has recently reviewed and formally accepted the __nyaml__ tool. Following a successful evaluation, NIAC has approved __nyaml__ and endorsed it as the recommended tool for preparing NeXus definition proposals. In support of this decision, the official NeXus definition repository was updated to integrate __nyaml__ into its workflow through the addition of two makefile targets: 'make nyaml', which converts existing definitions from the canonical nxdl.xml format into .yaml, and 'make nxdl', which detects modified or newly added .yaml files and converts them back into valid nxdl.xml format for submission and version control. This integration ensures that contributions made in .nyaml are compatible with the existing XML-based infrastructure. The adoption of __nyaml__ by NIAC reflects an ongoing commitment to fostering community engagement and modernising the technical tools underpinning the NeXus standard [@NIAC:2025].

# Acknowledgements
The __nyaml__ software development is funded by the German National Research Data Infrastructure
(NDFI) consortia FAIRmat (Deutsche Forschungsgemeinschaft DFG, 460197019).

# References

