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
Creates an instantiated NXDL schema XML tree by walking the dictionary nest
"""

import datetime
import os
import pathlib
import re
import textwrap
import warnings
from typing import Optional, Union
from urllib.parse import unquote

import lxml.etree as ET
import yaml
from yaml.scanner import ScannerError

from nyaml.comment_collector import CommentCollector
from nyaml.helper import (
    YAML_ATTRIBUTES_ATTRIBUTES,
    YAML_FIELD_ATTRIBUTES,
    YAML_GROUP_ATTRIBUTES,
    YAML_LINK_ATTRIBUTES,
    LineLoader,
    clean_empty_lines,
    get_yaml_escape_char_reverter_dict,
    is_copyright_comment,
    nx_name_type_resolving,
    remove_namespace_from_tag,
)

DOM_COMMENT = (
    "# NeXus - Neutron and X-ray Common Data Format\n"
    "#\n"
    "# Copyright (C) __COPYRIGHT_YEAR__ "
    "NeXus International Advisory Committee (NIAC)\n"
    "#\n"
    "# This library is free software; you can redistribute it and/or\n"
    "# modify it under the terms of the GNU Lesser General Public\n"
    "# License as published by the Free Software Foundation; either\n"
    "# version 3 of the License, or (at your option) any later version.\n"
    "#\n"
    "# This library is distributed in the hope that it will be useful,\n"
    "# but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
    "# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU\n"
    "# Lesser General Public License for more details.\n"
    "#\n"
    "# You should have received a copy of the GNU Lesser General Public\n"
    "# License along with this library; if not, write to the Free Software\n"
    "# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA\n"
    "#\n"
    "# For further information, see http://www.nexusformat.org\n"
)
DEPTH_SIZE = 4 * " "
# Initialised in yml_reader() funtion
COMMENT_BLOCKS: CommentCollector
CATEGORY = ""  # Definition would be either 'base' or 'application'


def get_nxdl_copyright_license(nxdl_file):
    """Extract the license part from nxdl file if nxdl file as input."""
    comment_start_sym = "^<!--"
    comment_end_sym = "-->\n+$"
    is_comment_start = False
    is_comment_end = False

    if os.path.isfile(nxdl_file):
        with open(nxdl_file, "r", encoding="utf-8") as nxdl_file_obj:
            nxdl_lines = nxdl_file_obj.readlines()
            comment = ""
            for line in nxdl_lines:
                # Find a single comment
                if re.match(comment_start_sym, line):
                    is_comment_start = True
                elif is_comment_start:
                    if re.match(comment_end_sym, line):
                        is_comment_end = True
                    else:
                        comment += line
                # Varifiy for copyright comment
                if is_comment_start and is_comment_end:
                    if is_copyright_comment(comment):
                        return comment
                    else:
                        comment = ""
                        is_comment_start = False
                        is_comment_end = False
        return ""


# pylint: disable=too-many-lines
def set_copyright_text(nxdl_copyright_license=""):
    """Set copyright text from nxdl file or create from current year."""

    global DOM_COMMENT
    if nxdl_copyright_license:
        DOM_COMMENT = nxdl_copyright_license
    else:
        copyright_year = (
            f"{datetime.datetime.now().year}-{datetime.datetime.now().year}"
        )

        DOM_COMMENT = DOM_COMMENT.replace("__COPYRIGHT_YEAR__", copyright_year)


def yml_reader(inputfile):
    """
    This function launches the LineLoader class.
    It parses the yaml in a dict and extends it with line tag keys for each key of the dict.
    """
    global COMMENT_BLOCKS
    with open(inputfile, "r", encoding="utf-8") as plain_text_yaml:
        loader = LineLoader(plain_text_yaml)
        loaded_yaml = loader.get_single_data()
    COMMENT_BLOCKS = CommentCollector(inputfile, loaded_yaml)
    COMMENT_BLOCKS.extract_all_comment_blocks()

    if "category" not in loaded_yaml.keys():
        raise ValueError(
            "All definitions should be either 'base' or 'application' category. "
            "No category has been found."
        )
    global CATEGORY
    CATEGORY = loaded_yaml["category"]
    return loaded_yaml


def check_for_default_attribute_and_value(xml_element):
    """Check for default attribute for NeXus concepts.

    NeXus Groups, fields and attributes might have xml default attributes and values that must
    come. For example: 'optional' which is 'true' by default for base class and false otherwise.
    """

    # base: Default attributes and value for all elements of base class except dimension element
    base_attr_to_val = {"optional": "true"}

    # application: Default attributes and value for all elements of application class except
    # dimension element
    application_attr_to_val = {"optional": "false"}

    # Default attributes and value for dimension element
    base_dim_attr_to_val = {"required": "false"}
    application_dim_attr_to_val = {"required": "true"}

    # Eligible tag for default attr and value
    eligible_tag = ["group", "field", "attribute"]

    def set_default_attribute(xml_elem, default_attr_to_val):
        for deflt_attr, deflt_val in default_attr_to_val.items():
            if (
                deflt_attr not in xml_elem.attrib
                and "maxOccurs" not in xml_elem.attrib
                and "minOccurs" not in xml_elem.attrib
                and "recommended" not in xml_elem.attrib
            ):
                xml_elem.set(deflt_attr, deflt_val)

    for child in list(xml_element):
        # skipping comment 'function' that mainly collect comment from yaml file.
        if not isinstance(child.tag, str):
            continue
        tag = remove_namespace_from_tag(child.tag)

        if tag == "dim" and CATEGORY == "base":
            set_default_attribute(child, base_dim_attr_to_val)
        if tag == "dim" and CATEGORY == "application":
            set_default_attribute(child, application_dim_attr_to_val)
        if tag in eligible_tag and CATEGORY == "base":
            set_default_attribute(child, base_attr_to_val)
        if tag in eligible_tag and CATEGORY == "application":
            set_default_attribute(child, application_attr_to_val)
        check_for_default_attribute_and_value(child)


def yml_reader_nolinetag(inputfile):
    """
    pyyaml based parsing of yaml file in python dict
    """
    with open(inputfile, "r", encoding="utf-8") as stream:
        parsed_yaml = yaml.safe_load(stream)
    return parsed_yaml


def check_for_skipped_attributes(component, value, allowed_attr=None, verbose=False):
    """
    Check for any attributes have been skipped or not.
    NOTE: We should keep in mind about 'doc'
    """
    block_tag = ["enumeration"]
    if value:
        for attr, val in value.items():
            if attr == "doc":
                continue
            if "__line__" in attr or attr in block_tag:
                continue
            line_number = f"__line__{attr}"
            if verbose:
                print(f"__line__ : {value[line_number]}")
            if (
                not isinstance(val, dict)
                and "\\@" not in attr
                and attr not in allowed_attr
                and "NX" not in attr
                and val
            ):
                raise ValueError(
                    f"An attribute '{attr}' in part '{component}' has been found"
                    f". Please check around line '{value[line_number]}. At this "
                    f"time, the allowed attributes are {allowed_attr}."
                )


def format_nxdl_doc(string):
    """NeXus format for doc string"""
    string = check_for_mapping_char_other(string)
    string_len = 80
    if "\n" not in string:
        if len(string) > string_len:
            wrapped = textwrap.TextWrapper(
                width=string_len, break_long_words=False, replace_whitespace=False
            )
            string = "\n".join(wrapped.wrap(string))
        formatted_doc = "\n" + f"{string}"
    else:
        text_lines = string.split("\n")
        text_lines = clean_empty_lines(text_lines)
        formatted_doc = "\n" + "\n".join(text_lines)
    if not formatted_doc.endswith("\n"):
        formatted_doc += "\n"
    return formatted_doc.expandtabs(4)


def check_for_mapping_char_other(text):
    """
    Check for mapping char \':\' which does not be passed through yaml library.
    Then replace it by ':'.
    """
    if not text:
        text = ""
    text = str(text)
    if text == "True":
        text = "true"
    if text == "False":
        text = "false"
    # Some escape char is not valid in yaml libray which is written while writing
    # yaml file. In the time of writing nxdl revert to that escape char.
    escape_reverter = get_yaml_escape_char_reverter_dict()
    for key, val in escape_reverter.items():
        if key in text:
            text = text.replace(key, val)
    return text.strip()


def handle_each_part_doc(text):
    """Check and handle if the text is corresponds to xref or plain doc.

    In nyaml doc the entire documentation may come in list of small docs.
    one doc string might be as follows:
    '''
    xref:
        spec: <spec>
        term: <term>
        url: <url>
    '''

    which has to be formatted as
    '''
    This concept is related to term `<term>`_ of the <spec> standard.
    .. _<term>: <url>


    Parameters
    ----------
    text : string
        String that looks like yaml notaion.

    return
    ------
    Formated text
    """

    clean_txt = text.strip()

    if not clean_txt.startswith("xref:"):
        return format_nxdl_doc(check_for_mapping_char_other(clean_txt)).strip()

    no_lines = len(clean_txt.splitlines())
    try:
        xref_dict = yaml.safe_load(clean_txt)
    except ScannerError as scan_err:
        raise ValueError(
            "Found invalid xref. Please make sure that your xref entries are valid yaml."
        ) from scan_err
    xref_entries = xref_dict.get("xref", {})

    if no_lines != len(xref_entries) + 1:
        raise ValueError("Invalid xref. It contains nested or duplicate keys.")

    if no_lines > 4:
        raise ValueError("Invalid xref. Too many keys.")

    for key in xref_entries:
        if key not in ("term", "spec", "url"):
            raise ValueError(
                f"Invalid xref key `{key}`. Must be one of `term`, `spec` or `url`."
            )

    return (
        f"This concept is related to term `{xref_entries.get('term', 'NO TERM')}`_ "
        f"of the {xref_entries.get('spec', 'NO TERM')} standard.\n\n"
        f".. _{xref_entries.get('term', 'NO SPECIFICATION')}: "
        f"{xref_entries.get('url', 'NO URL')}"
    )


def xml_handle_doc(obj, value: Union[str, list], line_number=None, line_loc=None):
    """This function creates a 'doc' element instance, and appends it to an existing element"""
    # global comment_bolcks
    doc_elemt = ET.SubElement(obj, "doc")
    text = ""
    if isinstance(value, list):
        for doc_part in value:
            text = text + "\n" + handle_each_part_doc(doc_part) + "\n"
    else:
        text = text + "\n" + handle_each_part_doc(value) + "\n"
    # To keep the doc middle of doc tag.
    doc_elemt.text = text
    if line_loc is not None and line_number is not None:
        xml_handle_comment(obj, line_number, line_loc, doc_elemt)


def xml_handle_units(obj, value):
    """This function creates a 'units' element instance, and appends it to an existing element"""
    obj.set("units", str(value))


# pylint: disable=too-many-branches
def xml_handle_exists(dct, obj, keyword, value):
    """
    This function creates an 'exists' element instance, and appends it to an existing element
    """
    line_number = f"__line__{keyword}"
    assert value is not None, (
        f"Line {dct[line_number]}: exists argument must not be None !"
    )
    if isinstance(value, list):
        if len(value) == 4:
            if value[0] == "min" and value[2] == "max":
                obj.set("minOccurs", str(value[1]))
                if str(value[3]) != "infty":
                    obj.set("maxOccurs", str(value[3]))
                else:
                    obj.set("maxOccurs", "unbounded")
            elif value[0] == "max" and value[2] == "min":
                if str(value[1]) != "infty":
                    obj.set("maxOccurs", str(value[1]))
                else:
                    obj.set("maxOccurs", "unbounded")
                obj.set("minOccurs", str(value[3]))
            else:
                raise ValueError(
                    f"Line {dct[line_number]}: exists keyword"
                    f"needs to go either with an optional [recommended] list with two "
                    f"entries either [min, <uint>] or [max, <uint>], or a list of four "
                    f"entries [min, <uint>, max, <uint>] !"
                )
        elif len(value) == 2 and value[0] == "min":
            obj.set("minOccurs", str(value[1]))
        elif len(value) == 2 and value[0] == "max":
            obj.set("maxOccurs", str(value[1]))
        else:
            raise ValueError(
                f"Line {dct[line_number]}: exists keyword "
                f"needs to go either with optional, recommended, a list with two "
                f"entries either [min, <uint>] or [max, <uint>], or a list of four "
                f"entries [min, <uint>, max, <uint>] !"
            )
    else:
        # This clause take optional in all cases except dimension where 'required' key is allowed
        # not the 'optional' key.
        if value == "optional":
            obj.set("optional", "true")
        elif value == "recommended":
            obj.set("recommended", "true")
        elif value == "required":
            obj.set("optional", "false")
        else:
            obj.set("minOccurs", "0")


def xml_handle_dimensions(dct, obj, keyword, value):
    """
    Create dimensionsType element instance, its childs, and append to an existing element.

    tests/data/NXdimensionsType.yaml documents the syntax supported
    """
    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    dims: Optional[ET.Element] = None
    if isinstance(value, dict):
        # top-level docstring dealt with already by the caller
        n_idx_dicts = len(
            [key for key in value if re.match("^[0-9]+$", f"{key}") is not None]
        )
        non_line_comment_keys = []
        for key in value:
            if isinstance(key, str):
                if not key.startswith("__line__"):
                    non_line_comment_keys.append(key)
        if set(non_line_comment_keys) in [{"rank"}, {"rank", "doc"}]:
            # only rank
            dims = ET.SubElement(obj, "dimensions")
            dims.set("rank", f"{value['rank']}")
            if "doc" in value:
                docs = ET.SubElement(dims, "doc")
                docs.text = f"\n{value['doc']}"
        elif n_idx_dicts > 0:
            # full_syntax
            dims = ET.SubElement(obj, "dimensions")
            if "rank" in value:
                dims.set("rank", f"{value['rank']}")
            if "doc" in value:
                docs = ET.SubElement(dims, "doc")
                docs.text = f"{value['doc']}"
            for dim_key, dim_obj in value.items():
                if dim_key != "doc" and isinstance(dim_obj, dict):
                    dim = ET.SubElement(dims, "dim")
                    dim.set("index", str(dim_key))
                    for key, val in dim_obj.items():
                        if not key.startswith("__line__"):
                            if isinstance(val, bool):
                                # boolean representations in yaml should not become
                                # Python bool representations as otherwise roundtrips
                                # otherwise yaml2nxdl false > False but nxdl2yaml will
                                # keep it is as False > False
                                if val is True:
                                    dim.set(f"{key}", "true")
                                else:
                                    dim.set(f"{key}", "false")
                            elif isinstance(val, int):
                                dim.set(f"{key}", f"{val}")
                            else:
                                dim.set(f"{key}", val)
        elif "dim" in value and not isinstance(value["dim"], list):
            # one of the short variants
            if re.match("^\\([A-Za-z0-9_, ]+\\)$", value["dim"]) is not None:
                # common for cases shorthand_terse and shorthand_explicit_rank_new
                dims = ET.SubElement(obj, "dimensions")
                # rank = 0
                for idx, val in enumerate(
                    value["dim"][1:-1].replace(" ", "").split(",")
                ):
                    if val != "":
                        dim = ET.SubElement(dims, "dim")
                        dim.set("index", f"{idx + 1}")
                        dim.set("value", f"{val}")
                    # rank += 1
                if "rank" in value:  # shorthand_explicit_rank_new
                    dims.set("rank", f"{value['rank']}")
                # else:  # shorthand_terse, automatic setting of rank switched off
                #     dims.set("rank", f"{rank}")
        elif "dim" in value and isinstance(value["dim"], list) and "rank" in value:
            # shorthand_explicit_rank_old
            dims = ET.SubElement(obj, "dimensions")
            dims.set("rank", f"{value['rank']}")
            for entry in value["dim"]:
                if len(entry) == 2 and all(val != "" for val in entry):
                    dim = ET.SubElement(dims, "dim")
                    dim.set("index", f"{entry[0]}")
                    dim.set("value", f"{entry[1]}")
                else:
                    raise ValueError(
                        "{entry} does not follow shorthand_explicit_rank_old formatting"
                    )

    elif isinstance(value, str):
        if re.match("^\\([A-Za-z0-9_, ]+\\)$", value):
            valid_dims = []
            for entry in value[1:-1].replace(" ", "").split(","):
                if len(entry) > 0:  # ignore trailing comma and empty mnemonics
                    valid_dims.append(entry)
            if len(valid_dims) > 0:
                dims = ET.SubElement(obj, "dimensions")
                dims.set("rank", f"{len(valid_dims)}")
                for dim_idx, dim_name in enumerate(valid_dims):
                    if dim_idx != "" and dim_name != "":
                        dim = ET.SubElement(dims, "dim")
                        dim.set("index", f"{dim_idx + 1}")
                        dim.set("value", f"{dim_name}")

    # Comments for all <dim> elements will be on top of the <dimensions> element
    xml_handle_comment(obj, line_number, line_loc, dims)


def xml_handle_enumeration(dct, obj, keyword, value, verbose):
    """This function creates an 'enumeration' element instance.

    Different cases are handled:
    1) The items are in a flat list directly under "enumeration".
    2) The items are in a dicitionary under the "items" key.
    3) The items are dictionaries and may contain a nested doc.
    4) The enumeration is open. The input is a dict with keywords "open_enum"
       and "items" (which is  a flat list of all enum items without docs).
    5) The enumeration is open. The input is a nested dict with keyword "open_enum"
       and each items is a dict itself (with docs for each item).
    """
    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    xml_handle_comment(obj, line_number, line_loc)
    enum = ET.SubElement(obj, "enumeration")

    assert value is not None, (
        f"Line {line_loc}: enumeration must \
bear at least an argument !"
    )
    assert len(value) >= 1, (
        f"Line {dct[line_number]}: enumeration must not be an empty list!"
    )
    if isinstance(value, list):
        for element in value:
            itm = ET.SubElement(enum, "item")
            itm.set("value", str(element))
    if isinstance(value, dict) and value != {}:
        if "open_enum" in value:
            line_number = f"__line__{'open_enum'}"
            line_loc = value[line_number]
            xml_handle_comment(enum, line_number, line_loc)
            enum.set("open", str(value["open_enum"]))

            del value["open_enum"]

        if "items" in value:
            line_number = f"__line__{'items'}"
            line_loc = value[line_number]
            xml_handle_comment(enum, line_number, line_loc)

            if isinstance(value["items"], list):
                for element in value["items"]:
                    itm = ET.SubElement(enum, "item")
                    itm.set("value", str(element))
            return

        for element, elmnt_value in value.items():
            if "__line__" not in element:
                itm = ET.SubElement(enum, "item")
                itm.set("value", str(element))

                line_number = f"__line__{element}"
                line_loc = value[line_number]

                xml_handle_comment(enum, line_number, line_loc, itm)
                if isinstance(elmnt_value, dict):
                    recursive_build(itm, elmnt_value, verbose)


# pylint: disable=unused-argument
def xml_handle_link(dct, obj, keyword, value, verbose):
    """
    If we have an NXDL link we decode the name attribute from <optional string>(link)[:-6]
    """

    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    xml_handle_comment(obj, line_number, line_loc)
    name = keyword[:-6]
    link_obj = ET.SubElement(obj, "link")
    link_obj.set("name", str(name))

    if value:
        rm_key_list = []
        for attr, vval in value.items():
            if "__line__" in attr:
                continue
            line_number = f"__line__{attr}"
            line_loc = value[line_number]
            if attr == "doc":
                xml_handle_doc(link_obj, vval, line_number, line_loc)
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
            elif attr in YAML_LINK_ATTRIBUTES and not isinstance(vval, dict):
                if vval:
                    link_obj.set(attr, str(vval))
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
                xml_handle_comment(obj, line_number, line_loc, link_obj)

        for key in rm_key_list:
            del value[key]
        # Check for skipped attributes
        check_for_skipped_attributes("link", value, YAML_LINK_ATTRIBUTES, verbose)

    if isinstance(value, dict) and value != {}:
        recursive_build(link_obj, value, verbose=None)


def xml_handle_choice(dct, obj, keyword, value, verbose=False):
    """
    Build choice xml elements. That consists of groups.
    """
    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    xml_handle_comment(obj, line_number, line_loc)
    # Add to this tuple if new attributes have been added to nexus definition.
    possible_attr = ()
    choice_obj = ET.SubElement(obj, "choice")
    # take care of special attributes
    name = keyword[:-8]
    choice_obj.set("name", name)

    if value:
        rm_key_list = []
        for attr, vval in value.items():
            if "__line__" in attr:
                continue
            line_number = f"__line__{attr}"
            line_loc = value[line_number]
            if attr == "doc":
                xml_handle_doc(choice_obj, vval, line_number, line_loc)
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
            elif attr in possible_attr and not isinstance(vval, dict):
                if vval:
                    choice_obj.set(attr, str(vval))
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
                xml_handle_comment(obj, line_number, line_loc, choice_obj)

        for key in rm_key_list:
            del value[key]
        # Check for skipped attributes
        check_for_skipped_attributes("choice", value, possible_attr, verbose)

    if isinstance(value, dict) and value != {}:
        recursive_build(choice_obj, value, verbose=None)


def xml_handle_symbols(dct, obj, keyword, value: dict):
    """Handle a set of NXDL symbols as a child to obj"""
    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    assert len(list(value.keys())) > 0, (
        f"Line {line_loc}: symbols table must not be empty !"
    )
    xml_handle_comment(obj, line_number, line_loc)
    syms = ET.SubElement(obj, "symbols")
    if "doc" in value.keys():
        line_number = "__line__doc"
        line_loc = value[line_number]
        xml_handle_comment(syms, line_number, line_loc)
        doctag = ET.SubElement(syms, "doc")
        doctag.text = "\n" + textwrap.fill(value["doc"], width=70) + "\n"
    rm_key_list = []
    for kkeyword, vvalue in value.items():
        if "__line__" in kkeyword:
            continue
        if kkeyword != "doc":
            line_number = f"__line__{kkeyword}"
            line_loc = value[line_number]
            xml_handle_comment(syms, line_number, line_loc)
            assert vvalue is not None and isinstance(vvalue, str), (
                f"Line {line_loc}: put a comment in doc string !"
            )
            sym = ET.SubElement(syms, "symbol")
            sym.set("name", kkeyword)
            xml_handle_doc(sym, vvalue)
            rm_key_list.append(kkeyword)
            rm_key_list.append(line_number)
    for key in rm_key_list:
        del value[key]


def check_keyword_variable(verbose, dct, keyword, value):
    """
    Check whether both keyword_name and keyword_type are empty,
        and complains if it is the case
    """
    keyword_name, keyword_type = nx_name_type_resolving(keyword)
    if verbose:
        print(f"{keyword_name}({keyword_type}): value type is {type(value)}\n")
    if keyword_name == "" and keyword_type == "":
        line_number = f"__line__{keyword}"
        raise ValueError(f"Line {dct[line_number]}: found an improper yaml key !")


def helper_keyword_type(kkeyword_type):
    """
    Return a value of keyword_type if it belong to NX_TYPE_KEYS
    """
    if re.match(r"NX_[A-Z]+", kkeyword_type):
        return kkeyword_type
    return None


def verbose_flag(verbose, keyword, value):
    """
    Verbose stdout printing for nested levels of yaml file, if verbose flag is active
    """
    if verbose:
        print(f"key:{keyword}; value type is {type(value)}\n")


def xml_handle_nametype(keyword, keyword_name, dct, obj):
    """
    Identify NeXus nameType attribute for field, group, attribute use hint if required.
    """
    concept_name = keyword_name[2:] if keyword_name.startswith("\\@") else keyword_name
    if concept_name == "":
        # no explicit name given as e.g. in group type="NXobject"
        # obj.set("nameType", "any")
        # cannot be specified because having no/empty concept name is not allowed
        # cannot be partial because if no hint is given why should it be partial
        return
    if concept_name.islower():
        # obj.set("nameType", "specified")  # is the NeXus default, no need to add
        return
    if concept_name.isupper():
        # nameType="any" correct for almost all cases except for those where an
        # explicit nameType hint is made in the yaml file
        # this is relevant for e.g. NXcanSAS ENTRY/DATA/Q which is specified
        if dct.get(keyword) and "nameType" in dct[keyword]:
            supported = ["specified", "any", "partial"]
            name_type = dct[keyword]["nameType"]
            if name_type in supported:
                obj.set("nameType", name_type)
            else:
                raise ValueError(f"nameType for {keyword} is not in {supported}")
        return
    # Mixed-case names: Check if an explicit nameType hint is provided.
    if dct.get(keyword) and "nameType" in dct[keyword]:
        supported = ["specified", "any", "partial"]
        name_type = dct[keyword]["nameType"]
        if name_type in supported:
            obj.set("nameType", name_type)
            return
        else:
            warnings.warn(
                f"Mixed case concept_name with an unsupported nameType {name_type}",
                SyntaxWarning,
            )

    # Determine if the name follows a variable-like pattern.
    variable_prefix_match = re.search("^[A-Z]*[a-z0-9_.]*$", concept_name)
    variable_suffix_match = re.search("^[a-z0-9_.]*[A-Z]*$", concept_name)
    if variable_prefix_match or variable_suffix_match:
        warnings.warn(
            "Concept matching a partial nametype detected that lacks nameType=partial",
            SyntaxWarning,
        )
        return
    # Default case: NeXus assumes "specified" as the default, so no need to set it explicitly.
    # NXcanSAS dQw suggests it is specified, or is this an error in that appdef?
    # raise ValueError(f"nameType for {concept_name} undefined")


def xml_handle_attributes(dct, obj, keyword, value, verbose):
    """Handle the attributes found connected to attribute field"""

    line_number = f"__line__{keyword}"
    line_loc = dct[line_number]
    xml_handle_comment(obj, line_number, line_loc)
    # as an attribute identifier
    keyword_name, keyword_typ = nx_name_type_resolving(keyword)
    line_number = f"__line__{keyword}"
    if verbose:
        print(f"__line__ : {dct[line_number]}")
    if keyword_name == "" and keyword_typ == "":
        raise ValueError(f"Line {dct[line_number]}: found an improper yaml key !")
    elemt_obj = ET.SubElement(obj, "attribute")
    elemt_obj.set("name", keyword_name[2:])
    if keyword_typ:
        elemt_obj.set("type", keyword_typ)

    rm_key_list = []
    if value and value:
        # taking care of attributes of attributes
        for attr, attr_val in value.items():
            if "__line__" in attr:
                continue
            line_number = f"__line__{attr}"
            line_loc = value[line_number]
            if attr in ["doc", *YAML_ATTRIBUTES_ATTRIBUTES] and not isinstance(
                attr_val, dict
            ):
                if attr == "unit":
                    elemt_obj.set(f"{attr}s", str(value[attr]))
                    rm_key_list.append(attr)
                    rm_key_list.append(line_number)
                    xml_handle_comment(obj, line_number, line_loc, elemt_obj)
                elif attr == "exists" and attr_val:
                    xml_handle_exists(value, elemt_obj, attr, attr_val)
                    rm_key_list.append(attr)
                    rm_key_list.append(line_number)
                    xml_handle_comment(obj, line_number, line_loc, elemt_obj)
                elif attr == "doc":
                    xml_handle_doc(
                        elemt_obj, format_nxdl_doc(attr_val), line_number, line_loc
                    )
                    rm_key_list.append(attr)
                    rm_key_list.append(line_number)
                elif attr == "nameType":
                    xml_handle_nametype(keyword, keyword_name, dct, elemt_obj)
                else:
                    elemt_obj.set(attr, check_for_mapping_char_other(attr_val))
                    rm_key_list.append(attr)
                    rm_key_list.append(line_number)
                    xml_handle_comment(obj, line_number, line_loc, elemt_obj)

        for key in rm_key_list:
            del value[key]
        # Check cor skipped attribute
        check_for_skipped_attributes(
            "Attribute", value, YAML_ATTRIBUTES_ATTRIBUTES, verbose
        )
    if value:
        recursive_build(elemt_obj, value, verbose)


def validate_field_attribute_and_value(v_attr, vval, allowed_attribute, value):
    """
    Check for any attributes that comes with invalid name,
        and invalid value.
    """

    if not isinstance(vval, dict) and not str(vval):  # check for empty value
        line_number = f"__line__{v_attr}"
        raise ValueError(
            f"In a field a valid attribute ('{v_attr}') found that is not stored."
            f" Please check around line {value[line_number]}"
        )

    # The below elements might come as child element
    skipped_child_name = ["doc", "dimension", "enumeration", "choice", "exists"]
    # check for invalid key or attributes
    if (
        v_attr not in [*skipped_child_name, *allowed_attribute]
        and "__line__" not in v_attr
        and not isinstance(vval, dict)
        and "(" not in v_attr  # skip only groups and field that has name and type
        and "\\@" not in v_attr
    ):  # skip nexus attributes
        line_number = f"__line__{v_attr}"
        raise ValueError(
            f"In a field or group a invalid attribute ('{v_attr}') or child has found."
            f" Please check around line {value[line_number]}."
        )


def xml_handle_fields_or_group(
    dct, obj, keyword, value, ele_type, allowed_attr, verbose=False
):
    """Handle a field or group in yaml file."""
    line_annot = f"__line__{keyword}"
    line_loc = dct[line_annot]
    xml_handle_comment(obj, line_annot, line_loc)
    l_bracket = -1
    r_bracket = -1
    if keyword.count("(") == 1:
        l_bracket = keyword.index("(")
    if keyword.count(")") == 1:
        r_bracket = keyword.index(")")

    keyword_name, keyword_type = nx_name_type_resolving(keyword)
    if ele_type == "field" and not keyword_name:
        raise ValueError(
            f"No name for NeXus {ele_type} has been found. Check around line:{line_loc}"
        )
    if not keyword_type and not keyword_name:
        raise ValueError(
            f"No name or type for NeXus {ele_type} has been found."
            f"Check around line: {line_loc}"
        )

    elemt_obj = ET.SubElement(obj, ele_type)

    # type come first
    if l_bracket == 0 and r_bracket > 0:
        elemt_obj.set("type", keyword_type)
        if keyword_name:
            elemt_obj.set("name", keyword_name)
    elif l_bracket > 0:
        elemt_obj.set("name", keyword_name)
        if keyword_type:
            elemt_obj.set("type", keyword_type)
    else:
        elemt_obj.set("name", keyword_name)

    if isinstance(value, dict):
        # calls to this field_or_group function need to deal specifically with entries
        # like nameType: somevalue because we do not require fields, or attributes
        # to include a datatype attribute when we assume that is (NX_CHAR)
        # hence nameType: specified could be misinterpreted as introducing a new child
        # there is a clear signature though to assure if we face a group, field, or attribute,
        # namely when value is only a dictionary and not a string
        # i.e. conceptname(class or datatype): may only be have trailing comments
        # on the same line
        rm_key_list = []
        # In each each if clause apply xml_handle_comment(), to collect
        # comments on that yaml line.
        for attr, vval in value.items():
            if "__line__" in attr:
                continue
            line_number = f"__line__{attr}"
            line_loc = value[line_number]
            if attr == "doc":
                xml_handle_doc(
                    elemt_obj,
                    vval,
                    line_number,
                    line_loc,
                )
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
            elif attr == "exists" and vval:
                xml_handle_exists(value, elemt_obj, attr, vval)
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
                xml_handle_comment(obj, line_number, line_loc, elemt_obj)
            elif attr == "nameType":
                xml_handle_nametype(keyword, keyword_name, dct, elemt_obj)
            elif attr == "unit" and ele_type == "field":
                xml_handle_units(elemt_obj, vval)
                xml_handle_comment(obj, line_number, line_loc, elemt_obj)
                rm_key_list.append(attr)
            elif attr in ("dimensions", "dim") and ele_type == "field":
                xml_handle_dimensions(
                    dct=value, obj=elemt_obj, keyword=attr, value=vval
                )
                rm_key_list.append(attr)
            elif attr in allowed_attr and not isinstance(vval, dict) and vval:
                validate_field_attribute_and_value(attr, vval, allowed_attr, value)
                elemt_obj.set(attr, check_for_mapping_char_other(vval))
                rm_key_list.append(attr)
                rm_key_list.append(line_number)
                xml_handle_comment(obj, line_number, line_loc, elemt_obj)

        for key in rm_key_list:
            del value[key]
        # Check for skipped attributes
        check_for_skipped_attributes(ele_type, value, allowed_attr, verbose)

        if value != {}:
            recursive_build(elemt_obj, value, verbose)


def xml_handle_comment(
    obj: ET._Element,
    line_annotation: str,
    line_loc_no: int,
    xml_ele: ET._Element = None,
    is_def_cmnt: bool = False,
):
    """Handle comment.

        Add xml comment: check for comments searched by 'line_annotation'
    (e.g. __line__data) and line_loc_no (e.g. 30). It
    does following tasks:

    1. Rearrange comment elements of xml_ele and xml_ele where comment comes first.
    2. Append comment element when no xml_ele found as general comments.
    """

    line_info = (line_annotation, int(line_loc_no))
    if line_info in COMMENT_BLOCKS:  # noqa: F821
        cmnt = COMMENT_BLOCKS.get_comment_by_line_info(line_info)  # noqa: F821
        cmnt_text = cmnt.get_comment_text_list()

        # Check comment for definition element and return
        if is_def_cmnt:
            return cmnt_text
        if xml_ele is not None:
            obj.remove(xml_ele)
            for string in cmnt_text:
                # Format comment string to preserve text nxdl to yaml and vice versa
                obj.append(ET.Comment(string))
            obj.append(xml_ele)
        elif not is_def_cmnt and xml_ele is None:
            for string in cmnt_text:
                obj.append(ET.Comment(string))

    # The searched comment is not related with definition element
    return []


def recursive_build(obj, dct, verbose):
    """Walk through nested dictionary.
    Parameters:
    -----------
    obj : ET.Element
        Obj is the current node of the XML tree where we want to append to.
    dct : dict
     dct is the nested python dictionary which represents the content of a child and
     its successors.

    Note: NXDL fields may contain attributes but trigger no recursion so attributes are leafs.
    """
    for keyword, value in iter(dct.items()):
        if "__line__" in keyword:
            continue
        line_number = f"__line__{keyword}"
        line_loc = dct[line_number]
        keyword_name, keyword_type = nx_name_type_resolving(keyword)
        # keyword's like nameType need proper escape character in the future
        # to simplify their distinction from NX_CHAR fields and attributes
        if 0 < sum(1 for char in keyword if char.isupper()) < len(keyword):
            if isinstance(value, str):
                continue

        check_keyword_variable(verbose, dct, keyword, value)
        if verbose:
            print(f"keyword_name:{keyword_name} keyword_type {keyword_type}\n")

        if keyword[-6:] == "(link)":
            xml_handle_link(dct, obj, keyword, value, verbose)
        elif keyword[-8:] == "(choice)":
            xml_handle_choice(dct, obj, keyword, value)
        # symbols of fields or attributes, root level symbols dealt with by nyaml2nxdl()
        elif keyword_type == "" and keyword_name == "symbols":
            xml_handle_symbols(dct, obj, keyword, value)
        elif re.match(r"NX[a-zA-Z].*", keyword_type) is not None:
            elem_type = "group"
            # we can be sure we need to instantiate a new group
            xml_handle_fields_or_group(
                dct,
                obj,
                keyword,
                value,
                elem_type,
                YAML_GROUP_ATTRIBUTES,
                verbose=False,
            )
        elif keyword_name[0:2] == "\\@":  # check if obj qualifies as a NeXus attribute
            xml_handle_attributes(dct, obj, keyword, value, verbose)
        elif keyword == "doc":
            xml_handle_doc(obj, value, line_number, line_loc)
        elif keyword == "unit":
            xml_handle_units(obj, value)
        elif keyword == "enumeration":
            xml_handle_enumeration(dct, obj, keyword, value, verbose)
        elif keyword in ("dimensions", "dim"):
            xml_handle_dimensions(dct, obj, keyword, value)
        elif keyword == "exists":
            xml_handle_exists(dct, obj, keyword, value)
        # Handles fileds e.g. AXISNAME
        elif keyword_name != "" and "__line__" not in keyword_name:
            elem_type = "field"
            xml_handle_fields_or_group(
                dct,
                obj,
                keyword,
                value,
                elem_type,
                YAML_FIELD_ATTRIBUTES,
                verbose=False,
            )
        else:
            raise ValueError(
                f"An unknown type of element {keyword} has been found which is "
                f"not be able to be resolved. Check around line {dct[line_number]}"
            )
        if isinstance(value, dict):
            if value in ("dimensions", "dim"):
                xml_handle_dimensions(dct, obj, keyword, value)


def extend_doc_type(doc_type, new_component, comment=False):
    """Extend doc type for etree.tostring function

    Extend doc type to build DOM and process instruction comments.
    """
    start_sym = "<?"
    end_sym = "?>"
    if comment:
        start_sym = "<!--\n"
        end_sym = "-->"
    return doc_type + "\n" + start_sym + new_component + end_sym


def pretty_print_xml(xml_root, output_xml, def_comments=None):
    """Print in nxdl.xml file.

    Print better human-readable indented and formatted xml file using
    built-in libraries and preceding XML processing instruction
    """
    # Handle DOM as doc_type
    doc_type = '<?xml-stylesheet type="text/xsl" href="nxdlformat.xsl"?>'

    if DOM_COMMENT:
        doc_type = extend_doc_type(doc_type, DOM_COMMENT, comment=True)
    if def_comments:
        for string in def_comments:
            doc_type = extend_doc_type(doc_type, string, comment=True)

    tmp_xml = "tmp.xml"
    ET.indent(xml_root, space=DEPTH_SIZE)
    xml_string = ET.tostring(
        xml_root,
        pretty_print=True,
        encoding="UTF-8",
        xml_declaration=True,
        doctype=doc_type,
    )
    with open(tmp_xml, "wb") as file_tmp:
        file_tmp.write(xml_string)
    flag = False
    with open(tmp_xml, "r", encoding="utf-8") as file_out:
        with open(output_xml, "w", encoding="utf-8") as file_out_mod:
            for i in file_out.readlines():
                i = unquote(i)
                if "<doc>" not in i and "</doc>" not in i and flag is False:
                    file_out_mod.write(i)
                elif "<doc>" in i and "</doc>" in i:
                    file_out_mod.write(i)
                elif "<doc>" in i and "</doc>" not in i:
                    flag = True
                    white_spaces = len(i) - len(i.lstrip())
                    file_out_mod.write(i)
                elif "<doc>" not in i and "</doc>" not in i and flag is True:
                    file_out_mod.write((white_spaces + 4) * " " + i)
                elif "<doc>" not in i and "</doc>" in i and flag is True:
                    file_out_mod.write(white_spaces * " " + i)
                    flag = False
    tmp_xml_path = pathlib.Path(tmp_xml)
    pathlib.Path.unlink(tmp_xml_path)


# pylint: disable=too-many-statements
def nyaml2nxdl(input_file: str, out_file, verbose: bool):
    """
    Main of the nyaml2nxdl converter, creates XML tree, namespace and
    schema, definitions then evaluates a nested dictionary of groups recursively and
    fields or (their) attributes as children of the groups
    """
    nxdl_copyright_license = get_nxdl_copyright_license(nxdl_file=out_file)
    set_copyright_text(nxdl_copyright_license=nxdl_copyright_license)
    def_attributes = [
        "deprecated",
        "ignoreExtraGroups",
        "category",
        "type",
        "ignoreExtraFields",
        "ignoreExtraAttributes",
        "restricts",
    ]
    yml_appdef = yml_reader(input_file)
    def_cmnt_text = []
    if verbose:
        print(f"input-file: {input_file}\n")
        print("application/base contains the following root-level entries:\n")
        print(str(yml_appdef.keys()))
    # etree does not allow to set namespace-map after root creation
    # So, mimic a nsmap and fill it later as dict has hash property
    nsmap = {
        None: "http://definition.nexusformat.org/nxdl/3.1",
    }
    xml_root = ET.Element("definition", attrib={}, nsmap=nsmap)
    assert "category" in yml_appdef.keys(), (
        "Required root-level keyword category is missing!"
    )
    assert yml_appdef["category"] in [
        "application",
        "base",
    ], (
        "Only \
application and base are valid categories!"
    )
    assert "doc" in yml_appdef.keys(), "Required root-level keyword doc is missing!"

    name_extends = ""
    yml_appdef_copy = yml_appdef.copy()
    for kkey, vvalue in yml_appdef_copy.items():
        if "__line__" in kkey:
            continue
        line_number = f"__line__{kkey}"
        line_loc_no = yml_appdef[line_number]
        if not isinstance(vvalue, dict) and kkey in def_attributes:
            if isinstance(vvalue, bool):
                xml_root.set(kkey, "true" if vvalue else "false")
            else:
                xml_root.set(kkey, str(vvalue) or "")
            cmnt_text = xml_handle_comment(
                xml_root, line_number, line_loc_no, is_def_cmnt=True
            )
            def_cmnt_text += cmnt_text

            del yml_appdef[line_number]
            del yml_appdef[kkey]
        # Taking care of name and extends
        elif "NX" in kkey:
            # Taking the attribute order but the correct value will be stored later
            # check for name first or type first if (NXobject)NXname then type first
            l_bracket_ind = kkey.rfind("(")
            r_bracket_ind = kkey.rfind(")")
            if l_bracket_ind == 0:
                extend = kkey[1:r_bracket_ind]
                name = kkey[r_bracket_ind + 1 :]
                xml_root.set("extends", extend)
                xml_root.set("name", name)
            elif l_bracket_ind > 0:
                name = kkey[0:l_bracket_ind]
                extend = kkey[l_bracket_ind + 1 : r_bracket_ind]
                xml_root.set("name", name)
                xml_root.set("extends", extend)
            else:
                name = kkey
                xml_root.set("name", name)
                xml_root.set("extends", "NXobject")
            cmnt_text = xml_handle_comment(
                xml_root, line_number, line_loc_no, is_def_cmnt=True
            )
            def_cmnt_text += cmnt_text if cmnt_text else []

            name_extends = kkey

    if "type" not in xml_root.attrib:
        xml_root.set("type", "group")
    # Taking care of namespaces
    namespaces = {
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    }
    # Fill nsmap variable here
    nsmap.update(namespaces)  # type: ignore
    xml_root.attrib["{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"] = (
        "http://definition.nexusformat.org/nxdl/3.1 ../nxdl.xsd".replace(" ", "%20")
    )

    # Taking care of Symbols elements
    if "symbols" in yml_appdef.keys():
        xml_handle_symbols(yml_appdef, xml_root, "symbols", yml_appdef["symbols"])

        del yml_appdef["symbols"]
        del yml_appdef["__line__symbols"]
    if isinstance(yml_appdef["doc"], str):
        assert yml_appdef["doc"] != "", "Doc has to be a non-empty string!"
    elif isinstance(yml_appdef["doc"], list):
        assert any(yml_appdef["doc"]), (
            "One of the doc elements has to be a non-empty string!"
        )

    line_number = "__line__doc"
    line_loc_no = yml_appdef[line_number]
    xml_handle_doc(xml_root, yml_appdef["doc"], line_number, line_loc_no)

    del yml_appdef["doc"]

    root_keys = 0
    for key in yml_appdef.keys():
        if "__line__" not in key:
            root_keys += 1
            extra_key = key

    assert root_keys == 1, (
        f"Accepting at most keywords: category, doc, symbols, and NX... "
        f"at root-level! check key at root level {extra_key}"
    )

    assert "NX" in name_extends and len(name_extends) > 2, (
        "NX \
keyword has an invalid pattern, or is too short!"
    )
    # Write copyright year in doc string
    # Taking care if definition has empty content
    if yml_appdef[name_extends]:
        recursive_build(xml_root, yml_appdef[name_extends], verbose)
    # Taking care of comments that comes at the end of file that is might not be intended for
    # any nxdl elements.
    if COMMENT_BLOCKS[-1].has_post_comment:  # noqa: F821
        post_comment = COMMENT_BLOCKS[-1]  # noqa: F821
        (lin_annot, line_loc) = post_comment.get_line_info()
        xml_handle_comment(xml_root, lin_annot, line_loc)

    # Note: Just to keep the functionality if we need this later.
    default_attr = False
    if default_attr:
        check_for_default_attribute_and_value(xml_root)
    pretty_print_xml(xml_root, out_file, def_cmnt_text)
    if verbose:
        print("Parsed YAML to NXDL successfully\n")
