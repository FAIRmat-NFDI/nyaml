# Tutorials
This explanatory tutorial will explain different keywords, terms, and rules from the perspective of YAML format of the NeXus schema. Therefore it provides a overall grasp on how to write a NeXus schema those syntactical components.

## Design of NeXus Ontology and Terms in YAML

Within the YAML format, the root section denotes the top-level description of the application definition or base class schema, comprising the `category`, `type`, `doc`, `symbols` block, and the name of the schema (e.g. `NXmpes(NXobject)`). Correspondingly, the root section refers to the XML element `definition`, encompassing the first `doc` child of the `definition` and `symbols`. The definition element encapsulates essential XML attributes such as the schema's `name` (and xml attribute), the object it `extends` (an xml attribute), and the schema `type` (an xml attribute), with additional XML attributes (e.i. `xmlns:xsi`) handled by the nyaml converter. The accurate designation of category as either `base` or `application` distinguishes between an `application definition` and a `base class`. The schema name (e.i. `NXmpes(NXobject)`) with paranthesis indicates the extension of the current application definition, noting that base classes must `extends` NXobject, whereas application definitions may `extends` either `NXobject` or another `application definition` (excluding base classes). Schemas may incorporate one or multiple symbols, each imbued with specialized physical meanings beyond their literal interpretation, which are utilised over the application definition.
Within the YAML format, the root section denotes the top-level description of the application definition or base class schema, comprising the `category`, `type`, `doc`, `symbols` block, and the name of the schema (e.g. `NXmpes(NXobject)`). Correspondingly, the root section refers to the XML element `definition`, encompassing the first `doc` child of the `definition` and `symbols`. The definition element encapsulates essential xml attributes such as the schema's `name` (and xml attribute), the object it `extends` (an xml attribute), and the schema `type` (an xml attribute), with additional XML attributes (e.i. `xmlns:xsi`) handled by the nyaml converter. The accurate designation of category as either `base` or `application` distinguishes between an `application definition` and a `base class`. The schema name (e.i. `NXmpes(NXobject)`) with paranthesis indicates the extension of the current application definition, noting that base classes must `extends` NXobject, whereas application definitions may `extends` either `NXobject` or another `application definition` (excluding base classes). Schemas may incorporate one or multiple symbols, each imbued with specialized physical meanings beyond their literal interpretation, which are utilised over the application definition.

**A typical root section for the application definition `NXmpes` outlined**

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
```

### NeXus Group
[NeXus groups](https://manual.nexusformat.org/design.html#design-groups), as instances of NeXus base classes, embody the compositional structure of application definitions. Depending on the value of keyword `nameType`, these groups can be initialized dynamically or statically, each approach offering distinct advantages. The keyword `nameType` can hold three district values: `specified`, `any`, and `partial` (for details see the table in `nameType` keyword).

Dynamic initialization allows the instantiation of groups while implementing the NeXus definition to store data (in HDF5 file format called NeXus file). This method provides flexibility for multiple instances at the same level within the NeXus file. For instance, the group `(NXmanipulator)` (with `nameType`=`any`) can initialize multiple groups such as `manipulator1` and `manipulator2` of the base class `NXmanipulator` during data writing.

Descriptive information about NeXus groups is encapsulated within the `doc` child of the respective group. It is important to note that the group annotation of `source_TYPE(NXsource)` or `(NXsource)source_TYPE` signifies the encapsulation of the group's `name` as `source_TYPE` and its type as `NXsource` base class. Notably, the order between `name` and `type` within the XML element will be inverted for two different syntaxs.

Furthermore, for `nameType`=`partial`, the uppercase part of the group's name can be dynamically overwritten, allowing for the instantiation of multiple instances. For example, `source_electric` and `source_magnetic` can coexist from `NXsource`. The same upper case rules for multiple instances are also applicable for NeXus fields and attributes.

**NeXus Groups in YAML format**
```yaml
# NeXus groups in YAML format
source_TYPE(NXsource):
  exists: recommended
  nameType: partial
  doc: |
    A source used to generate a beam.
(NXmanipulator):
  exists: optional
  nameType: any # default
  doc: |
    Manipulator for positioning of the sample.
  value_log(NXlog):
    exists: optional
