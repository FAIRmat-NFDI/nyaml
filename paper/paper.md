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
  - given-names: Lukas
    surname: Pielsticker
    orcid: https://orcid.org/0000-0001-9361-8333
    affiliation: "1,3"
  - given-names: Markus
    surname: Kühbach
    orcid: https://orcid.org/0000-0002-7117-5196
    affiliation: 1
  - given-names: Andrea
    surname: Albino
    orcid: https://orcid.org/0000-0001-9280-7431
    affiliation: 1
  - given-names: Florian
    surname: Dobener
    orcid: https://orcid.org/0000-0003-1987-6224
    affiliation: 1
  - given-names: Sherjeel
    surname: Shabih
    orcid: https://orcid.org/0009-0008-6635-4465
    affiliation: 1
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

affiliations:
  - name: Physics Department and CSMB, Humboldt-Universität zu Berlin, Zum Großen Windkanal 2, D-12489 Berlin, Germany
    index: 1
  - name: Lehrstuhl für Angewandte Physik, Friedrich-Alexander-Universität Erlangen-Nürnberg, Staudtstra{\ss}e 7, D-91058 Erlangen, Germany
    index: 2
  - name: Department Heterogeneous Reactions, Max Planck Institute for Chemical Energy Conversion, Stiftstraße 34-36, D-45470 Mülheim an der Ruhr, Germany
    index: 3

date: 01 July 2025
bibliography: paper.bib
---
# Summary

The NeXus scientific data format standard [@Könnecke:2015; @Könnecke2006; @Klosowski1997], which was originally introduced for neutron, X-ray, and muon science, has in recent years seen a significant enhancement across diverse scientific domains such as materials science. NeXus definitions, consisting of application definitions or base classes, specify the hierarchical structure and semantics of valid NeXus files and are written in XML [@xml10] using the NeXus Definition Language (NXDL), which itself is specified using XSD (XML Schema Definition).

__nyaml__ is a Python-based tool with both a command-line interface and an importable API that facilitates the conversion between NXDL XML and a simplified YAML [@YAML11] representation. YAML's indentation-based syntax enhances human readability and simplifies manual editing. By providing a reliable, lossless round-trip conversion between XML and YAML, __nyaml__ enables developers to edit NeXus definitions more efficiently without sacrificing structural or semantic fidelity.

# Statement of need
The growth of both the standard and the number of NeXus definition developers makes it all the more important to ensure that the development process is both user-friendly and resilient to errors. The existing representation of NeXus definitions in XML offers structural rigor through the NeXus Definition Language (NXDL) and a well-defined hierarchy for metadata and data types. However, it is verbose and can be difficult to edit by hand. Writing and maintaining NXDL files often involves dealing with deeply nested elements and strict syntax, which can be error-prone and time-consuming, especially for users who are not familiar with XML development. __nyaml__ addresses these challenges by enabling the development of NeXus definitions in a cleaner, YAML-based format while preserving the full structure, semantics, and developer comments of the original XML.


# Conversion process

