# Writing a NeXus definition in YAML

This tutorial walks you through writing a NeXus application definition in YAML using `nyaml`. You will build a complete definition step by step, learning each concept as it is introduced.

## What should you know before this tutorial?

- You should have a basic understanding of NeXus: see [Learn > Introduction to NeXus](https://manual.nexusformat.org/index.html){:target="_blank" rel="noopener"}
- You should have `nyaml` installed: see [Tutorials > Installation](installation.md)

## What you will know at the end of this tutorial?

You will know

- the basic structure of a NeXus definition written in YAML
- how to write groups, fields, and attributes
- how to use the key special keywords (`\exists`, `\unit`, `\dimensions`, `\enumeration`, etc.)
- how to convert a YAML definition to NXDL XML using `nyaml2nxdl`

!!! note
    We are making extensive use of special keywords here (`\nameType`, `\exists`, `\unit`, `\dimensions`, `\enumeration`, `\xref`) that indicate specific parts of the NeXus schema in the YAML notation. All of these keywords are identified by the `\` prefix. To learn more, see [Learn > nyaml notation](../learn/yaml-notation.md). The NeXus `choice` concept is not yet supported in `nyaml`.

---

## Goal

We will build `NXmy_measurement`, a minimal but complete application definition for a simple 2D detector measurement. By the end you will have a valid YAML definition and know how to convert it to NXDL XML.

---

## Step 1: The root section

Every NeXus definition starts with a root section. It sets the `\category` (`application` or `base`), the `\type` (always `group`), a human-readable `\doc` string, and the name of the NeXus definition.

Create a file called `NXmy_measurement.yaml` with this content:

```yaml
\category: application
\doc: |
  Minimal application definition for a 2D detector measurement.
\type: group
NXmy_measurement(NXobject):
```

The last line `NXmy_measurement(NXobject):` declares the definition name and the class it extends. Application definitions typically extend `NXobject`.

You can already convert this to XML:

```bash
nyaml2nxdl NXmy_measurement.yaml
```

This produces `NXmy_measurement.nxdl.xml`.

---

## Step 2: Add an entry with basic metadata fields

Real NeXus application definitions wrap their data in an `NXentry` group. Inside it, a `definition` field identifies which application definition the file conforms to. Add this inside `NXmy_measurement(NXobject):`:

```yaml
NXmy_measurement(NXobject):
  (NXentry):
    definition:
      \enumeration: [NXmy_measurement]
    title:
    start_time(NX_DATE_TIME):
      \doc: Datetime of the start of the measurement.
    end_time(NX_DATE_TIME):
      \exists: recommended
      \doc: Datetime of the end of the measurement.
```

A few things to notice:

- `(NXentry):` without a name means any valid group name is accepted in the HDF5 file (e.g. `entry`, `entry1`). This is `\nameType: any`, the default for anonymous groups.
- `definition:` is a field with no type, so it defaults to `NX_CHAR`.
- `start_time(NX_DATE_TIME):` declares a field with NeXus type `NX_DATE_TIME`.
- `\exists: recommended` on `end_time` means it is advised but not required. By default all concepts in an application definition are required; `\exists` relaxes that. In base classes, however, all concepts are optional.

---

## Step 3: Add an instrument group with a detector

The `NXinstrument` group describes the experimental setup. Inside it we add a detector:

```yaml
NXmy_measurement(NXobject):
  (NXentry):
    definition:
      \enumeration: [NXmy_measurement]
    title:
    start_time(NX_DATE_TIME):
      \doc: Datetime of the start of the measurement.
    end_time(NX_DATE_TIME):
      \exists: recommended
      \doc: Datetime of the end of the measurement.
    (NXinstrument):
      detector(NXdetector):
        \doc: The 2D area detector.
        distance(NX_FLOAT):
          \unit: NX_LENGTH
          \doc: Distance from sample to detector surface.
```

The `\unit: NX_LENGTH` line declares the unit *category* for the `distance` field. This tells readers and validators that the stored values are a length (metres, millimeters, etc.), without fixing the exact unit; the writer stores the actual unit as a sibling HDF5 attribute. Use one of the [NeXus unit categories](https://manual.nexusformat.org/nxdl-types.html#unit-categories-allowed-in-nxdl-specifications){:target="_blank" rel="noopener"} rather than raw strings like `"m"`.

---

## Step 4: Add array data with `dimensions`

The detector records a 2D intensity array. Use `\dimensions` to declare its shape. Symbolic dimension names make the definition self-documenting and allow validators to check dimensional consistency across fields. Add a `\symbols` block at the root and a `data` field inside the detector:

```yaml
\category: application
\doc: |
  Minimal application definition for a 2D detector measurement.
\type: group
\symbols:
  \doc: Dimension symbols used in this definition.
  n_x: Number of detector pixels along x.
  n_y: Number of detector pixels along y.
NXmy_measurement(NXobject):
  (NXentry):
    definition:
      \enumeration: [NXmy_measurement]
    title:
    start_time(NX_DATE_TIME):
      \doc: Datetime of the start of the measurement.
    end_time(NX_DATE_TIME):
      \exists: recommended
      \doc: Datetime of the end of the measurement.
    (NXinstrument):
      detector(NXdetector):
        \doc: The 2D area detector.
        distance(NX_FLOAT):
          \unit: NX_LENGTH
          \doc: Distance from sample to detector surface.
        data(NX_NUMBER):
          \unit: NX_ANY
          \doc: Raw 2D intensity array.
          \dimensions:
            \rank: 2
            \dim: (n_x, n_y)
```

The `\dimensions` block declares `\rank: 2` and uses the symbolic names `n_x` and `n_y` from `\symbols`. A shorter `\dim: (n_x, n_y)` tuple form is equivalent to the verbose `\dim: [[0, n_x], [1, n_y]]` form.

---

## Step 5: Mark optional fields with `exists`

Not everything needs to be required. Add recommended pixel-offset fields to the detector:

```yaml
        x_pixel_offset(NX_FLOAT):
          \exists: recommended
          \unit: NX_LENGTH
          \doc: Horizontal pixel positions relative to the detector centre.
          \dimensions:
            \rank: 1
            \dim: (n_x,)
        y_pixel_offset(NX_FLOAT):
          \exists: recommended
          \unit: NX_LENGTH
          \doc: Vertical pixel positions relative to the detector centre.
          \dimensions:
            \rank: 1
            \dim: (n_y,)
```

There is often no practical difference between `\exists: recommended` and `\exists: optional`. In most validation tools, neither `\exists: recommended` nor `\exists: optional` cause a validation error if the concept is absent. The distinction is semantic and aimed at readers of the definition: `recommended` signals that the field is extremely helpful for understanding the experiment even if it is not strictly required to interpret the data, while `optional` is for purely supplementary metadata whose absence is entirely unsurprising.

---

## Step 6: Add a default plot group

NeXus convention: every application definition should have a default `NXdata` group with `@signal` and `@axes` attributes so tools can find the primary data to plot without user configuration. Add it as a sibling of `(NXinstrument)`:

```yaml
    data(NXdata):
      \doc: Default plot.
      \@signal:
        \enumeration: [data]
      \@axes:
        \enumeration: [['x_pixel_offset', 'y_pixel_offset']]
      data(NX_NUMBER):
        \unit: NX_ANY
        \dimensions:
          \rank: 2
          \dim: (n_x, n_y)
      x_pixel_offset(NX_FLOAT):
        \unit: NX_LENGTH
        \dimensions:
          \rank: 1
          \dim: (n_x,)
      y_pixel_offset(NX_FLOAT):
        \unit: NX_LENGTH
        \dimensions:
          \rank: 1
          \dim: (n_y,)
```

The `\@signal` and `\@axes` entries are NeXus *attributes* (prefixed with `\@`) that label which field is the signal and which are the axes for plotting.

!!! note
    In a real HDF5 file these fields would typically be HDF5 hard-links into the detector group rather than duplicated data. The NXDL definition specifies what *must be accessible* at that path; the writer decides whether to copy or link.

We are also using `\enumeration` here to restrict the values that the `signal` and `axes` attributes can have in data instance files.

---

## Step 7: Convert to NXDL XML

Convert the finished definition:

```bash
nyaml2nxdl NXmy_measurement.yaml
```

You can also go in the reverse direction — for example, to start from an existing XML definition and edit it in YAML:

```bash
nyaml2nxdl NXmy_measurement.nxdl.xml --output-file NXmy_measurement.yaml
```

??? success "Complete NXmy_measurement.yaml"
    ```yaml
    \category: application
    \doc: |
      Minimal application definition for a 2D detector measurement.
    \type: group
    \symbols:
      \doc: Dimension symbols used in this definition.
      n_x: Number of detector pixels along x.
      n_y: Number of detector pixels along y.
    NXmy_measurement(NXobject):
      (NXentry):
        definition:
          \enumeration: [NXmy_measurement]
        title:
        start_time(NX_DATE_TIME):
          \doc: Datetime of the start of the measurement.
        end_time(NX_DATE_TIME):
          \exists: recommended
          \doc: Datetime of the end of the measurement.
        (NXinstrument):
          detector(NXdetector):
            \doc: The 2D area detector.
            distance(NX_FLOAT):
              \unit: NX_LENGTH
              \doc: Distance from sample to detector surface.
            data(NX_NUMBER):
              \unit: NX_ANY
              \doc: Raw 2D intensity array.
              \dimensions:
                \rank: 2
                \dim: (n_x, n_y)
            x_pixel_offset(NX_FLOAT):
              \exists: recommended
              \unit: NX_LENGTH
              \doc: Horizontal pixel positions relative to the detector centre.
              \dimensions:
                \rank: 1
                \dim: (n_x,)
            y_pixel_offset(NX_FLOAT):
              \exists: recommended
              \unit: NX_LENGTH
              \doc: Vertical pixel positions relative to the detector centre.
              \dimensions:
                \rank: 1
                \dim: (n_y,)
        data(NXdata):
          \doc: Default plot.
          \@signal:
            \enumeration: [data]
          \@axes:
            \enumeration: [['x_pixel_offset', 'y_pixel_offset']]
          data(NX_NUMBER):
            \unit: NX_ANY
            \dimensions:
              \rank: 2
              \dim: (n_x, n_y)
          x_pixel_offset(NX_FLOAT):
            \unit: NX_LENGTH
            \dimensions:
              \rank: 1
              \dim: (n_x,)
          y_pixel_offset(NX_FLOAT):
            \unit: NX_LENGTH
            \dimensions:
              \rank: 1
              \dim: (n_y,)
    ```

---

## Next steps

- For the full reference of all YAML keywords (`\nameType`, `\exists`, `\unit`, `\dimensions`, `\enumeration`, `\xref`) with complete YAML/XML comparisons, see [Learn > nyaml notation](../learn/yaml-notation.md)
- To validate your converted NXDL file, fork the [official NeXus definitions repository](https://github.com/nexusformat/definitions){:target="_blank" rel="noopener"} and open a pull request; the repository runs an automated validation workflow on every pull request
- For a full end-to-end walkthrough (writing, validating, and contributing to the community definitions), see [pynxtools > Tutorials > Writing your first application definition](https://fairmat-nfdi.github.io/pynxtools/tutorial/writing-an-application-definition.html){:target="_blank" rel="noopener"}
