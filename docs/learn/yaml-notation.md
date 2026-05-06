# nyaml notation reference

This page is the detailed reference for writing NeXus definitions in YAML using `nyaml`. It documents all building blocks and special keywords, with YAML and NXDL XML comparisons for each.

For a step-by-step introduction that teaches these concepts progressively through an example, see [Tutorials > Writing a NeXus definition in YAML](../tutorials/writing-a-yaml-definition.md).

!!! note
    The NeXus `choice` concept is not yet supported in `nyaml`.

---

## Root section

The root section is the top-level block of a definition. It maps to the XML `<definition>` element and contains the following keys:

- `\category`: `application` for application definitions, `base` for base classes
- `\type`: always `group`
- `\doc`: free-text description of the definition
- `\symbols`: named dimension constants used throughout the definition (optional)
- The schema name (e.g. `NXmpes(NXobject)`): the parenthesized base class indicates what this definition extends. An application definition extends either `NXobject` or another application definition.

!!! warning
    All definition-level keys (`\category`, `\type`, `\doc`, `\symbols`, `\deprecated`, `\restricts`, `\ignoreExtraGroups`, `\ignoreExtraFields`, `\ignoreExtraAttributes`) **must** be written with the `\` prefix. Writing them bare (e.g. `category:` instead of `\category:`) is an error and the converter will reject the file.

=== "YAML"
    ```yaml
    \category: application
    \type: group
    \doc: |
      This is the most general application definition for multidimensional photoelectron spectroscopy.

      .. _ISO 18115-1:2023: https://www.iso.org/standard/74811.html
      .. _IUPAC Recommendations 2020: https://doi.org/10.1515/pac-2019-0404
    \symbols:
      \doc: |
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

---

## Groups

