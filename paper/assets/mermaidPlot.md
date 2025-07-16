  ```mermaid
  graph TD;
    subgraph Start
      id1["Input File (YAML or XML)"]
    end
    subgraph Correct File Converter
      id2["nyaml2nxdl Converter"]
      id3["nxdl2nyaml Converter"]
    end
    subgraph nyaml2nxdl
      id4["Comment Collector"]
      id5["Python Dictionary Object"]
    end
    subgraph nxdl2nyaml
      id6["XML Object"]
      id7["YAML File (intermediate)"]
      id8["SHA256 Hash for YAML Content"]
    end
    subgraph Final result
    id9["Write XML File"]
    id10["Write YAML File"]
    end

    id1--> |YAML File|id2
    id1--> |XML File|id3
    id2-->nyaml2nxdl
    id4-->id5
    id3-->nxdl2nyaml
    id6-->id7
    id7-->id8
    nyaml2nxdl-->id9
    nxdl2nyaml-->id10
  ```
