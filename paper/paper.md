---
title: 'nyaml: A Format Converter for NeXus Data Model.'
tags:
    - Python
    - NeXus
    - NXDL
authors:
  - name: Adrian M. Price-Whelan
    orcid: 0000-0000-0000-0000
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Author Without ORCID
    equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
    affiliation: 2
  - name: Author with no affiliation
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: 3
  - given-names: Ludwig
    dropping-particle: van
    surname: Beethoven
    affiliation: 3
affiliations:
 - name: Lyman Spitzer, Jr. Fellow, Princeton University, United States
   index: 1
   ror: 00hx57361
 - name: Institution Name, Country
   index: 2
 - name: Independent Researcher, Country
   index: 3
date: 13 August 2017
bibliography: paper.bib
---

# Summary

The NeXus scientific data format [@Koennecke:2015] is a widely adopted standard for organizing and sharing scientific data, particularly in the field of materials characterization. NeXus definitions specify the hierarchical structure and semantics of valid NeXus files and are written in XML using the NeXus Definition Language (NXDL), which itself is specified using XSD (XML Schema Definition). nyaml is a Python-based tool with both a command-line interface and an importable API that facilitates the conversion between NXDL XML and a simplified YAML representation. YAML's indentation-based syntax enhances human readability and simplifies manual editing. By providing a reliable, lossless round-trip conversion between XML and YAML, nyaml enables developers to edit NeXus definitions more efficiently without sacrificing structural or semantic fidelity.


# Statement of need

The NeXus data format standard has in recent years seen a significant enhancement across diverse scientific domains. The growth of both the standard and the number of NeXus definition developers makes it all the more important to ensure that the development process is both user-friendly and resilient to errors. The existing representation of NeXus definitions in XML offers structural rigor through the NeXus Definition Language (NXDL) and a well-defined hierarchy for metadata and data types. However, it is verbose and can be difficult to edit by hand. Writing and maintaining NXDL files often involves dealing with deeply nested elements and strict syntax, which can be error-prone and time-consuming—especially for users who are not familiar with XML development. nyaml addresses these challenges by enabling the development of NeXus definitions in a cleaner, YAML-based format while preserving the full structure and semantics of the original XML.


# NYAML to NXDL
# NXDL to NYAML
# Evaluation from NAIC
# Citations

NOTE! The following is example of citation
Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures
Note! The follwoing is example figure
Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

# References

