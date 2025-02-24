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
This file collects the functions for conversion from nxdl.xml to yaml version.
"""

# pylint: disable=too-many-lines

import re
import textwrap
from pathlib import Path
from typing import Callable, Dict, List

import lxml.etree as ET

from nyaml.helper import (
    NXDL_ATTRIBUTES_ATTRIBUTES,
    NXDL_FIELD_ATTRIBUTES,
    NXDL_GROUP_ATTRIBUTES,
    NXDL_LINK_ATTRIBUTES,
    clean_empty_lines,
    get_node_parent_info,
    get_yaml_escape_char_dict,
    is_copyright_comment,
    remove_namespace_from_tag,
)

DEPTH_SIZE = 2 * " "
CMNT_TAG = "!--"
CMNT_TAG_END = "--"
CMNT_START = "<!--"
CMNT_END = "-->"
DEFINITION_CATEGORIES = ("category: application", "category: base")


def separate_pi_comments(input_file):
    """Separate PI comments from ProcessesInstruction (PI).

    ProcessesInstruction refers xml element process and version
    Separate the comments that comes immediately after XML process instruction part,
    i.e. copyright comment part.
    """
    comments_list = []
    comment = []

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
        def_tag = "<definition"
        for line in lines:
            if CMNT_START in line:
                line = line.replace(CMNT_START, "")
                if CMNT_END in line:
                    line = line.replace(CMNT_END, "")
                    comments_list.append(line)
                else:
                    comment.append(line)
            elif CMNT_END in line and len(comment) > 0:
                comment.append(line.replace(CMNT_END, ""))
                comments_list.append("".join(comment))
                comment.clear()
            elif len(comment) > 0:
                comment.append(line)
            elif def_tag in line:
                break
    return comments_list


# Collected: https://dustinoprea.com/2019/01/22/python-parsing-xml-and-retaining-the-comments/
class _CommentedTreeBuilder(ET.TreeBuilder):
    def start(self, tag, attrs):
        super().start(tag=tag, attrs=attrs)

    def Comment(self, text):  # pylint: disable=invalid-name
        """Defining comment builder in TreeBuilder"""
        self.start(CMNT_TAG, {})
        self.data(text)
        self.end(CMNT_TAG_END)


def parse(filepath):
    """Parse xml function.

    Construct parser function for modified tree builder for including modified TreeBuilder
    and rebuilding XMLParser.
    """
    comments = separate_pi_comments(filepath)
    ctb = _CommentedTreeBuilder()
    xp_parser = ET.XMLParser(target=ctb, encoding="UTF-8")
    root = ET.parse(filepath, xp_parser)
    return comments, root


def handle_mapping_char(text, depth=-1, skip_n_line_on_top=False):
    """Check for escape character and replace by alternative character."""

    escape_char = get_yaml_escape_char_dict()
    for esc_key, val in escape_char.items():
        if esc_key in text:
            text = text.replace(esc_key, val)
    if not skip_n_line_on_top:
        if depth > 0:
            text = add_new_line_with_pipe_on_top(text, depth)
        else:
            raise ValueError("Need depth size to co-ordinate text line in yaml file.")
    return text


def add_new_line_with_pipe_on_top(text, depth):
    """Design docs block.

    Restructure the text by adding pipe '|' and '\n' char if ':' is found in text.
    """
    char = ":"
    if char in text:
        return "|" + "\n" + depth * DEPTH_SIZE + text
    return text


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class Nxdl2yaml:
    """Parse XML file and print a YML file."""

    def __init__(
        self,
        symbol_list: List[str],
        root_level_definition: List[str],
        root_level_doc="",
        root_level_symbols="",
    ):
        # updated part of yaml_dict
        self.found_definition = False
        self.root_level_doc = root_level_doc
        self.root_level_symbols = root_level_symbols
        self.root_level_definition = root_level_definition
        self.symbol_list = symbol_list
        self.include_comment = True
        self.pi_comments = None
        # NOTE: Here is how root_level_comments organised for storing comments
        # root_level_comment= {'root_doc': comment,
        #                      'symbols': comment,
        #       The 'symbol_doc_comments' list is for comments from all 'symbol doc'
        #                      'symbol_doc_comments' : [comments]
        #                      'symbol_list': [symbols],
        #       The 'symbol_comments' contains comments for 'symbols doc' and all 'symbol'
        #                      'symbol_comments': [comments]}
        self.root_level_comment: Dict[str, str] = {}

        self.optionality_keys = (
            "minOccurs",
            "maxOccurs",
            "optional",
            "recommended",
            "required",
        )
        # "Take care of general attributes. Note other choices may be allowed in the future"
        self.choice_allowed_attr = ()

    def print_yml(self, input_file, output_yml, verbose):
        """Parse an XML file provided as input and print a YML file."""
        output_file_path = Path(output_yml)
        if output_file_path.is_file():
            output_file_path.unlink()

        depth = 0

        self.pi_comments, root = parse(input_file)
        xml_tree = {"tree": root, "node": root}
        self.xmlparse(output_yml, xml_tree, depth, verbose)

    def handle_symbols(self, depth, node):
        """Handle symbols field and its childs symbol"""

        self.root_level_symbols = (
            f"{remove_namespace_from_tag(node.tag)}: "
            f"{node.text.strip() if node.text else ''}"
        )
        depth += 1
        last_comment = ""
        sbl_doc_cmnt_list = []
        # Comments that come above symbol tag
        symbol_cmnt_list = []
        for child in list(node):
            tag = remove_namespace_from_tag(child.tag)
            if tag == CMNT_TAG and self.include_comment:
                last_comment = self.convert_to_yaml_comment(depth, child.text)
            if tag == "doc":
                symbol_cmnt_list.append(last_comment)
                # The line below is for handling length of 'symbol_comments' and
                # 'symbol_doc_comments'. Otherwise print_root_level_info() gets inconsistency
                # over for the loop while writing comment on file
                sbl_doc_cmnt_list.append("")
                last_comment = ""
                self.symbol_list.append(
                    self.handle_not_root_level_doc(depth, text=child.text)
                )
            elif tag == "symbol":
                # place holder is symbol name
                symbol_cmnt_list.append(last_comment)
                last_comment = ""
                if "doc" in child.attrib:
                    self.symbol_list.append(
                        self.handle_not_root_level_doc(
                            depth, tag=child.attrib["name"], text=child.attrib["doc"]
                        )
                    )
                else:
                    for symbol_doc in list(child):
                        tag = remove_namespace_from_tag(symbol_doc.tag)
                        if tag == CMNT_TAG and self.include_comment:
                            last_comment = self.convert_to_yaml_comment(
                                depth, symbol_doc.text
                            )
                        if tag == "doc":
                            sbl_doc_cmnt_list.append(last_comment)
                            last_comment = ""
                            self.symbol_list.append(
                                self.handle_not_root_level_doc(
                                    depth,
                                    tag=child.attrib["name"],
                                    text=symbol_doc.text,
                                )
                            )
        self.store_root_level_comments("symbol_doc_comments", sbl_doc_cmnt_list)
        self.store_root_level_comments("symbol_comments", symbol_cmnt_list)

    def store_root_level_comments(self, holder, comment):
        """Store yaml text or section line and the comments inteded for that lines or section"""

        self.root_level_comment[holder] = comment

    def handle_definition(self, node):
        """Handle definition group and its attributes.

        NOTE: Here we try to store the order of the xml element attributes, so that we get
        the same order in nxdl from yaml.
        """
        keyword = ""
        # tmp_word for reseving the location
        tmp_word = "#xx#"
        attribs = node.attrib
        # for tracking the order of name and type
        keyword_order = -1
        for item in attribs:
            if "name" == item:
                keyword = keyword + attribs[item]
                if keyword_order == -1:
                    self.root_level_definition.append(tmp_word)
                    keyword_order = self.root_level_definition.index(tmp_word)
            elif "extends" == item:
                keyword = f"{keyword}({attribs[item]})"
                if keyword_order == -1:
                    self.root_level_definition.append(tmp_word)
                    keyword_order = self.root_level_definition.index(tmp_word)
            elif "schemaLocation" not in item and "extends" != item:
                text = f"{item}: {attribs[item]}"
                self.root_level_definition.append(text)
        self.root_level_definition[keyword_order] = f"{keyword}:"

    def handle_root_level_doc(self, node):
        """
        Handle the documentation field found at root level.
        """
        text = self.handle_not_root_level_doc(depth=0, text=node.text)
        self.root_level_doc = text

    def clean_and_organise_text(self, text, depth):
        """Reconstruct text from doc and comment.

        Cleaninig up unintentional and accidental empty lines and spaces.
        """
        # Handling empty doc
        if not text:
            text = ""
        else:
            text = handle_mapping_char(text, -1, True)
        if "\n" in text:
            # To remove '\n' with non-space character as it will be added before text.
            text = clean_empty_lines(text.split("\n"))
            text_tmp = []
            yaml_indent_n = len((depth + 1) * DEPTH_SIZE)

            # Find indentation in the first line of text having alphabet
            first_line_indent_n = 0
            for line in text:
                # Consider only the lines that has at least one non-space character
                # and skip starting lines of a text block are empty
                if len(line.lstrip()) != 0:
                    first_line_indent_n = len(line) - len(line.lstrip())
                    break
            # Taking care of doc like below:
            # <doc>Text lines
            # text continues</doc>
            # So no indentation at the start of doc. So doc group will come along general
            # alignment
            if first_line_indent_n == 0:
                first_line_indent_n = yaml_indent_n

            # for indent_diff -ve all lines will move left by the same amount
            # for indent_diff +ve all lines will move right by the same amount
            indent_diff = yaml_indent_n - first_line_indent_n
            # CHeck for first line empty if not keep first line empty

            for line in text:
                line_indent_n = 0
                # count first empty spaces without alphabet
                line_indent_n = len(line) - len(line.lstrip())
                line_indent_n = line_indent_n + indent_diff
                if line_indent_n < yaml_indent_n:
                    # if line still under yaml identation
                    text_tmp.append(yaml_indent_n * " " + line.strip())
                else:
                    text_tmp.append(line_indent_n * " " + line.strip())

            text = "\n" + "\n".join(text_tmp)

        elif text:
            text = "\n" + (depth + 1) * DEPTH_SIZE + text.strip()

        return text

    def check_and_handle_doc_xref_and_other_doc(self, text, indent):
        """Check for xref doc which comes as a block of text.

        The doc part below is the example how xref comes:
        '''
        This concept is related to term `<term>`_ of the <spec> standard.
        .. _<term>: <url>
        '''
        converter as
        '''
        <indent>  "xref:
        <indent>    xpec: <value>
        <indent>    erm: <value>
        <indent>    url: <value>"
        '''

        Parameters
        ----------
        text: str
            plain text.
        Returns
        -------
        str
            return part of doc as formatted
        """

        xref_key, spec_key, term_key, url_key = ("xref", "spec", "term", "url")
        spec, term, url = (None, None, None)
        matches = re.search(
            r"This concept is related to term `([^`:]+)`_ of the"
            r" (.*?) standard\.\s+\.\. _\1: ([^\s]+)",
            text,
        )
        if matches:
            term = matches.group(1)
            spec = matches.group(2)
            url = matches.group(3)
            indent = indent + DEPTH_SIZE  # see example in func doc
            return (
                f"{indent}{xref_key}:\n{indent + DEPTH_SIZE}{spec_key}: {spec}"
                f"\n{indent + DEPTH_SIZE}{term_key}"
                f": {term}\n{indent + DEPTH_SIZE}{url_key}: {url}"
            ), True
        return text, False

    # pylint: disable=too-many-branches, too-many-locals
    def handle_not_root_level_doc(self, depth, text, tag="doc", file_out=None):
        """Handle docs field of group and field but not root.

        Handle docs field along the yaml file. In this function we also tried to keep
        the track of indentation. E.g. the below doc block.
            * Topic name
                Description of topic
        """
        if "}" in tag:
            tag = remove_namespace_from_tag(tag)
        indent = depth * DEPTH_SIZE
        text = self.clean_and_organise_text(text, depth)  # starts with '\n'
        docs = re.split(r"\n\s*\n", text)
        parts = []

        # Add links to previous docstring
        for doc in docs:
            link_match = re.match(r"\s*\.\. _.*", doc)
            if link_match is not None and len(parts) > 0:
                parts[-1] += doc
            else:
                parts.append(doc)

        modified_docs = []
        xref_in_doc = False
        for doc_part in parts:
            if not doc_part.isspace():
                mod_doc, xref_present = self.check_and_handle_doc_xref_and_other_doc(
                    doc_part, indent
                )
                xref_in_doc = xref_in_doc or xref_present
                modified_docs.append(mod_doc)
        # Note on doc example:
        # doc:
        #  - |
        #   text
        #  - |
        #   xref:
        #       spec:
        #       term:
        if len(modified_docs) == 1:
            doc_str = f"{indent}{tag}: |{modified_docs[0]}\n"
        elif len(modified_docs) > 1 and xref_in_doc:
            doc_str = f"{indent}{tag}:\n"
            for mod_doc in modified_docs:
                if not re.match(
                    r"^\s*\n", mod_doc
                ):  # if not starts with 'spaces and/or \n'
                    mod_doc = "\n" + mod_doc
                # doc_str = f"{doc_str}{indent} - |\n{textwrap.indent(mod_doc, indent+'  ')}\n"
                doc_str = f"{doc_str}{indent}- |{textwrap.indent(mod_doc, '')}\n"
        else:
            doc_str = f"{indent}{tag}: |{text}\n"

        if file_out:
            file_out.write(doc_str)
            return None
        return doc_str

    def write_out(self, indent, text, file_out):
        """
        Write text line in output file.
        """
        line_string = f"{indent}{text.rstrip()}\n"
        file_out.write(line_string)

    def print_root_level_doc(self, file_out):
        """Print at the root level of YML file the general documentation field found in XML file"""
        indent = 0 * DEPTH_SIZE

        text = self.root_level_comment.get("root_doc")
        if text:
            self.write_out(indent, text, file_out)

        text = self.root_level_doc
        self.write_out(indent, text, file_out)
        self.root_level_doc = ""

    def convert_to_yaml_comment(self, depth, text):
        """
        Convert into yaml comment by adding exta '#' char in front of comment lines
        """
        # To store indentation text from comment
        lines = self.clean_and_organise_text(text, depth).split("\n")
        indent = DEPTH_SIZE * depth
        mod_lines = []
        for line in lines:
            line = line.strip()
            if line:
                if line[0] != "#":
                    line = "# " + line
                mod_lines.append(line)
        # The starting '\n' to keep multiple comments separate
        return "\n" + "\n".join(map(lambda line: indent + line, mod_lines))

    def print_root_level_info(self, depth, file_out):
        """
        Print at the root level of YML file \
        the information stored as definition attributes in the XML file
        """
        if depth < 0:
            raise ValueError("Somthing wrong with indentation in root level.")

        has_category = False
        for def_line in self.root_level_definition:
            if def_line in DEFINITION_CATEGORIES:
                self.write_out(indent=0 * DEPTH_SIZE, text=def_line, file_out=file_out)
                has_category = True

        if not has_category:
            raise ValueError(
                "Definition dose not get any category from 'base or application'."
            )
        self.print_root_level_doc(file_out)
        text = self.root_level_comment.get("symbols", "")
        if text:
            indent = depth * DEPTH_SIZE
            self.write_out(indent, text, file_out)
        if self.root_level_symbols:
            self.write_out(
                indent=0 * DEPTH_SIZE, text=self.root_level_symbols, file_out=file_out
            )
            # symbol_list include 'symbols doc', and all 'symbol'
            for ind, symbol in enumerate(self.symbol_list):
                # Taking care of comments that come on top of 'symbols doc' and 'symbol'
                if (
                    "symbol_comments" in self.root_level_comment
                    and self.root_level_comment["symbol_comments"][ind] != ""
                ):
                    indent = depth * DEPTH_SIZE
                    self.write_out(
                        indent,
                        self.root_level_comment["symbol_comments"][ind],
                        file_out,
                    )
                if (
                    "symbol_doc_comments" in self.root_level_comment
                    and self.root_level_comment["symbol_doc_comments"][ind] != ""
                ):
                    indent = depth * DEPTH_SIZE
                    self.write_out(
                        indent,
                        self.root_level_comment["symbol_doc_comments"][ind],
                        file_out,
                    )

                self.write_out(indent=(0 * DEPTH_SIZE), text=symbol, file_out=file_out)
        indent = depth * DEPTH_SIZE
        # Take care copyright doc string
        for comment in self.pi_comments:
            if comment and not is_copyright_comment(comment):
                self.write_out(
                    indent, self.convert_to_yaml_comment(depth, comment), file_out
                )
        if self.root_level_definition:
            # Store NXname for writing at end of definition attributes
            nx_name = ""
            for defs in self.root_level_definition:
                if "NX" in defs and defs[-1] == ":":
                    nx_name = defs
                    continue
                if defs in ("category: application", "category: base"):
                    continue
                self.write_out(indent=0 * DEPTH_SIZE, text=defs, file_out=file_out)
            self.write_out(indent=0 * DEPTH_SIZE, text=nx_name, file_out=file_out)
        self.found_definition = False

    def handle_exists(self, exists_dict, key, val):
        """
        Create exist component as folows:

        {'min' : value for min,
         'max' : value for max,
         'optional' : value for optional}

        This is created separately so that the keys stays in order.
        """
        if not val:
            val = ""
        else:
            val = str(val)
        if "minOccurs" == key:
            exists_dict["minOccurs"] = ["min", val]
        elif "maxOccurs" == key:
            exists_dict["maxOccurs"] = ["max", val]
        elif "optional" == key:
            exists_dict["optional"] = ["optional", val]
        elif "recommended" == key:
            exists_dict["recommended"] = ["recommended", val]
        elif "required" == key:
            exists_dict["required"] = ["required", val]

    # pylint: disable=too-many-branches
    def handle_group_or_field(self, depth, node, file_out):
        """Handle all the possible attributes that come along a field or group"""

        name_type = ""
        node_attr = node.attrib
        rm_key_list = []
        # Maintain order: name and type in form name(type) or (type)name that come first
        for key, val in node_attr.items():
            if key == "name":
                name_type = name_type + val
                rm_key_list.append(key)
            elif key == "type":
                name_type = f"{name_type}({val})"
                rm_key_list.append(key)
        if not name_type:
            raise ValueError(
                f"No 'name' or 'type' has been found. But, 'group' or 'field' "
                f"must have at least a name.We have attributes:  {node_attr}"
            )
        indent = depth * DEPTH_SIZE
        file_out.write(f"{indent}{name_type}:\n")

        for key in rm_key_list:
            del node_attr[key]

        # tmp_dict intended to preserve order of attributes
        tmp_dict = {}
        exists_dict = {}
        for key, val in node_attr.items():
            # Check for any unwanted attributes
            self.check_for_unwanted_attributes(node=node)
            # As both 'minOccurs', 'maxOccurs' and optionality move to the 'exists'
            if key in self.optionality_keys:
                if "exists" not in tmp_dict:
                    tmp_dict["exists"] = []
                self.handle_exists(exists_dict, key, val)
            elif key == "units":
                tmp_dict["unit"] = str(val)
            else:
                tmp_dict[key] = str(val)

        if exists_dict:
            for key, val in exists_dict.items():
                if key in ["minOccurs", "maxOccurs"]:
                    tmp_dict["exists"] = tmp_dict["exists"] + val
                elif key in ["optional", "recommended", "required"]:
                    tmp_dict["exists"] = key

        depth_ = depth + 1
        for key, val in tmp_dict.items():
            # Increase depth size inside handle_map...() for writing text with one
            # more indentation.
            file_out.write(
                f"{depth_ * DEPTH_SIZE}{key}: "
                f"{handle_mapping_char(val, depth_ + 1, False)}\n"
            )

    def check_for_unwanted_attributes(self, node, allowed_attributes_li=None, tag=None):
        """Check for any attributes that NeXus does not allow."""
        node_tag = remove_namespace_from_tag(node.tag)
        if node_tag == "field":
            for key in node.attrib.keys():
                if key not in NXDL_FIELD_ATTRIBUTES:
                    raise ValueError(
                        f"Field has an unwanted attribute {key}."
                        f"NeXus field allows attributes from {NXDL_FIELD_ATTRIBUTES}"
                    )
        elif node_tag == "group":
            for key in node.attrib.keys():
                if key not in NXDL_GROUP_ATTRIBUTES:
                    raise ValueError(
                        f"Attribute has an unwanted attribute {key}."
                        f"NeXus attribute allows attributes from {NXDL_GROUP_ATTRIBUTES}"
                    )
        elif node_tag == tag:
            for key in node.attrib.keys():
                if key not in allowed_attributes_li:
                    raise ValueError(
                        f"{tag.capitalized()} has an unwanted attribute {key}."
                        f"NeXus {tag.capitalized()} allows attributes from {allowed_attributes_li}"
                    )

    # pylint: disable=too-many-branches, too-many-locals, too-many-statements
    def handle_dimensions(self, depth, node, file_out):
        """
        Handle instances of dimensionsType and its child nodes.

        tests/data/NXdimensionsType.yaml documents the choices
        """
        # analyze first the entire sub-graph behind the dimensionsType element
        yml_dim_dct = {}
        # dimensionsType, rank if present
        for attr, val in node.attrib.items():
            if not isinstance(val, dict):
                if attr in ["rank"]:
                    # indent = (depth + 1) * DEPTH_SIZE
                    yml_dim_dct["rank"] = val
                    break
                # rank is the only allowed attribute of a dimensionsType node
                # see https://manual.nexusformat.org/nxdl_desc.html#dimensionstype
                # for why doc needs to be defined as an XML element instead of an
                # attribute, i.e. using this
                # <dimensions rank="someint" doc="somedocstring"/> is invalid
                # instead, refactor that NeXus class to
                # <dimensions>
                #   <doc>somedocstring</doc>

        # dimensionsType, docstring, if present
        for child in list(node):
            tag = remove_namespace_from_tag(child.tag)
            if tag == "doc":
                yml_dim_dct["doc"] = self.handle_not_root_level_doc(
                    depth + 1, child.text, "doc", None
                )
                break  # dimensionsType can have only one top-level docstring

        # individual dimensionsType dim elements - the individual dimensions - if present
        for child in list(node):
            tag = remove_namespace_from_tag(child.tag)
            child_attrs = child.attrib
            # taking care of index and value attributes
            if tag == "dim":
                # taking care of index and value in format [[index, value]]
                if "index" in child_attrs:
                    idx_val = child_attrs.pop("index", "")
                    if idx_val != "":
                        yml_dim_dct[idx_val] = {}
                        for child_attrs_key, child_attrs_val in child_attrs.items():
                            if child_attrs_key in ["value", "required"]:
                                yml_dim_dct[idx_val][child_attrs_key] = child_attrs_val
                            elif child_attrs_key in ["ref", "incr", "refindex"]:
                                # deprecated !
                                yml_dim_dct[idx_val][child_attrs_key] = child_attrs_val
                            else:
                                raise ValueError(
                                    f"Found incorrect dim child attribute {child_attrs_key}, {child_attrs_val} !"
                                )
                    else:
                        raise ValueError(
                            f"Found incorrect dim child that has no index attribute !"
                        )

        # perform I/O based on the cases analyzed
        yml_dim_dct_keys = list(yml_dim_dct)
        indent = depth * DEPTH_SIZE
        if set(yml_dim_dct_keys) in [{"rank"}, {"doc", "rank"}]:
            # rank only notation
            file_out.write(f"{indent}dimensions:\n")
            for key, val in yml_dim_dct.items():
                if key == "doc":
                    file_out.write(f"{val}")
                    continue
                file_out.write(f"{indent}{DEPTH_SIZE}{key}: {val}\n")
        else:
            use_shorthand_notation = True  # try to falsify this default assumption
            for key, obj in yml_dim_dct.items():
                if isinstance(obj, dict):  # inside an individual dimension
                    for attr_key, attr_val in obj.items():
                        if attr_key in ["ref", "required", "incr", "refindex"]:
                            use_shorthand_notation = False
                            break
            if use_shorthand_notation:  # shorthand_explicit_rank_new
                file_out.write(f"{indent}dimensions:\n")
                dim_index_value = []
                for key, obj in yml_dim_dct.items():
                    if key == "rank":  # "doc"
                        if isinstance(obj, str):
                            file_out.write(f"{indent}{' ' * 2}{key}: {obj}\n")
                    elif key == "doc":
                        if isinstance(obj, str):
                            file_out.write(f"{obj}")
                    else:
                        if isinstance(obj, dict):  # inside an individual dimension
                            for attr_key, attr_val in obj.items():
                                # will be in order now because numbered indices!
                                if attr_key == "value" and attr_val != "":
                                    dim_index_value.append(attr_val)
                if len(dim_index_value) > 1:
                    file_out.write(
                        f"{indent}{' ' * 2}dim: ({', '.join(dim_index_value)})\n"
                    )
                elif len(dim_index_value) == 1:
                    file_out.write(f"{indent}{' ' * 2}dim: ({dim_index_value[0]},)\n")
            else:  # full syntax
                file_out.write(f"{indent}dimensions:\n")
                for key, obj in yml_dim_dct.items():
                    if key == "rank":  # "doc"
                        if isinstance(obj, str):
                            file_out.write(f"{indent}{' ' * 2}{key}: {obj}\n")
                    elif key == "doc":
                        if isinstance(obj, str):
                            file_out.write(f"{obj}")
                # two loops to assure that doc and rank are written before
                # the individual explicit dimension dicts
                for key, obj in sorted(yml_dim_dct.items()):
                    if key not in ["rank", "doc"] and isinstance(obj, dict):
                        if (
                            sum(
                                1
                                for attr_key, attr_val in obj.items()
                                if attr_val != ""
                            )
                            > 0
                        ):
                            file_out.write(f"{indent}{' ' * 2}{key}:\n")
                            for attr_key, attr_val in obj.items():
                                if attr_val != "":
                                    file_out.write(
                                        f"{indent}{' ' * 4}{attr_key}: {attr_val}\n"
                                    )

    def handle_enumeration(self, depth, node, file_out):
        """
        Handle the enumeration field parsed from the XML file.

        - If enumeration items contain a <doc> field, they will be stored as child fields.
        - If no docs are provided, items will be stored in a list format.
        - If the enumeration is open, an 'open_enum' key will be included.
        """
        indent = depth * DEPTH_SIZE
        tag = remove_namespace_from_tag(node.tag)
        attributes = node.attrib
        open_enum = attributes.get("open", "false").lower() == "true"
        node_children = list(node)

        check_doc = any(list(child) for child in node_children)

        file_out.write(f"{indent}{tag}:")

        if check_doc:
            file_out.write("\n")
            if open_enum:
                file_out.write(f"{indent + DEPTH_SIZE}open_enum: True\n")
            for child in node_children:
                child_tag = remove_namespace_from_tag(child.tag)
                if child_tag == "item":
                    item_indent = indent + DEPTH_SIZE
                    value = child.attrib["value"]
                    if value.startswith("[") and value.endswith("]"):
                        value = f'"{value}"'
                    file_out.write(f"{item_indent}{value}:\n")

                    doc_depth = depth + 2
                    for item_doc in list(child):
                        if remove_namespace_from_tag(item_doc.tag) == "doc":
                            self.handle_not_root_level_doc(
                                doc_depth, item_doc.text, item_doc.tag, file_out
                            )
                        if (
                            remove_namespace_from_tag(item_doc.tag) == CMNT_TAG
                            and self.include_comment
                        ):
                            self.handle_comment(doc_depth, item_doc, file_out)
                elif child_tag == CMNT_TAG and self.include_comment:
                    self.handle_comment(depth + 1, child, file_out)
        else:
            enum_with_comment = False
            enum_list = []
            for child in node_children:
                child_tag = remove_namespace_from_tag(child.tag)
                if child_tag == "item":
                    enum_list.append(child.attrib["value"])
                elif child_tag == CMNT_TAG and self.include_comment:
                    file_out.write("\n")
                    self.handle_comment(depth + 1, child, file_out)
                    # If there is a comment, we need to use the long notation with "items:"
                    enum_with_comment = True

            if open_enum:
                file_out.write(f"{indent + DEPTH_SIZE}open_enum: True\n")

            if open_enum or enum_with_comment:
                file_out.write(
                    f"{indent + DEPTH_SIZE}{'items'}: [{', '.join(enum_list)}]\n"
                )

            else:
                # Short notation as list if there is no comment or open enum
                file_out.write(f" [{', '.join(enum_list)}]\n")

    def handle_attributes(self, depth, node, file_out):
        """Handle the attributes parsed from the xml file"""

        name = ""
        nm_attr = "name"
        node_attr = node.attrib
        # Maintain order: name and type in form name(type) or (type)name that come first
        name = node_attr.pop(nm_attr, "")
        if not name:
            raise ValueError("Attribute must have a name key.")

        indent = depth * DEPTH_SIZE
        escapesymbol = r"\@"

        tmp_dict = {}
        exists_dict = {}
        for key, val in node_attr.items():
            if key not in NXDL_ATTRIBUTES_ATTRIBUTES:
                raise ValueError(
                    f"An attribute ({key}) has been found that is not allowed."
                    f"The allowed attr is {NXDL_ATTRIBUTES_ATTRIBUTES}."
                )
            # As both 'minOccurs', 'maxOccurs' and optionality move to the 'exists'
            if key in self.optionality_keys:
                if "exists" not in tmp_dict:
                    tmp_dict["exists"] = []
                self.handle_exists(exists_dict, key, val)
            elif key == "units":
                tmp_dict["unit"] = val
            else:
                tmp_dict[key] = val

        datatype = tmp_dict.get("type")

        if datatype:
            name_txt = f"{indent}{escapesymbol}{name}({datatype}):\n"
            del tmp_dict["type"]
        else:
            name_txt = f"{indent}{escapesymbol}{name}:\n"

        file_out.write(name_txt)

        has_min_max = False
        has_opt_reco_requ = False
        if exists_dict:
            for key, val in exists_dict.items():
                if key in ["minOccurs", "maxOccurs"]:
                    tmp_dict["exists"] = tmp_dict["exists"] + val
                    has_min_max = True
                elif key in ["optional", "recommended", "required"]:
                    tmp_dict["exists"] = key
                    has_opt_reco_requ = True
        if has_min_max and has_opt_reco_requ:
            raise ValueError(
                "Optionality 'exists' can take only either from ['minOccurs',"
                " 'maxOccurs'] or from ['optional', 'recommended', 'required']"
                ". But not from both of the groups together. Please check in"
                " attributes"
            )

        depth_ = depth + 1
        for key, val in tmp_dict.items():
            # Increase depth size inside handle_map...() for writing text with one
            # more indentation.
            file_out.write(
                f"{depth_ * DEPTH_SIZE}{key}: "
                f"{handle_mapping_char(val, depth_ + 1, False)}\n"
            )

    def handle_link(self, depth, node, file_out):
        """Handle link elements of nxdl"""

        node_attr = node.attrib
        # Handle special cases
        name = node_attr.pop("name", "")
        if name:
            indent = depth * DEPTH_SIZE
            file_out.write(f"{indent}{name}(link):\n")

        depth_ = depth + 1
        # Handle general cases
        for attr_key, val in node_attr.items():
            if attr_key in NXDL_LINK_ATTRIBUTES:
                indent = depth_ * DEPTH_SIZE
                file_out.write(f"{indent}{attr_key}: {val}\n")
            else:
                raise ValueError(
                    f"An unexpected attribute '{attr_key}' of link has found."
                    f"At this moment the allowed keys are {NXDL_LINK_ATTRIBUTES}"
                )

    def handle_choice(self, depth, node, file_out):
        """
        Handle choice element which is a parent node of group.
        """

        node_attr = node.attrib
        name = node_attr.pop("name", "")
        # Handle special casees
        if name:
            indent = depth * DEPTH_SIZE
            file_out.write(f"{indent}{name}(choice): \n")

        depth_ = depth + 1
        # Take care of attributes of choice element, attributes may come in future.
        for attr in node_attr.items():
            if attr in self.choice_allowed_attr:
                indent = depth_ * DEPTH_SIZE
                value = node_attr[attr]
                file_out.write(f"{indent}{attr}: {value}\n")
            else:
                raise ValueError(
                    f"An unexpected attribute '{attr}' of 'choice' has been found."
                    f"At this moment allowed attributes for choice {self.choice_allowed_attr}"
                )

    def handle_comment(self, depth, node, file_out):
        """
        Collect comment element and pass to write_out function
        """
        indent = depth * DEPTH_SIZE
        text = self.convert_to_yaml_comment(depth, node.text)
        self.write_out(indent, text, file_out)

    def recursion_in_xml_tree(self, depth, xml_tree, output_yml, verbose):
        """
            Descend lower level in xml tree. If we are in the symbols branch, the recursive
        behaviour is not triggered as we already handled the symbols' children.
        """

        tree = xml_tree["tree"]
        node = xml_tree["node"]
        for child in list(node):
            xml_tree_children = {"tree": tree, "node": child}
            self.xmlparse(output_yml, xml_tree_children, depth, verbose)

    # pylint: disable=too-many-branches, too-many-statements
    def xmlparse(self, output_yml, xml_tree, depth, verbose):
        """
        Main method of the nxdl2yaml converter.
        It parses XML tree, then prints recursively each level of the tree
        """
        tree = xml_tree["tree"]
        node = xml_tree["node"]
        if verbose:
            if isinstance(node.tag, Callable):
                print(f"Node tag: {node.tag}\n")
                print(f"Node text: {node.text}\n")
            else:
                print(f"Node tag: {remove_namespace_from_tag(node.tag)}\n")
                print(f"Attributes: {node.attrib}\n")
        with open(output_yml, "a", encoding="utf-8") as file_out:
            # too much file I/O, this with statement is in the recursion build
            # the entire yaml dictionary nest in main memory and dump thereafter
            tag = remove_namespace_from_tag(node.tag)
            if tag == "definition":
                self.found_definition = True
                self.handle_definition(node)
                # Taking care of root level doc and symbols
                remove_cmnt_n = None
                last_comment = ""
                for child in node:
                    tag_tmp = remove_namespace_from_tag(child.tag)
                    if tag_tmp == CMNT_TAG and self.include_comment:
                        last_comment = self.convert_to_yaml_comment(depth, child.text)
                        remove_cmnt_n = child
                    if tag_tmp == "doc":
                        self.store_root_level_comments("root_doc", last_comment)
                        last_comment = ""
                        self.handle_root_level_doc(child)
                        node.remove(child)
                        if remove_cmnt_n is not None:
                            node.remove(remove_cmnt_n)
                            remove_cmnt_n = None
                    if tag_tmp == "symbols":
                        self.store_root_level_comments("symbols", last_comment)
                        last_comment = ""
                        self.handle_symbols(depth, child)
                        node.remove(child)
                        if remove_cmnt_n is not None:
                            node.remove(remove_cmnt_n)
                            remove_cmnt_n = None

            if tag == "doc" and depth != 1:
                parent = get_node_parent_info(tree, node)[0]
                doc_parent = remove_namespace_from_tag(parent.tag)
                if doc_parent != "item":
                    self.handle_not_root_level_doc(
                        depth, text=node.text, tag=node.tag, file_out=file_out
                    )

            recurse_again = True
            if self.found_definition is True and self.root_level_doc:
                self.print_root_level_info(depth, file_out)
            # End of print root-level definitions in file
            if tag in ("field", "group") and depth != 0:
                self.handle_group_or_field(depth, node, file_out)
            if tag == ("attribute"):
                self.handle_attributes(depth, node, file_out)
            if tag == ("enumeration"):
                self.handle_enumeration(depth, node, file_out)
                recurse_again = False
            if tag == ("dimensions"):
                # self.handle_dimension(depth, node, file_out)
                self.handle_dimensions(depth, node, file_out)
                recurse_again = False
            if tag == ("link"):
                self.handle_link(depth, node, file_out)
            if tag == ("choice"):
                self.handle_choice(depth, node, file_out)
            if tag == CMNT_TAG and self.include_comment:
                self.handle_comment(depth, node, file_out)

        if recurse_again is True:
            depth += 1
            # Write nested nodes
            self.recursion_in_xml_tree(depth, xml_tree, output_yml, verbose)