```

### NeXus Field and NeXus Attribute
A NeXus group may contain NeXus fields, NeXus attributes, and NeXus groups. A field, that does not have preceding `NX`, and a attribute, preceded by `\@`, must have a [NeXus type](https://manual.nexusformat.org/nxdl-types.html#index-0) (e.g.`NX_FLOAT`, `NX_CHAR`). In the YAML notation, each NeXus field or attribute has a implicit type `NX_CHAR`; otherwise its type must be denoted inside the parenthesis (e.g. `end_time(NX_DATE_TIME)`). Other XML attributes of the NeXus `field` and NeXus `attribute` comes as children of the field and attribute defined by special keyword (the special keywords will be discussed on next section). The explanatory text of the NeXus fields or attributes goes under `doc` child.

A NeXus group may encompass multiple `field`, `attribute`, and subgroup, each serving distinct purposes within the data structure. The [`field`](https://manual.nexusformat.org/design.html#design-fields), denoted without the prefix NX, and the [`attribute`](https://manual.nexusformat.org/design.html#design-attributes), indicated by `\@`, must be associated with a NeXus type (e.g., `NX_FLOAT`, `NX_CHAR`). In YAML format, each field or attribute (NeXus attribute) implicitly assumes the type `NX_CHAR`, unless explicitly specified within parentheses (e.g., `end_time(NX_DATE_TIME)`).

Additionally, `XML` attributes specific to NeXus field and attribute are represented as children of the corresponding `field` or `attribute` elements (further details on special keywords will be discussed in the following section). Descriptive information pertaining to NeXus `field`s or `attribute`s is encapsulated within the `doc` child element.

**NeXus field and attribute in YAML format**
```yaml
(NXentry):
  exsits: required
  definition:  # Field type: NX_CHAR
    \@version:  # Attribute type: NX_CHAR
    enumeration: [NXmpes]
  title:
  start_time(NX_DATE_TIME):  # Field type: NX_DATE_TIME
    doc: Datetime of the start of the measurement.
  end_time(NX_DATE_TIME):  # Field type: NX_DATE_TIME
    exists: recommended
    doc: Datetime of the end of the measurement.
```

### NeXus Link
The NeXus `link` concept reduces duplication of the data since several concepts of the same kind (e.g., NeXus field or NeXus attribute) can refer to a single copy of a data element. In YAML format, NeXus `link` is defined denoting the link in side parenthesis. At the same time, the concept containing the data must be mentioned under the `target` child.


**NeXus link in YAML format**
```yaml
reference_measurement(link):
  target: /entry
  doc: A link to a full data collection.
```

In the above YAML example, `reference_measurement` is defined as a link refering the `NXentry` group with its target specified as `/entry`. This structure ensures that the concept referencing the data is effectively linked to the designated target, thereby reducing redundancy and maintaining data integrity within the NeXus framework.

<!-- ### NeXus Choice
NeXus `choice` concept is designed to choose a concept from a number of concepts of the same kind (e.g., a NeXus field). The `choice` options allows for defining a scientific concept in several modes for different situations (e.g., for different instrument configurations or measurement modes).

**NeXus choice in YAML format**
__Not implemented in the `nyaml` tool! Coming soon__

```yaml
pixel_shape(choice):
  (NXoff_geometry):
    doc: Shape description of each pixel. Use only if all pixels in the detector
      are of uniform shape.
  (NXcylindrical_geometry):
    doc: Shape description of each pixel. Use only if all pixels in the detector
      are of uniform shape and require being described by cylinders.
```

In this `choice` example, `pixel_shape` could be any of the groups `(NXoff_geometry)` and `(NXcylindrical_geometry)`, depending on the geometry of the pixels. -->

## Special Keywords in YAML
To explain the context of NeXus, certain keywords hold significance beyond their literal interpretations. These special keywords are utilized to elucidate and denote various NeXus terms like attributes, fields, links, and groups, thereby enhancing the clarity and specificity of the data representation.

### Keyword `exists`
The `exists` keyword plays a pivotal role in delineating the optionality of NeXus concepts `attribute`, `field`, `choice` `link`, and `group`, during the implementation of NeXus definitions in NeXus files. It provides crucial insights into the expected presence or absence of these concepts within the NeXus data structure. By default, all the concepts of a base class are optional, while in an application definition, all concepts are required.

Currently, the accepted values for the `exists` keyword encompass:

`optional`: Denotes that the NeXus concept is not mandatory and may be absent.
`recommended`: Suggests that the NeXus concept is advisable, but not mandatory.
`required`: Indicates that the NeXus concept must be present within the structure. Any validation of a NeXus file will fail or give warning if required concepts (for a given application definition) are not available.
`[min, <number>, max, <number> or infty]`: Represents an array type value that signifies the multiplicity of the NeXus concepts. For instance, a concept having the keyword `exists: [min, 3, max, infty]` implies that this concept must come with a minimum of three instances and may extend to any number of instances.

**`exists` in YAML**

```yaml
transmission_correction(NXcalibration):
  exists: optional
  doc: |
    This calibration procedure is used to account for the different tranmsission efficiencies.
