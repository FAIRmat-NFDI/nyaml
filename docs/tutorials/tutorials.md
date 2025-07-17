# Tutorials for NXDL in YAML format
This tutorial will explain different keywords, terms, and rules from the perspective of YAML format of the NeXus schema. It provides a overall grasp on how to write a NeXus schema (base classes and application definitions) in YAML format using those syntactical components.

!!! note
    We do not support the NeXus `choice` concept in the `nyaml` tool yet.

## Design of NeXus Semantics and Terms in YAML

Within the YAML format, the root section denotes the top-level description of the application definition or base class schema, comprising the `category`, `type`, `doc`, `symbols` block, and the name of the schema (e.g. `NXmpes(NXobject)`). Correspondingly, the root section refers to the XML element `definition`, encompassing the first `doc` child of the `definition` and `symbols`. The definition element encapsulates essential XML attributes such as the schema's `name` (an xml attribute), the object it `extends` (an xml attribute), and the schema `type` (an xml attribute), with additional XML attributes (e.g. `xmlns:xsi`) handled by the nyaml converter. The accurate designation of category as either `base` or `application` distinguishes between a `base class` and an `application definition` respectively. The schema name (e.g. `NXmpes(NXobject)`) with parenthesis indicates the extension of the current application definition `NXmpes` from base class `NXobject`, an application definition may extend either `NXobject` or other application definitions. Schemas may incorporate one or multiple symbols, each imbued with specialized physical meanings beyond their literal interpretation, which are utilized over the application definition.

**A typical root section for the application definition `NXmpes` outlined**

=== "YAML"
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

=== "XML"

    ```xml
    <definition xmlns="http://definition.nexusformat.org/nxdl/3.1"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                category="application"
                type="group"
                name="NXmpes"
                extends="NXobject"
                xsi:schemaLocation="http://definition.nexusformat.org/nxdl/3.1 ../nxdl.xsd">
      <doc>
        This is the most general application definition for multidimensional photoelectron spectroscopy.
        .. _ISO 18115-1:2023: https://www.iso.org/standard/74811.html
        .. _IUPAC Recommendations 2020: https://doi.org/10.1515/pac-2019-0404
      </doc>
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
    </definition>
    ```
