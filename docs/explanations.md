# Motivation

The NeXus data format, described by the NeXus Definition Language (NXDL), represents a concerted effort aimed at facilitating data exchange within scientific communities, particularly among those engaged in neutron, X-ray, and muon research [J. Appl. Cryst. (2015). 48, 301-305](https://doi.org/10.1107/S1600576714027575). The data format is also being used by the material science community under the project [NeXus-FAIRmat](https://fairmat-nfdi.github.io/nexus_definitions/) supporting FAIR (Findable, Accessible, Interoperable and Reuseable) data principle. It serves as a standardized framework for both data exchange and storage. At its core, the NeXus Definition Language (NXDL) functions as the cornerstone through which scientists delineate the nomenclature and organizational structure of information within NeXus data files, tailored to specific scientific techniques.

NXDL is used to define general data storage objects (base classes) and the base classes are the building blocks for defining measurement-specific or even instrument-specific or software-specific data storage objects (application definitions). In this process, members and definitions of individual base classes can be used as is or customized. In essence, the process of schema development, whether for a base class or an application definition, entails crafting an NXDL schema definition file with the extension 'nxdl.xml', utilizing the Extensible Markup Language, [XML](https://www.w3.org/TR/REC-xml/REC-xml-20081126.xml) .

To expedite the schema development process, we have introduced the use of Yet Another Markup Language ([YAML](https://yaml.org/)), which provides a syntax or style specifically tailored for defining scientific domain-driven schemas with NXDL. One significant advantage of YAML over XML is its indentation-driven approach, which eliminates the need for starting and ending tags for each entity within the schema. The `YAML` format results in a reduction of NXDL keyword repetition and allows for a intuitive grasp with object oriented programing domain, such as class inheritance. These benefits are attained without compromising the integrity of the original NeXus schema, which is traditionally expressed in XML format.

The `YAML` format, while not yet an official version of NeXus application definitions or base classes, necessitates a method for transcoding it into `XML`. The [nyaml](https://github.com/FAIRmat-NFDI/nyaml/tree/main) Python package serves as a converter tool designed specifically for this purpose. It enables the conversion of NXDL from `YAML` format to `XML`, thereby enhancing the capability of NeXus schema developers to incorporate domain-specific scientific knowledge into the schema. Furthermore, the tool offers the flexibility to extend existing NeXus schemas in XML by facilitating conversion back and forth between the two formats. It is important to note that here we do not introduce NeXus data objects, terms, or types, which are fundamental for writing base class schemas or application definition schemas. For individuals new to NeXus, we refer to the official NeXus site at NeXus [official site](https://www.nexusformat.org/).

## nyaml Workflow

Like every scientific software, the `nyaml` tool also follows a specific workflow.

```mermaid
graph TD;
  subgraph Start
    id1["Input File (YAML or XML)"]
  end
  subgraph Correct File Converter
    id2["YAML Converter"]
    id3["XML Converter"]
  end
  subgraph YAML converter
    id4["Comment Collector"]
    id5["Python Dictionary Object"]
  end
  subgraph XML converter
    id6["XML Object"]
  end
  subgraph Final result
  id7["Write XML File"]
  id8["Write YAML File"]
  end

  id1--> |YAML File|id2
  id1--> |XML File|id3
  id2-->id4
  id4-->id5
  id3-->id6
  id5-->id7
  id6-->id8
```

For a given input file, the `nyaml` converter checks for the correct file type and call appropriate converter. For an XML file, the XML converter parses the `XML` file, by means of [lxml](https://lxml.de/) python library, into an `XML` tree object. Adhering to the NXDL rules, the converter writes the application definition or the base class object to a `yaml` file that matches the `nyaml` syntax. If the input file is a `yaml` file, the `yaml` converter collects the comments in a `Comments` object and parses the `yaml` file into a python `dictionary` object. Later, the application definition or base classes will be converted into an `XML` file by combining the `Comments` and the python `dictionary` object.

## Conversion from YAML to XML
Presented below is a concise and trimmed example of the `NXmpes` application definition (not a full application definition) in `YAML` format, alongside its corresponding translation into `XML` format, as illustrated below. Subsequently, the fundamental rules governing this conversion process are elucidated. For a comprehensive understanding of the basic structure of NXDL, readers are encouraged to explore the [NeXus Manual](https://manual.nexusformat.org/user_manual.html). Throughout the following discussions, various components of the NXmpes application definition will be discussed in the light of `nyaml` converter.

**NXmpes application definition in YAML format**
```yaml
category: application
type: group
doc: |
  This is the most general application definition for multidimensional photoelectron spectroscopy.

  .. _ISO 18115-1:2023: https://www.iso.org/standard/74811.html
  .. _IUPAC Recommendations 2020: https://doi.org/10.1515/pac-2019-0404
symbols:
  doc: |
    The symbols used in the schema to specify e.g. dimensions of arrays
  n_transmission_function: |
    Number of data points in the transmission function.
NXmpes(NXobject):
  (NXentry):
    exsits: required
    definition:
      \@version:
      enumeration: [NXmpes]
    title:
    start_time(NX_DATE_TIME):
      doc: |
        Datetime of the start of the measurement.
    end_time(NX_DATE_TIME):
      exists: recommended
      doc: |
        Datetime of the end of the measurement.
    (NXinstrument):
      doc:
      - |
        Description of the MPES spectrometer and its individual parts.
      - |
        xref:
          spec: ISO 18115-1:2023
          term: 12.58
          url: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.58
      source_TYPE(NXsource):
        exists: recommended
        doc: |
          A source used to generate a beam.
      (NXmanipulator):
        exists: optional
        doc: |
          Manipulator for positioning of the sample.
        value_log(NXlog):
          exists: optional
          value(NX_NUMBER):
            unit: NX_PRESSURE
            doc: |
              In the case of an experiment in which the gas pressure changes and is recorded,
              this is an array of length m of gas pressures.
    (NXprocess):
      exists: recommended
      doc: |
        Document an event of data processing, reconstruction, or analysis for this data.
      transmission_correction(NXcalibration):
        exists: optional
        doc: |
          This calibration procedure is used to account for the different tranmsission efficiencies.
        transmission_function(NXdata):
          exists: recommended
          doc: |
            Transmission function of the electron analyser.
          \@axes:
            enumeration: [kinetic_energy]
          kinetic_energy(NX_FLOAT):
            unit: NX_ENERGY
            doc: |
              Kinetic energy values
            dimensions:
              rank: 1
              dim: [[1, n_transmission_function]]
```

**NXmpes application definition in nxdl.xml format**
```xml
  <?xml version='1.0' encoding='UTF-8'?>
  <?xml-stylesheet type="text/xsl" href="nxdlformat.xsl"?>
  <definition xmlns="http://definition.nexusformat.org/nxdl/3.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" category="application" type="group" name="NXmpes" extends="NXobject" xsi:schemaLocation="http://definition.nexusformat.org/nxdl/3.1 ../nxdl.xsd">
      <symbols>
          <doc>
              The symbols used in the schema to specify e.g. dimensions of arrays
          </doc>
          <symbol name="n_transmission_function">
              <doc>
                  Number of data points in the transmission function.
              </doc>
          </symbol>
      </symbols>
      <doc>
          This is the most general application definition for multidimensional
          photoelectron spectroscopy.

          .. _ISO 18115-1:2023: https://www.iso.org/standard/74811.html
          .. _IUPAC Recommendations 2020: https://doi.org/10.1515/pac-2019-0404
      </doc>
      <group type="NXentry">
          <field name="definition">
              <attribute name="version"/>
              <enumeration>
                  <item value="NXmpes"/>
              </enumeration>
          </field>
          <field name="title"/>
          <field name="start_time" type="NX_DATE_TIME">
              <doc>
                  Datetime of the start of the measurement.
              </doc>
          </field>
          <field name="end_time" type="NX_DATE_TIME" recommended="true">
              <doc>
                  Datetime of the end of the measurement.
              </doc>
          </field>
          <group type="NXinstrument">
              <doc>
                  Description of the MPES spectrometer and its individual parts.

                  This concept is related to term `12.58`_ of the ISO 18115-1:2023 standard.

                  .. _12.58: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.58
              </doc>
              <group name="source_TYPE" type="NXsource" recommended="true">
                  <doc>
                      A source used to generate a beam.
                  </doc>
              </group>
              <group type="NXmanipulator" optional="true">
                  <doc>
                      Manipulator for positioning of the sample.
                  </doc>
                  <group name="value_log" type="NXlog" optional="true">
                      <field name="value" type="NX_NUMBER" units="NX_PRESSURE">
                          <doc>
                              In the case of an experiment in which the gas pressure changes and is recorded,
                              this is an array of length m of gas pressures.
                          </doc>
                      </field>
                  </group>
              </group>
          </group>
          <group type="NXprocess" recommended="true">
              <doc>
                  Document an event of data processing, reconstruction, or analysis for this data.
              </doc>
              <group name="transmission_correction" type="NXcalibration" optional="true">
                  <doc>
                      This calibration procedure is used to account for the different tranmsission
                      efficiencies.
                  </doc>
                  <group name="transmission_function" type="NXdata" recommended="true">
                      <doc>
                          Transmission function of the electron analyser.
                      </doc>
                      <attribute name="axes">
                          <enumeration>
                              <item value="kinetic_energy"/>
                          </enumeration>
                      </attribute>
                      <field name="kinetic_energy" type="NX_FLOAT" units="NX_ENERGY">
                          <doc>
                              Kinetic energy values
                          </doc>
                          <dimensions rank="1">
                              <dim index="1" value="n_transmission_function"/>
                          </dimensions>
                      </field>
                  </group>
              </group>
          </group>
      </group>
  </definition>
```
