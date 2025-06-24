# FAIRmat NYAML documentation
The NeXus data format, described by the NeXus Definition Language (NXDL), represents a concerted effort aimed at facilitating data exchange within scientific communities, particularly among those engaged in neutron, X-ray, and muon research [J. Appl. Cryst. (2015). 48, 301-305](https://doi.org/10.1107/S1600576714027575). The data format is also being used by the material science community under the project [NeXus-FAIRmat](https://fairmat-nfdi.github.io/nexus_definitions/) supporting FAIR (Findable, Accessible, Interoperable and Reuseable) data principle. It serves as a standardized framework for both data exchange and storage. At its core, the NeXus Definition Language (NXDL) functions as the cornerstone through which scientists delineate the nomenclature and organizational structure of information within NeXus data files, tailored to specific scientific techniques.

NXDL is used to define general data storage objects (base classes) and the base classes are the building blocks for defining measurement-specific or even instrument-specific or software-specific data storage objects (application definitions). In this process, members and definitions of individual base classes can be used as is or customized. In essence, the process of schema development, whether for a base class or an application definition, entails crafting an NXDL schema definition file with the extension 'nxdl.xml', utilizing the Extensible Markup Language, [XML](https://www.w3.org/TR/REC-xml/REC-xml-20081126.xml).

To expedite the schema development process, we have introduced the use of Yet Another Markup Language ([YAML](https://yaml.org/)), which provides a syntax or style specifically tailored for defining scientific domain-driven schemas with NXDL. One significant advantage of YAML over XML is its indentation-driven approach, which eliminates the need for starting and ending tags for each entity within the schema. The `YAML` format results in a reduction of NXDL keyword repetition and allows for a intuitive grasp with object oriented programing domain, such as class inheritance. These benefits are attained without compromising the integrity of the original NeXus schema, which is traditionally expressed in XML format.

The `YAML` format, while not yet an official version of NeXus application definitions or base classes, necessitates a method for transcoding it into `XML`. The [nyaml](https://github.com/FAIRmat-NFDI/nyaml/tree/main) Python package serves as a converter tool designed specifically for this purpose. It enables the conversion of NXDL from `YAML` format to `XML`, thereby enhancing the capability of NeXus schema developers to incorporate domain-specific scientific knowledge into the schema. Furthermore, the tool offers the flexibility to extend existing NeXus schemas in XML by facilitating conversion back and forth between the two formats. It is important to note that here we do not introduce NeXus data objects, terms, or types, which are fundamental for writing base class schemas or application definition schemas. For individuals new to NeXus, we refer to the official NeXus site at NeXus [official site](https://www.nexusformat.org/).

<div markdown="block" class="home-grid">
<div markdown="block">

### Tutorial

Tutorials to write different parts and a full NeXus application or base class

- [Tutorials for writing NeXus definition in YAML](tutorials.md)

</div>
<div markdown="block">

### How-to guides

How-to install and use the nyaml tool

- [How-to guide for NYAML tools](how_to_guide.md)

</div>

<div markdown="block">

### Learn

An introduction to NeXus and its design principles.

- [An introduction to NeXus](https://manual.nexusformat.org/index.html)
- [Explanation of the nyaml tool](explanations.md)


</div>
<div markdown="block">
### Reference
Relavent references that supported to develop this tool:
- [NYAML GitHub repository](https://github.com/FAIRmat-NFDI/nyaml)
- [FAIRmat-NeXus website](https://fairmat-experimental.github.io/nexus-fairmat-proposal/)
- [FAIRmat-NeXus GitHub repository](https://github.com/FAIRmat-NFDI/nexus_definitions)
- [Official werbsite for NeXus](https://manual.nexusformat.org/index.html)

- [NYAML developed under project FAIRmat-NFDI](https://github.com/FAIRmat-NFDI)
- [National Research Data Infrastructure (NFDI) funded FAIRmat-NFDI](https://www.nfdi.de/?lang=en)
</div>
</div>