[NeXus groups](https://manual.nexusformat.org/design.html#design-groups){:target="_blank" rel="noopener"} are instances of NeXus base classes and form the compositional structure of a definition. A group is written as `name(NXbaseclass):` in YAML.

The `\nameType` keyword (see below) controls whether the name is matched exactly, loosely, or as a prefix (or suffix) pattern in HDF5 files. Dynamic initialization (using `\nameType: any`) allows multiple instances of the same group type at the same hierarchy level; for example, `(NXmanipulator)` (with `\nameType: any`) can be instantiated as `manipulator1` and `manipulator2` during data writing.

The `group` annotation `source_TYPE(NXsource)` means the group's concept name is `source_TYPE` and its type is the `NXsource` base class. For `\nameType: partial`, the uppercase part of the name can be replaced at instantiation time, allowing multiple distinct instances (e.g. `source_electric` and `source_magnetic`). The same uppercase rules apply to fields and attributes.

=== "YAML"
    ```yaml
    source_TYPE(NXsource):
      \exists: recommended
      \nameType: partial
      \doc: |
        A source used to generate a beam.
    (NXmanipulator):
      \exists: optional
      \nameType: any  # default for anonymous groups
      \doc: |
        Manipulator for positioning of the sample.
      value_log(NXlog):
        \exists: optional
    ```

=== "XML"
    ```xml
    <group name="source_TYPE" type="NXsource" recommended="true" nameType="partial">
      <doc>
        A source used to generate a beam.
      </doc>
    </group>
    <!-- If no nameType is specified, NXmanipulator has nameType any by default -->
    <group type="NXmanipulator" optional="true" nameType="any">
      <doc>
        Manipulator for positioning of the sample.
      </doc>
      <group name="value_log" type="NXlog" optional="true"/>
    </group>
    ```

---

## Fields and attributes

A NeXus `field` is a named data entry written without an `NX` prefix. Its NeXus type is given in parentheses, e.g. `end_time(NX_DATE_TIME)`. If the type is omitted the field defaults to `NX_CHAR`. See the [full list of NeXus types](https://manual.nexusformat.org/nxdl-types.html#index-0){:target="_blank" rel="noopener"}.

A NeXus `attribute` is a metadata entry for a field or group, prefixed with `\@`. It must also have a NeXus type, which defaults to `NX_CHAR` if omitted.

Descriptive text for any concept is given in the `\doc` child.

=== "YAML"
    ```yaml
    (NXentry):
      definition:  # Field type: NX_CHAR
        \@version:  # Attribute type: NX_CHAR
        \enumeration: [NXmpes]
      title:
      start_time(NX_DATE_TIME):
        \doc: Datetime of the start of the measurement.
      end_time(NX_DATE_TIME):
        \exists: recommended
        \doc: Datetime of the end of the measurement.
    ```
=== "XML"
    ```xml
    <group type="NXentry">
      <field name="definition" type="NX_CHAR">
        <attribute name="version"/>
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

---

## Links

A NeXus `link` avoids data duplication by letting one concept point to another. In YAML it uses the `(link)` suffix; the `\target` child gives the path to the actual data.

=== "YAML"
    ```yaml
    reference_measurement(link):
      \target: /entry
      \doc: A link to a full data collection.
    ```
=== "XML"
    ```xml
    <link type="NXentry" target="/entry">
      <doc>A link to a full data collection.</doc>
    </link>
    ```

In the example above, `reference_measurement` links to the `NXentry` group at `/entry`. This ensures that the concept referencing the data points to the designated target, reducing redundancy and maintaining data integrity.

---

## Special keywords

### Reserved keywords and escape characters

`nyaml` uses a set of reserved keys, each written with a `\` prefix, that map to NXDL concept properties. The `\` prefix activates the corresponding feature; writing the same key *without* the `\` prefix makes it a plain concept name (field or group) instead, and  `\@` for attributes.

**Reserved keywords**

| Keyword | Where it applies |
|---------|-----------------|
| `\doc` | doc string for any concept |
| `\unit` | NeXus unit category for a field |
| `\enumeration` | enumeration values for a field or attribute |
| `\nameType` | enumeration for the name-matching rule (`specified`, `any`, `partial`) |
| `\dim` | dimension specification shorthand |
| `\dimensions` | full dimension block |
| `\exists` | presence constraint (`required`, `recommended`, `optional`, …) |
| `\minOccurs`, `\maxOccurs` | occurrence bounds |
| `\rank` | rank inside a `\dimensions` block |
| `\type` | NeXus type override for a field or the root group type |
| `\category` | root-level definition category (`base` or `application`) |
| `\symbols` | root-level named dimension constants |
| `\deprecated` | deprecation notice |
| `\restricts`, `\ignoreExtraGroups`, `\ignoreExtraFields`, `\ignoreExtraAttributes` | root-level definition modifiers |

**Using a reserved keyword as a concept name**

Omit the `\` prefix to use a keyword as an actual field, group, or attribute name:

=== "YAML"
    ```yaml
    NXtest(NXobject):
      doc:           # plain concept named "doc"  →  <field name="doc"/>
      unit:          # plain concept named "unit" →  <field name="unit"/>
      enumeration:   # plain concept named "enumeration" → <field name="enumeration"/>
    ```
=== "XML"
    ```xml
    <group name="NXtest" type="NXobject">
      <field name="doc"/>
      <field name="unit"/>
      <field name="enumeration"/>
    </group>
    ```

With the `\` prefix, `\doc:`, `\unit:`, and `\enumeration:` activate their respective handlers and produce `<doc>`, `<field units="…">`, and `<enumeration>` elements.

The `\@` prefix for XML attributes follows the same convention: `\@version` names the attribute `version` in the NXDL output, distinguishing it from a child field named `version`.

---

### `nameType`

Controls how an instance name in an HDF5 file is matched against the concept name in the definition.

|      `nameType`      |        `specified`         |              `any`             |          `partial`           | Default value  |
|----------------------|----------------------------|--------------------------------|------------------------------|----------------|
| All upper case       | &#10003;                   | &#10003;                       | &#10003; (with warning)      | `specified`    |
| All lower case       | &#10003;                   | &#10003; (with warning)        | &#10003; (with error)        | `specified`    |
| Mixed case           | &#10003;                   | &#10003; (with warning)        | &#10003;                     | `specified`    |
| Anonymous group name | &#10003; (with error)      | &#10003;                       | &#10003; (with error)        | `any`          |

=== "YAML"
    ```yaml
    source_TYPE(NXsource):
      \exists: recommended
      \nameType: partial
      \doc: |
        A source used to generate a beam.
    (NXmanipulator):
      \exists: optional
      \nameType: any  # default for anonymous groups
      \doc: |
        Manipulator for positioning of the sample.
      value_log(NXlog):
        \exists: optional
    ```

=== "XML"
    ```xml
    <group name="source_TYPE" type="NXsource" recommended="true" nameType="partial">
      <doc>
        A source used to generate a beam.
      </doc>
    </group>
    <!-- If no nameType is specified, NXmanipulator has nameType any by default -->
    <group type="NXmanipulator" optional="true" nameType="any">
      <doc>
        Manipulator for positioning of the sample.
      </doc>
      <group name="value_log" type="NXlog" optional="true"/>
    </group>
    ```

---

### `exists`

Controls whether an instance of a concept is present in a conforming NeXus file. By default, all concepts in a base class are optional, and all concepts in an application definition are required.

Accepted values:

- `required`: must be present; validation fails if absent
- `recommended`: advised but not mandatory; validation warns if absent
- `optional`: may be absent without any validation error
- `[min, <number>, max, <number> or infty]`: specifies a multiplicity range

=== "YAML"
    ```yaml
    transmission_correction(NXcalibration):
      \exists: optional
      \doc: |
        This calibration procedure is used to account for the different transmission efficiencies.
      calibrationDATA(NXdata):
        \exists: [min, 3, max, infty]
    ```
=== "XML"
    ```xml
    <group name="transmission_correction" type="NXcalibration" optional="true">
      <doc>
        This calibration procedure is used to account for the different transmission efficiencies.
      </doc>
      <group name="calibrationDATA" type="NXdata" minOccurrences="3" maxOccurrences="unbounded"/>
    </group>
    ```

In the example above, `transmission_correction` is optional, while `calibrationDATA` must appear at least three times.

---

### `unit`

Specifies the NeXus unit category for a field. Use one of the existing [unit categories](https://manual.nexusformat.org/nxdl-types.html#unit-categories-allowed-in-nxdl-specifications){:target="_blank" rel="noopener"} (e.g. `NX_VOLTAGE`, `NX_LENGTH`, `NX_WAVELENGTH`) rather than raw unit strings like `"m"`. The unit category declares the physical dimension; the actual unit written to the HDF5 file (e.g. `V`, `mV`) is stored as a sibling attribute `fieldname/@units`.

=== "YAML"
    ```yaml
    detector_voltage(NX_FLOAT):
      \unit: NX_VOLTAGE
      \doc: |
        Voltage applied to detector.
    ```
=== "XML"
    ```xml
    <field name="detector_voltage" type="NX_FLOAT" units="NX_VOLTAGE">
      <doc>Voltage applied to detector.</doc>
    </field>
    ```

---

### `dimensions`

Describes the shape of a data array. Using the "dimensions" keyword constraints the instance data of a field to an array with at least one dimension. The `\rank` key gives the number of dimensions. Each dimension is specified with `\dim` using either the full array-of-arrays form or the shorter tuple form. Use symbolic names from the root `\symbols` block rather than hardcoded integers.

=== "YAML"
    ```yaml
    # 2D particle motion, full form
    \dimensions:
      \rank: 2
      \dim: [[0, nx], [1, ny]]
    ```

=== "YAML (shorter form)"
    ```yaml
    # 2D particle motion, shorter form
    \dimensions:
      \rank: 2
      \dim: (nx, ny)
    ```
=== "XML"
    ```xml
    <dimensions rank="2">
      <dim index="0" value="nx"/>
      <dim index="1" value="ny"/>
    </dimensions>
    ```

---

### `enumeration`

A list of predefined allowed values for a field or attribute. Individual items may include a `doc` child. Set `\open: true` to allow values beyond the listed ones.

=== "YAML"
    ```yaml
    definition:
      \@version:
        \enumeration: [NXmpes]
    ```
=== "XML"
    ```xml
    <field name="definition">
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
      \enumeration:
        \open: true
        \items: [NXmpes]
    ```
=== "XML (open enum)"
    ```xml
    <field name="enum_with_open_enum">
      <enumeration open="true">
        <item value="NXmpes"/>
      </enumeration>
    </field>
    ```

=== "YAML (open enum with doc)"
    ```yaml
    enum_with_open_and_vector_items:
      \enumeration:
        \open: true
        '[0, 1, 0]':
          \doc: |
            This is an open enumeration with values 0, 1, and 0.
        '[0, 1, 1]':
          \doc: |
            This is an open enumeration with values 0, 1, and 1.
    ```
=== "XML (open enum with doc)"
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

---

### `xref`

The `\xref` keyword (only valid inside `\doc`) links a concept to an entry in an external ontology or standard such as ISO. It is YAML-only: `nyaml` converts it to the corresponding textual representation inside the XML `<doc>` element.

=== "YAML"
    ```yaml
    (NXinstrument):
      \doc:
      - |
        Description of the MPES spectrometer and its individual parts.
      - |
        \xref:
          \spec: ISO 18115-1:2023
          \term: 12.58
          \url: https://www.iso.org/obp/ui/en/#iso:std:iso:18115:-1:ed-3:v1:en:term:12.58
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

---

## NXDL coverage

`nyaml` covers all NXDL concepts that are relevant to writing modern NeXus definitions. The table below maps each major NXDL XSD type and its attributes to the corresponding nyaml notation.

| NXDL XSD concept | Attributes / children | nyaml notation |
|---|---|---|
| `definition` | `category` | `\category` |
| | `type` | `\type` |
| | `name`, `extends` | `NXname(NXbase):` key |
| | `restricts` | `\restricts` |
| | `deprecated` | `\deprecated` |
| | `ignoreExtraGroups` | `\ignoreExtraGroups` |
| | `ignoreExtraFields` | `\ignoreExtraFields` |
| | `ignoreExtraAttributes` | `\ignoreExtraAttributes` |
| `group` | `name`, `type` | `name(NXbaseclass):` key |
| | `minOccurs`, `maxOccurs` | `\minOccurs`, `\maxOccurs` |
| | `recommended`, `optional` | `\exists: recommended`, `\exists: optional` |
| | `nameType` | `\nameType` |
| | `deprecated` | `\deprecated` |
| `field` | `name` | plain key, e.g. `fieldname:` |
| | `type` | `fieldname(NX_TYPE):` |
| | `units` | `\unit` |
| | `minOccurs`, `maxOccurs` | `\minOccurs`, `\maxOccurs` |
| | `recommended`, `optional` | `\exists: recommended`, `\exists: optional` |
| | `nameType` | `\nameType` |
| | `deprecated` | `\deprecated` |
| | `dimensions` child | `\dimensions` with `\rank`, `\dim` |
| | `enumeration` child | `\enumeration` |
| | `attribute` child | `\@name:` |
| `attribute` | `name`, `type` | `\@name(NX_TYPE):` |
| | `recommended`, `optional` | `\exists: recommended`, `\exists: optional` |
| | `nameType` | `\nameType` |
| | `enumeration` child | `\enumeration` |
| `link` | `name` | `name(link):` key |
| | `target` | `\target` |
| | `napimount` | `\napimount` |
| `enumeration` | `open` | `\open: true` |
| | `item` children | list items or dict keys under `\enumeration` (possibly with `items`) |
| `doc` | free text | `\doc` |
| | cross-reference | `\xref` with `\spec`, `\term`, `\url` |
| `symbols` | `doc`, `symbol` children | `\symbols` block |
| `dimensions` | `rank` | `\rank` |
| | `dim` children | `\dim` |

**Not supported:**

- `choice` — the NeXus `choice` element is not yet implemented in `nyaml`
- Legacy `field` XML attributes (`signal`, `axes`, `axis`, `primary`, `long_name`, `stride`, `data_offset`, `interpretation`) — these are field XML attributes that are now deprecated; use `\@signal:`, `\@axes:` etc. (the standard `attribute` syntax) instead