```
In the above example the greoup `transmission_correction` is a optional group.

### Keyword `unit`
A statement introducing NeXus-compliant NXDL `units` attribute to the `field`, e.g. `NX_VOLTAGE` to assign a predefined physical unit.

**`unit` in YAML**

```yaml
detector_voltage(NX_FLOAT):
  unit: NX_VOLTAGE
  doc: |
    Voltage applied to detector.
```

### Keyword `dimensions`
The `dimensions` term  describes the multidimensional nature of the data, specifying its rank, dimensional indices, and corresponding length of the rank. For example, the attribute `rank` defines the dimension of the data set. To elucidate each dimension, we use two other keywords: `dim` and `dim_parameters`. The `dim` keyword comprises an array of arrays, the nested array encapsulates values for `index` and `value` (NeXus keywords) pairs. Each array within the `dim` array corresponds to a specific dimension of the multidimensional data. For example, for 2D particle motion, the `dim` array may be represented as `[[0, nx], [1, ny]]`, each member indicating the axis index and axis name. The keyword `dim_parameters` contains further information of each dimension such as `doc`, `ref`, etc. It is important to note that each term or keyword within `dim_parameters` must have the same length as the value of the rank keyword.

**`dimensions` in YAML**
```yaml
# 2D particle motion
dimensions:
   rank: 2
   dim: [[0, nx], [1, ny]]
   dim_parameters:
      doc: ["Position of particle on x-axis.","Position of particle on y-axis."]
```
The `dimensions` can also be written in shorter form
**Dimensions in YAML (shorter form)**
```yaml
# 2D particle motion
dimensions:
   rank: 2
   dim: (nx, ny)
```

### Keyword `enumeration`
List of strings which are considered as a set of predefined values for fields or attributes.

**Enumeration in YAML**
```yaml
definition:
  \@version:
In the example, the only valid value for NeXus field `definition` is `NXmpes`.
```
In the example, the only valid value for NeXus field `definition` is `NXmpes`.
The `xref` keyword (which can only be used inside the keyword `doc`) is used to refer any other ontology or any other standard such `ISO`. The `xref` in the example `doc` will reflect the information inside the XML `doc`. Note that the `xref` keyword is only available in the `YAML` representation and will be transformed into its textual representation inside the `doc` text in `XML`.
### Keyword `xref`
The `xref` keyword (which can only be used inside the keyword `doc`) is used to refer any other ontology or any other standard (such as `ISO`). The `xref` in the example `doc` will reflect the information inside the XML `doc`. Note that the `xref` keyword is only available in the `YAML` representation and will be transformed into its textual representation inside the `doc` text in `XML`.

**`xref` in YAML**
```yaml
(NXinstrument):
  doc:
  - |
    Description of the MPES spectrometer and its individual parts.
  - |
    xref:
      spec: ISO 18115-1:2023
      term: 12.58
      url: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.58
```

### Keyword `nameType`
To initialize a NeXus `group`, `field` or `attribute` the keyword `nameType` carries very significant information on the initialized name depending on all characters upper case, lower case or combination of upper-lower case.


|      `nameType`     |        `specified`         |             `any`            |          `partial`          |   default value       |
|---------------------|----------------------------|------------------------------|-----------------------------|-----------------------|
| All Upper Case      | &#10003;                   |   &#10003;                   | &#10003; (with warning msg) | `specified`           |
| All Lower Case      | &#10003;                   |   &#10003; (with warning msg)| &#10003; (with error);      | `specified`           |
| Upper and Lower Case| &#10003;                   |   &#10003; (with warning msg)| &#10003;                    | `specified`           |
| Anonymous Group Name| &#10003; (with error)      |   &#10003;                   | &#10003; (with error)       | `any`                 |