### NeXus Group, Field, Attribute, and Link
#### NeXus Group
[NeXus groups](https://manual.nexusformat.org/design.html#design-groups), as instances of NeXus base classes, embody the compositional structure of application definitions. Depending on the value of keyword `nameType`, these groups can be initialized dynamically or statically and each approach offers distinct advantages. The keyword `nameType` can hold one of the three district values: `specified`, `any`, and `partial` (for details see the table in `nameType` keyword).

Dynamic initialization allows the instantiation of groups while implementing the NeXus definition to store data (in HDF5 file format called NeXus file). This method provides flexibility for multiple instances at the same level within the NeXus file. For instance, the `group` `(NXmanipulator)` (with `nameType`=`any`) can initialize multiple groups such as `manipulator1` and `manipulator2` initializing base class `NXmanipulator` during data writing.

Descriptive information about NeXus groups is encapsulated within the `doc` child of the respective `group`. It is important to note that the `group` annotation of `source_TYPE(NXsource)` signifies the encapsulation of the `group`'s `name` as `source_TYPE` and its `type` as `NXsource` base class.

Furthermore, for `nameType`=`partial` (see keyword `nameType`), the uppercase part of the `group`'s name can be dynamically overwritten, allowing for instantiation of multiple instances. For example, `source_electric` and `source_magnetic` can coexist under the same parent `group`. The same upper case rules for multiple instances are also applicable for NeXus `field`s and `attribute`s.

**NeXus Groups in YAML and XMLformat**

=== "YAML"
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

=== "XML"
    ```xml
    <group name="source_TYPE" type="NXsource" recommended="true" nameType="partial">
      <doc>
        A source used to generate a beam.
      </doc>
    </group>
    <!-- If not nameType is specified default NXmanipulator has nameType any -->
    <group type="NXmanipulator" optional="true" nameType="any">
      <doc>
        Manipulator for positioning of the sample.
      </doc>
      <group name="value_log" type="NXlog" optional="true"/>
    </group>
    ```
#### NeXus Field and Attribute
A NeXus `group` may contain NeXus `field`s, NeXus `attribute`s, and other NeXus `group`s. A `field`, representing an instance of NXDL/XSD fieldType, is written as a string without a preceding `NX`, and an `attribute`, preceded by `\@`, must have a [NeXus type](https://manual.nexusformat.org/nxdl-types.html#index-0) (e.g.`NX_FLOAT`, `NX_CHAR`). The NeXus type type must be denoted inside parenthesis (e.g. `end_time(NX_DATE_TIME)`); if the type is omitted, the NeXus `field` or `attribute` has an implicit type `NX_CHAR` by default. Other XML attributes or properties of the NeXus `field`/`attribute`/`group`/`doc` can be defined using one of the special keywords (see `Special Keywords in YAML` below). The descriptive text for NeXus `field`/`attribute`/`group`/`link` is given within the `doc` child.

**NeXus field and attribute in YAML and XML format**

=== "YAML"
    ```yaml
    (NXentry):
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
=== "XML"
    ```xml
    <group type="NXentry">
      <field name="definition" type="NX_CHAR">
        <attribute name="\@version"/>
        <enumeration>
          <item value="NXmpes"/>
        </enumeration>
      </field>
      <field name="title"/>
      <field name="start_time" type="NX_DATE_TIME">
        <doc>Datetime of the start of the measurement.</doc>
      </field>
      <field name="end_time" type="NX_DATE_TIME" recommended="true">
        <doc>Datetime of the end of the measurement.</doc>
      </field>
    </group>
    ```

#### NeXus Link
The NeXus `link` reduces data duplication since several concepts of the same kind (e.g., NeXus `group`, `field`, or `attribute`) can refer to a single copy of a data element. In YAML format, NeXus `link` is denoted by the `link` keyword inside parenthesis. At the same time, the target concept containing the data must be mentioned under the `target` child.



**NeXus link in YAML and XML format**

=== "YAML"
    ```yaml
    reference_measurement(link):
      target: /entry
      doc: A link to a full data collection.
    ```
=== "XML"
    ```xml
    <link type="NXentry" target="/entry">
      <doc>A link to a full data collection.</doc>
    </link>
    ```

In the YAML example above, `reference_measurement` is defined as a link referring to an instance of the `NXentry` group with its `target` attribute denoting a value `/entry`. This structure ensures that the concept referencing the data is effectively linked to the designated target, thereby reducing the redundancy and maintaining data integrity within the NeXus framework.


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

### Special Keywords in YAML

In the YAML schema, certain keywords hold self significance beyond their literal representational meanings. These special keywords are utilized to elucidate and denote various NeXus terms like `attribute`s, and `group`s, thereby improves the clarity and specificity of the data representation.

#### Keyword `nameType`
To initialize a NeXus concepts, e.g., `group`, `field`, the keyword `nameType` carries significant information on the initialized name depending whether all characters are upper case, lower case or combination of upper-lower case.


|      `nameType`     |        `specified`         |             `any`            |          `partial`          |   default value       |
|---------------------|----------------------------|------------------------------|-----------------------------|-----------------------|
| All Upper Case      | &#10003;                   |   &#10003;                   | &#10003; (with warning msg) | `specified`           |
| All Lower Case      | &#10003;                   |   &#10003; (with warning msg)| &#10003; (with error);      | `specified`           |
| Upper and Lower Case| &#10003;                   |   &#10003; (with warning msg)| &#10003;                    | `specified`           |
| Anonymous Group Name| &#10003; (with error)      |   &#10003;                   | &#10003; (with error)       | `any`                 |

**`nameType` keyword in YAML**

=== "YAML"
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

=== "XML"
    ```xml
    <group name="source_TYPE" type="NXsource" recommended="true" nameType="partial">
      <doc>
        A source used to generate a beam.
      </doc>
    </group>
    <!-- If no nameType is specified, by default NXmanipulator has nameType any -->
    <group type="NXmanipulator" optional="true" nameType="any">
      <doc>
        Manipulator for positioning of the sample.
      </doc>
      <group name="value_log" type="NXlog" optional="true"/>
    </group>
    ```

#### Keyword `exists`

The `exists` keyword plays a pivotal role in defining the optionality of NeXus concepts. e.g., `group`, `field`. It provides crucial insights for the expected presence or absence of these concepts within the NeXus data structure when implementing the NeXus definitions in NeXus files. By default, all the concepts of a base class are optional, while in an application definition, all concepts are required.


Currently, the accepted values for the `exists` keyword encompass:
`required`: Indicates that the NeXus concept must be present within the structure. Any validation of a NeXus file will fail or give a warning if required concepts (for a given application definition) are not available.

`recommended`: Suggests that the NeXus concept is advised, but not mandatory.
`optional`: Denotes that the NeXus concept is not mandatory and may be absent.

`[min, <number>, max, <number> or infty]`: Represents an array type value that signifies the multiplicity of the NeXus concepts. For instance, a concept having the keyword `exists: [min, 3, max, infty]` implies that this concept must come with a minimum of three instances and may extend to any number of instances.

**`exists` in YAML**

=== "YAML"
    ```yaml
    transmission_correction(NXcalibration):
      exists: optional
      doc: |
        This calibration procedure is used to account for the different transmission efficiencies.
      calibrationDATA(NXdata):
        exists: [min, 3, max, infty]
    ```
=== "XML"
    ```xml
    <group type="NXcalibration" optional="true">
      <doc>
        This calibration procedure is used to account for the different transmission efficiencies.
      </doc>
      <group name="calibrationDATA" type="NXdata" minOccurrences="3" maxOccurrences="unbounded"/>
    </group>
    ```

In the above example the group `transmission_correction` is an optional group.

#### Keyword `unit`
The `unit` keyword is used to define the NeXus-compliant unit categories.

**`unit` in YAML**

=== "YAML"
    ```yaml
    detector_voltage(NX_FLOAT):
      unit: NX_VOLTAGE
      doc: |
        Voltage applied to detector.
    ```
=== "XML"
    ```xml
    <field name="detector_voltage" type="NX_FLOAT" units="NX_VOLTAGE"/>
      <doc>Voltage applied to detector.</doc>
    </field>
    ```
In the above example, the `detector_voltage` field is defined as a `NX_FLOAT` type with a unit of `NX_VOLTAGE`, indicating that the values stored in this field are measured in volts or millivolts or other voltage units.

#### Keyword `dimensions`

The `dimensions` term  describes the multidimensional nature of the data, specifying its rank, dimensional indices, and corresponding length of the rank. The attribute `rank` defines the number of physical dimension of the data array. To elucidate each dimension, we use two other keywords: `dim` and `dim_parameters`. The `dim` keyword comprises an array of arrays, the nested array encapsulates values for `index` and `value` (NeXus keywords) pairs. Each array element of the `dim` array corresponds to a specific dimension of the multidimensional data. For example, for 2D particle motion, the `dim` array may be represented as `[[0, nx], [1, ny]]`, each element indicating the axis index and axis name. The keyword `dim_parameters` contains further information of each dimension such as `doc`, `ref`, etc. It is important to note that each array corresponds to a keyword within `dim_parameters` must have the same length as the value of the `rank` keyword.


**`dimensions` in YAML**

=== "YAML"
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
=== "YAML (shorter form)"
    ```yaml
    # 2D particle motion
    dimensions:
      rank: 2
      dim: (nx, ny)
    ```
=== "XML"
    ```xml
    <dimensions rank="2">
      <dim index="0" value="nx">
        <doc>Position of particle on x-axis.</doc>
      </dim>
      <dim index="1" value="ny">
        <doc>Position of particle on y-axis.</doc>
      </dim>
    </dimensions>
    ```
=== "XML (shorter form)"
    ```xml
    <dimensions rank="2">
      <dim index="0" value="nx"/>
      <dim index="1" value="ny"/>
    </dimensions>
    ```

#### Keyword `enumeration`
List of strings which are considered as a set of predefined values for `field`s or `attribute`s. Individual items of the enumeration may also hold a `doc` keyword to provide a description of the item.

**`enumeration` in YAML**

=== "YAML"
    ```yaml
    definition:
      \@version:  # Attribute type: NX_CHAR
        enumeration: [NXmpes]
    ```
=== "XML"
    ```xml
    <field name="definition" >
      <attribute name="version">
        <enumeration>
          <item value="NXmpes"/>
        </enumeration>
      </attribute>
    </field>
    ```

=== "YAML (open enum)"
    ```yaml
    enum_with_open_enum:
        enumeration:
          open_enum: true
          items: [NXmpes]
    ```
=== "XML (open enum)"
    ```xml
    <field name="enum_with_open_enum">
      <enumeration open="true">
        <item value="NXmpes"/>
      </enumeration>
    </field>
    ```
=== "YAML (open enum & vector items)"
    ```yaml
    enum_with_open_and_vector_items:
      enumeration:
        open_enum: true
        '[0, 1, 0]':
          doc: |
            This is an open enumeration with values 0, 1, and 0.
        '[0, 1, 1]':
          doc: |
            This is an open enumeration with values 0, 1, and 1.
    ```
=== "XML (open enum & vector items)"
    ```xml
    <field name="enum_with_open_and_vector_items">
      <enumeration open="true">
        <item value="[0, 1, 0]">
          <doc>This is an open enumeration with values 0, 1, and 0.</doc>
        </item>
        <item value="[0, 1, 1]">
          <doc>This is an open enumeration with values 0, 1, and 1.</doc>
        </item>
      </enumeration>
    </field>
    ```

`open_enum` defines that along with the listed items other items are also valid while initializing the NeXus object.

#### Keyword `xref`
The `xref` keyword (which can only be used inside the keyword `doc`) is used to refer any other ontology or any other standard (such as `ISO`). The `xref` in the example `doc` will reflect the information inside the XML `doc`. Note that the `xref` keyword is only available in the YAML representation and will be transformed into its textual representation inside the `doc` text in XML.

**`xref` in YAML**

=== "YAML"
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
=== "XML"
    ```xml
    <group type="NXinstrument">
      <doc>
        Description of the MPES spectrometer and its individual parts.

        This concept is related to term `12.58`_ of the ISO 18115-1:2023 standard.

        .. _12.58: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.58

      </doc>
    </group>
    ```
