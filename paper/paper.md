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
# Statement of need
# NYAML to NXDL
# NXDL to NYAML
# Evaluation from NAIC

The NeXus International Advisory Committee (NIAC) is the governing body responsible for overseeing the development and maintenance of the NeXus data standard. A core responsibility of the NIAC is the stewardship of the NeXus Definition Language (NXDL), the XML-based schema that defines the hierarchical structure and semantics of NeXus data files [1]. As part of its mission to facilitate the standardization of NeXus definitions in NXDL, NIAC has recently reviewed and formally accepted \verb|nyaml|. Simplified editing, improved clarity, and reduced error rates in the standard proposals produced by both new contributors and experienced developers were the decisive benefits that guided this decision. Following a successful evaluation, NIAC has approved \verb|nyaml| and endorsed it as the recommended tool for preparing NeXus definition proposals. In support of this decision, the official NeXus definition repository was updated to integrate \verb|nyaml| into its workflow through the addition of two makefile targets: 'make nyaml', which converts existing definitions from the canonical nxdl.xml format into .nyaml, and 'make nxdl', which detects modified or newly added .nyaml files and converts them back into valid nxdl.xml format for submission and version control. This integration ensures that contributions made in .nyaml are compatible with the existing XML-based infrastructure. The adoption of \verb|nyaml| by NIAC reflects an ongoing commitment to fostering community engagement and modernising the technical tools underpinning the NeXus standard [2].

References:

[1] Könnecke, M., et al. (2015). The NeXus data format. Journal of Applied Crystallography, 48(1), 301–305. https://doi.org/10.1107/S1600576714027575
[2] NIAC and NeXus Documentation. https://www.nexusformat.org

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

