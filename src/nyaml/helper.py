#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
File consists of helping functions and variables.

The functions and variables are utilized in the converting tool
to convert from nyaml to nxdl and vice versa.
"""

import hashlib
import os
from typing import Any

from yaml.composer import Composer
from yaml.constructor import Constructor
from yaml.loader import SafeLoader
from yaml.nodes import ScalarNode
from yaml.resolver import BaseResolver

# Yaml library does not except the keys (escape char "\t" and yaml separator ":")
ESCAPE_CHAR_DICT_IN_YAML: dict[str, str] = {"\t": "    "}
ESCAPE_CHAR_DICT_IN_XML: dict[str, str] = {
    val: key for key, val in ESCAPE_CHAR_DICT_IN_YAML.items()
}

# Reserved nyaml keywords that map to NXDL concepts rather than concept names.
# Use a backslash prefix (e.g. \rank) to use one of these as a concept name.
# \@ is already the escape prefix for XML attributes (e.g. \@version).
RESERVED_KEYWORDS = frozenset(
    {
        "doc",
        "unit",
        "enumeration",
        "nameType",
        "dim",
        "dimensions",
        "exists",
        "minOccurs",
        "maxOccurs",
        "rank",  # sub-key inside a 'dimensions' block
    }
)

# Set up attributes for nxdl version
NXDL_GROUP_ATTRIBUTES: tuple[str, ...] = (
    "optional",
    "recommended",
    "name",
    "type",
    "maxOccurs",
    "minOccurs",
    "deprecated",
    "nameType",
)
NXDL_FIELD_ATTRIBUTES: tuple[str, ...] = (
    "optional",
    "recommended",
    "name",
    "type",
    "axes",
    "axis",
    "data_offset",
    "interpretation",
    "long_name",
    "maxOccurs",
    "minOccurs",
    "nameType",
    "primary",
    "signal",
    "stride",
    "required",
    "deprecated",
    "units",
)

NXDL_ATTRIBUTES_ATTRIBUTES: tuple[str, ...] = (
    "name",
    "type",
    "recommended",
    "optional",
    "deprecated",
    "nameType",
)

NXDL_LINK_ATTRIBUTES: tuple[str, ...] = ("name", "target", "napimount", "nameType")

# Set up attributes for yaml version
YAML_GROUP_ATTRIBUTES: tuple[str, ...] = (*NXDL_GROUP_ATTRIBUTES, "exists")

YAML_FIELD_ATTRIBUTES: tuple[str, ...] = (
    *NXDL_FIELD_ATTRIBUTES[0:-1],
    "unit",
    "exists",
    "dim",
)

YAML_ATTRIBUTES_ATTRIBUTES: tuple[str, ...] = (
    *NXDL_ATTRIBUTES_ATTRIBUTES,
    "minOccurs",
    "maxOccurs",
    "exists",
)

YAML_LINK_ATTRIBUTES: tuple[str, ...] = NXDL_LINK_ATTRIBUTES


def remove_namespace_from_tag(tag: object) -> str:
    """Helper function to remove the namespace from an XML tag."""
    if callable(tag) and getattr(tag, "__name__", "") == "Comment":
        return "!--"
    if isinstance(tag, (bytes, bytearray)):
        tag = tag.decode("utf-8", errors="ignore")
    if isinstance(tag, str):
        return tag.split("}")[-1]
    return str(tag).split("}")[-1] if tag is not None else ""


def check_for_proper_nameType(
    name: str,
    nameType: str | None,
    keyword_name: str,
) -> None:
    """Check for proper nameType for a given name.

    Rules:
    - If nameType is present, it must be one of ("specified", "any", "partial")

    - Name not given (only for groups):
      - Should have no nameType.
      - nameType="any" does not raise.
      - nameType in ("specified", "partial") raises an error.

    - Name with all lower case letters:
      - Should have no nameType (i.e., default to "specified") or nameType="specified".
      - If nameType="any", print a warning (fully renameable in this case).
      - If nameType="partial", print an error.

    - Name with all upper case letters:
      - Should have nameType in ("any", "specified").
      - If no nameType, NeXus assumption is nameType="specified".
      - If nameType="partial", print a warning (fully renameable in this case).

    - Name with upper case and lower case letters:
      - Should have nameType="partial".
      - If nameType="specified", do not raise or warn.
      - If no nameType, NeXus assumption is nameType="specified". Print an information.
      - If nameType="any", print an a warning (fully renameable in this case).
    """
    allowed_name_types = ("specified", "any", "partial")

    if nameType:
        if nameType not in allowed_name_types:
            raise ValueError(
                f'Name "{keyword_name}" has nameType="{nameType}", but only one of '
                f'("specified", "any", "partial") is allowed.'
            )

    if not name:  # Unnamed group case
        if not nameType or nameType == "any":
            return
        raise ValueError(
            f'Unnamed group should have either no nameType or nameType="any". '
            f'Found nameType="{nameType}".'
        )

    if name.islower():  # All lower cases
        if not nameType or nameType == "specified":
            return
        if nameType == "any":
            print(
                f'Warning: Name "{keyword_name}" (all lowercase) has nameType="any", which makes it fully renameable. '
                "Is that intentional?"
            )
        elif nameType == "partial":
            print(
                f'Error: Name "{keyword_name}" (all lowercase) has nameType="partial", but nothing can be replaced. '
                'Consider introducing upper case letters or dropping nameType="partial".'
            )

    elif name.isupper():  # All upper cases
        if not nameType:
            return  # Default assumption is "specified"
        if nameType not in ("any", "specified"):
            print(
                f'Warning: Name "{keyword_name}" (all uppercase) has nameType="partial".'
                ' Since the name only has uppercase letters, there is no difference to nameType="any".'
            )

    else:  # Mixed upper and lower case
        if not nameType:
            print(
                f'Info: Name "{keyword_name}" (mixed upper and lower case) has no nameType, assuming "specified".'
            )
            return
        if nameType == "any":
            print(
                f'Warning: Name "{keyword_name}" (mixed upper and lower case) has nameType="any", which makes it fully renameable. '
                "Is that intentional?"
            )


class LineLoader(SafeLoader):  # pylint: disable=too-many-ancestors
    """Class to load yaml file with extra non yaml items.

    LineLoader parses a yaml into a python dictionary extended with extra items.
    The new items have as keys __line__<yaml_keyword> and as values the yaml file line number
    """

    def compose_node(self, parent: Any, index: Any) -> Any:
        """Compose node and return node."""
        # the line number where the previous token has ended (plus empty lines)
        node = Composer.compose_node(self, parent, index)
        setattr(node, "__line__", self.line + 1)
        return node

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        """Construct mapping between node info and line info."""
        node_pair_lst_for_appending = []

        # Visit through node-pair list
        for key_node in node.value:
            shadow_key_node = ScalarNode(
                tag=BaseResolver.DEFAULT_SCALAR_TAG,
                value="__line__" + key_node[0].value,
            )
            shadow_value_node = ScalarNode(
                tag=BaseResolver.DEFAULT_SCALAR_TAG, value=key_node[0].__line__
            )
            node_pair_lst_for_appending.append((shadow_key_node, shadow_value_node))

        node.value = node.value + node_pair_lst_for_appending
        return Constructor.construct_mapping(self, node, deep=deep)


def get_yaml_escape_char_dict() -> dict[str, str]:
    """Get escape char and the way to skip them in yaml."""
    return ESCAPE_CHAR_DICT_IN_YAML


def get_yaml_escape_char_reverter_dict() -> dict[str, str]:
    """To revert yaml escape char in xml constructor from yaml."""

    return ESCAPE_CHAR_DICT_IN_XML


def type_check(nx_type: str) -> str:
    """Check for nexus type if type is NX_CHAR get '' or get as it is."""

    if nx_type in ["NX_CHAR", ""]:
        nx_type = ""
    else:
        nx_type = f"({nx_type})"
    return nx_type


def get_node_parent_info(tree: Any, node: Any) -> tuple[Any, int]:
    """Return tuple of (parent, index).

    parent = parent node is the first level node under tree node
    index = index of grand child node of tree
    """

    # map from grand child to parent which is child of tree
    parent_map: dict[Any, Any] = {c: p for p in tree.iter() for c in p}
    parent = parent_map[node]
    return parent, list(parent).index(node)


def clean_empty_lines(line_list: list[str] | str) -> list[str]:
    """Clean up empty lines by top part and bottom and part."""
    if not isinstance(line_list, list):
        line_list = line_list.split("\n") if "\n" in line_list else [""]

    start_non_empty_line = -1
    ends_non_empty_line: int | None = None
    # Find the index of first non-empty line
    for ind, line in enumerate(line_list):
        if len(line.strip()) > 1:
            start_non_empty_line = ind
            break

    # Find the index of the last non-empty line
    for ind, line in enumerate(reversed(line_list)):
        if len(line.strip()) > 1:
            ends_non_empty_line = -ind
            break

    if ends_non_empty_line == 0:
        ends_non_empty_line = None
    return line_list[start_non_empty_line:ends_non_empty_line]


def nx_name_type_resolving(tmp: str) -> tuple[str, str]:
    """Separate name and NeXus type

    Extracts the eventual custom name {optional_string}
    and type {nexus_type} from a YML section string.
    YML section string syntax: optional_string(nexus_type)
    """
    if tmp.count("(") == 1 and tmp.count(")") == 1:
        # we can safely assume that every valid YML key resolves
        # either an nx_ (type, base, candidate) class contains only 1 '(' and ')'
        index_start = tmp.index("(")
        index_end = tmp.index(")", index_start + 1)
        if index_start > index_end:
            raise ValueError(
                f"Check name and type combination {tmp} which can not be resolved."
            )
        if index_end - index_start == 1:
            raise ValueError(
                f"Check name(type) combination {tmp}, properly not defined."
            )
        typ = tmp[index_start + 1 : index_end]
        nam = tmp.replace("(" + typ + ")", "")
        return nam, typ

    # or a name for a member
    typ = ""
    nam = tmp
    return nam, typ


def get_sha256_hash(file_name: str | os.PathLike[str]) -> str:
    """Generate a sha256_hash for a given file."""
    sha_hash = hashlib.sha256()

    with open(
        file=os.fspath(file_name),
        mode="rb",
    ) as file_obj:
        # Update hash for each 4k block of bytes
        for b_line in iter(lambda: file_obj.read(4096), b""):
            sha_hash.update(b_line)
    return sha_hash.hexdigest()


def extend_yaml_file_by_nxdl_as_comment(
    yaml_file: str | os.PathLike[str],
    file_to_be_appended: str | os.PathLike[str],
    top_lines_list: list[str] | None = None,
) -> None:
    """Extend yaml file by the file_to_be_appended as comment."""

    with open(os.fspath(yaml_file), mode="a+", encoding="utf-8") as f1_obj:
        if top_lines_list:
            for line in top_lines_list:
                f1_obj.write(line)

        with open(os.fspath(file_to_be_appended), encoding="utf-8") as f2_obj:
            for line in f2_obj:
                f1_obj.write(f"# {line}")


def separate_hash_yaml_and_nxdl(
    yaml_file: str | os.PathLike[str],
    sep_yaml: str | os.PathLike[str],
    sep_xml: str | os.PathLike[str],
) -> str:
    """Separate yaml, SHA hash and nxdl parts.

    Separate the provided yaml file into yaml, nxdl and hash if yaml was extended with
    nxdl at the end of yaml as

                    <yaml part>
        '\n# ++++++++++++++++++++++++++++++++++ SHA HASH \
            ++++++++++++++++++++++++++++++++++\n'
         # <has value>'
                    <nxdl part>
    """
    sha_hash = ""
    with open(os.fspath(yaml_file), encoding="utf-8") as inp_file:
        lines = inp_file.readlines()
        # file to write yaml part
        with (
            open(os.fspath(sep_yaml), "w", encoding="utf-8") as yml_f_ob,
            open(os.fspath(sep_xml), "w", encoding="utf-8") as xml_f_ob,
        ):
            write_on_yaml = True

            last_line = lines[0]
            for line in lines[1:]:
                # Write in file when ensured that the next line is not with '++ SHA HASH ++'
                if "++ SHA HASH ++" not in line and write_on_yaml:
                    yml_f_ob.write(last_line)
                    last_line = line
                elif "++ SHA HASH ++" in line:
                    write_on_yaml = False
                    last_line = ""
                elif not write_on_yaml and not last_line:
                    # The first line of xml file has been found so in future write lines directly
                    # into xml file.
                    if not sha_hash:
                        sha_hash = line.split("# ", 1)[-1].strip()
                    else:
                        xml_f_ob.write(line[2:])
            # If the yaml file does not contain any hash for nxdl then we may have last line.
            if last_line:
                yml_f_ob.write(last_line)

    return sha_hash


def is_copyright_comment(text: str) -> bool:
    """Analyze a comment, whether it is a copyright comment or not.

    Return true if dom comment.
    """

    # some signature keywords to distinguish dom comments from other comments.
    signature_keyword_list = [
        "NeXus",
        "GNU Lesser General Public",
        "Free Software Foundation",
        "Copyright (C)",
        "WITHOUT ANY WARRANTY",
    ]
    for keyword in signature_keyword_list:
        if keyword not in text:
            return False

    return True
