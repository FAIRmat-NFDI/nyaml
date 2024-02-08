
NeXus Definition Language (NXDL) is the key component through which scientists define the nomenclature and arrangement of information in NeXus data files cite{Konnecke2015}.
NXDL is used to define general data storage objects (base classes) and use them as the building blocks for defining measurement-specific or even instrument-specific data storage objects (application definitions). In this process, members and definitions of individual base classes can be used as is or customized.

Technically, the creation of a base class or application definitions requires the creation of an NXDL schema definition file. NXDL uses a (restricted) set of extensible markup language (XML). 
As XML markup language files \cite{XMLXXXX}, NXDL files contain labeled, categorized, and structurally organized information in plain text format, ensuring both human- and machine-readability. This enables their automated conversion into schema files that can be used, in combination with other NXDL files, to validate NeXus data files.

To accomplish the benefit of using this common data exchange format, scientists need to define the hierarchy of the data elements and their description but also they need to master NXDL formatting. Specific knowledge is required to implement these formatting rules. A joint community of scientists and computer programmers is needed to accomplish this goal. Furthermore, scientists are required to know the design principles of NeXus, e. g., expected defaults type of a NeXus field is assumed to have a NeXus type if no explicitly mentioning of data type is provided cite{manualNeXusformat}.

To reduce these efforts, we implemented yaml2nxdl; a specific parser tool designed as a Python module which is required to create a formatted NXDL XML file from a YAML file with the hierarchical definitions representing the content of the NXDL file. YAML is an abbreviation for Yet Another Markup Language cite{YamlXXXX}, it is a markup language designed for human interaction. The major difference from XML is that newlines and indentation actually mean something. The benefit for users of writing YAML files and convert it with ymlnxdl is reduced typing efforts and eliminated demand to have NXDL specific knowledge. This lowers the entry barrier when writing application definitions.

An example of YAML file and its translation in XML is shown in table below, the key points are hereafter presented, for a more complete description of the basic structure of NXDL please refer to cite{manualNeXusformat}.

```yaml
doc: "Some text."
symbols: 
  doc: "Some text."
  mysym1: "Symbol description"
  mysym2: "Symbol description"
category: application
NXmpes_ARPES:
  NXentry:
    @entry:
      doc: "Some text."
    @default:
    start_time(NX_DATE_TIME):
      doc: "ISO8601 date time."
    definition:
      enumeration: [myenum1, myenum2]
    NXinstrument:
      NXsource:
        doc: "Some text."
        name:
        probe:
          doc: "Some text."
```

```xml
<?xml version="1.0" ?>
<?xml-stylesheet type="text/xsl" href="nxdlformat.xsl"?>
<definition category="application" extends="NXobject" name="NXmpes_ARPES" type="group" xmlns="http:" xmlns:xsi="http:" xsi:schemaLocation="http:">
  <doc>Some text.</doc>
  <symbols>
    <doc>Some text.</doc>
    <symbol name="mysym1">
      <doc>Some text.</doc>
    </symbol>
    <symbol name="mysym2">
      <doc>Some text.</doc>
    </symbol>
  </symbols>
  <group type="NXentry">
    <attribute name="entry">
      <doc>Some text.</doc>
    </attribute>
    <attribute name="default" optional="true"/>
    <field name="start_time" type="NX_DATE_TIME">
      <doc>ISO8601 date time.</doc>
    </field>
    <field name="definition" type="NX_CHAR">
      <enumeration>
        <item value="myenum1"/>
        <item value="myenum2"/>
      </enumeration>
    </field>
    <group type="NXinstrument">
      <group type="NXsource">
        <doc>Some text.</doc>
        <field name="name" type="NX_CHAR"/>
        <field name="probe" type="NX_CHAR">
          <doc>Some text.</doc>
        </field>
      </group>
    </group>
  </group>
</definition>
```

 From transcoding YAML files we need to follow several rules.  