The __nyaml__ tool is a Python package developed for converting NeXus definitions from YAML format (files with a __.yaml__ extension) into the XML format (files with a __.nxdl.xml__ extension), and vice versa. The package is published on PyPI and therefore can be installed using Python package managers (e.g., __pip__ [@pip2025]). To write or modify NeXus definitions in YAML format, modification of existing definitions the conversion goes through __XML $\rightarrow$ YAML $\rightarrow$ modification of YAML $\rightarrow$ XML__ and new definitions that go through __YAML $\rightarrow$ XML__, the __nyaml__ package introduces a set of keywords and syntactic rules (see [documentation](https://fairmat-nfdi.github.io/nyaml)) that are specific to NXDL (NeXus Definition Language) in YAML.


The tool is designed to be used as a command-line utility but can also be utilized as a Python module for programmatic usages. The converter command is invoked using __nyaml2nxdl__, which determines the conversion direction based on the input file (either from YAML to XML or XML to YAML) and delegates the task to the appropriate converter. The converter then executes the corresponding data workflow pipeline (see \autoref{fig:nyaml_workflow}). These workflows, __YAML to XML__ and __XML to YAML__, are designed to ensure that the conversion process is efficient, reliable, reproducible, and preserves the integrity of the original NeXus data structure and semantics.

![Converter workflow for nyaml tool, XML to YAML and vice-versa \label{fig:nyaml_workflow}](assets/workflow-1.pdf){ width=75% }

Conversion from __YAML to XML__ follows specific workflow steps (depicted in \autoref{fig:nyaml_workflow}) according to NXDL rules and syntax specific to the YAML format (see [documentation](https://fairmat-nfdi.github.io/nyaml)). Starting from a given input YAML file (see \autoref{fig:nyaml_workflow}), the workflow performs the following steps:

1. The __nyaml2nxdl__ converter collects the input __.yaml__ file.

2. Using __PyYAML__ [@PyYAML:2024], the converter collects and tracks comments in the YAML file.

3. The converter parses the YAML file into a nested hashed map—a Python dictionary object.

4. The converter writes the hashed map and comments into an output XML file in accordance with NXDL concepts.


The conversion algorithm interprets the specific keywords and syntactic rules to transcode the NXDL from YAML into XML (see [documentation](https://fairmat-nfdi.github.io/nyaml)). Leveraging the NXDL rules, the conversion process detects possible inconsistencies in the YAML content and raises errors or warnings if the rules are not properly followed.


The __XML to YAML__ conversion also follows a well-defined data workflow (\autoref{fig:nyaml_workflow}) that converts a given input XML file into a YAML file. The workflow begins with the XML input and proceeds as follows:


1. The __nxdl2nyaml__ converter takes over the __.nxdl.xml__ file.

2. Using __lxml__ [@lxml:2025], the converter parses the XML file and builds an XML tree structure.

3. Applying YAML-specific keywords and formatting rules, the converter generates a YAML file from the XML tree.

4. The converter computes a SHA256 hash of the generated YAML content.

5. The converter writes the YAML file and appends both the hash and the original XML content as comments at the end of the YAML file.


By attaching the hash and the original XML content to the YAML output (__.yaml__ file), the tool enables lossless round-trip conversions — if the YAML is not modified, converting back from YAML to XML, the original commented XML content will be written back to the XML file without any modification. However, if the YAML content is modified, the XML tree will be reconstructed from the YAML content and written to the XML file, which will differ from the original XML content included in the comments. This caching approach streamlines the XML → YAML → XML workflow and facilitates straightforward comparisons of XML files in version control systems such as Git.

# Evaluation from NIAC

The NeXus International Advisory Committee (NIAC) is the governing body responsible for overseeing the development and maintenance of the NeXus data standard. A core responsibility of the NIAC is the stewardship of the NeXus Definition Language (NXDL), the XML-based definitions that define the hierarchical structure and semantics of NeXus data files [Könnecke:2015]. As part of its mission to facilitate the standardization of NeXus definitions in NXDL, NIAC has recently reviewed and formally accepted the __nyaml__ tool. Following a successful evaluation, NIAC has approved __nyaml__ and endorsed it as the recommended tool for preparing NeXus definition proposals. In support of this decision, the official NeXus definition repository [@nexusDef:2024] was updated to integrate __nyaml__ into its workflow through the addition of two makefile targets: 'make nyaml' [@nyamlIntegration:2024], which converts existing definitions from the canonical nxdl.xml format into .yaml, and 'make nxdl', which detects modified or newly added .yaml files and converts them back into valid nxdl.xml format for submission and version control. This integration ensures that contributions made in .nyaml are compatible with the existing XML-based infrastructure. The adoption of __nyaml__ by NIAC reflects an ongoing commitment to fostering community engagement and modernizing the technical tools underpinning the NeXus standard [@NIAC:2025].

# Acknowledgements
The __nyaml__ software development is funded by the German National Research Data Infrastructure
(NFDI) consortia FAIRmat (Deutsche Forschungsgemeinschaft DFG, 460197019).

# References