* Named NeXus groups, which are instances of NeXus classes especially base or contributed classes. Creating (NXbeam) is a simple example of a request to define a group named according to NeXus default rules. mybeam1(NXbeam) or mybeam2(NXbeam) are examples how to create multiple named instances at the same hierarchy level.
* Members of groups so-called fields. A simple example of a member is voltage. Here the datatype is implied automatically as the default NeXus NX\_CHAR type.  By contrast, voltage(NX_FLOAT) can be used to instantiate a member of class which should be of NeXus type NX_FLOAT.
* And attributes or either groups or fields. Names of attributes have to be preceeded by \textbackslash@ to mark them as attributes.

**Special keywords**: Several keywords can be used as childs of groups, fields, and attributes to specify the members of these. Groups, fields and attributes are nodes of the XML tree.
* *doc*: A human-readable description/docstring
* *exists* A statement if an entry is more than optional. Options are recommended, required, [min, 1, max, infty] numbers like here 1 can be replaced by uint or infty to indicate no restriction on how frequently the entry can occur inside the NXDL schema at the same hierarchy level.
* *link* Define links between nodes.
* *units* A statement introducing NeXus-compliant NXDL units arguments, like NX_VOLTAGE
* *dimensions* Details which dimensional arrays to expect
* *enumeration* Python list of strings which are considered as recommended entries to choose from.

Yaml2nxdl offers a way to shift between a simple YAML-based schema and a XML-based schema. It is more than a YAML to XML (or XML to YAML) parser, as it is a NeXus-schema-informed parser, able to recognise and process NeXus instances. These can be NeXus application definitions, or classes such as base or contributed classes. 
Users either create NeXus instances by writing a YAML file or a XML file which details a hierarchy of data/metadata elements. 

The forward (YAML -> XML) and backward (XML -> YAML) conversions are implemented.
The workflow of the tool is quite straightforward.

    item[1.] Reads the user-specified NeXus instance, either in YML or XML format.
    item[2.] If input is in YAML, creates an instantiated NXDL schema XML tree by walking the dictionary nest.
   If input is in XML, creates a YML file walking the dictionary nest.
    item[3.] Write the tree into a YAML file or a properly formatted NXDL XML schema file to disk.
    item[4.]  It is also possible to merge different files, e. g. a base class file from NeXus repository \cite{nexusformatDef} and a file (either YAML or XML) containing new user-defined entities that extend the base class. Both YAML and XML file of the extended class are printed.


It can be run directly from command line typing the following:  "python yaml2nxdl.py [OPTIONS]". Several options can be passed as arguments:

--input-file TEXT The path to the input data file to read.
--append TEXT Parse user-defined NeXus file and append to a specified NeXus base class file from official repo. Write the base class name you want to append your file to with no extension.
--verbose Additional std output info is printed to help validation of your files.
--help Show this message and exit.

The following bullet point tips must be checked:

-The NeXus definition language (NXDL) is the key component through which scientists can customize NeXus cite{NexusXXXX}. NXDL is used to define base classes and use these as the building blocks for specifying application definitions. In this process, members and definitions of individual base classes can be used as is or customized.
- Technically, the creation of a base class or application definitions requires the creation of an NXDL schema definition file. NXDL uses a (restricted) set of extensible markup language (XML). Therefore, NXDL files are XML files \cite{XMLXXXX}.
 - The need for having such specifically-formatted files creates barriers for scientists: Namely, not only they need to define the hierarchy of the data elements and their description but also they need to master NXDL formatting. Specific knowledge is required to implement these formatting rules. Furthermore, scientists are required to know expected defaults such as that without mentioning it explicitly the type of a \nexus{} field is assumed \nxchar{}.
- To reduce these efforts, we implemented \ymlnxdl{}; a \python{} module which automates the transcoding of a YAML file (with the hierarchical definitions representing the content of the NXDL file) into the respective and correctly formatted NXDL XML file. YAML is an abbreviation for Yet Another Markup Language \cite{YamlXXXX}.
- The benefit of ymlnxdl{} for users is reduced typing efforts and eliminated demand to have NXDL specific knowledge. This lowers the entry barrier when writing application definitions.
