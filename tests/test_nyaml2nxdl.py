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
Tests for nyaml2nxdl tool
"""
import filecmp
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import lxml.etree as ET
import pytest
from click.testing import CliRunner

from nyaml import nyaml2nxdl, nyaml2nxdl_forward_tools
from nyaml.comment_collector import CommentCollector
from nyaml.nyaml2nxdl_forward_tools import handle_each_part_doc
from nyaml.nyaml2nxdl_helper import LineLoader, remove_namespace_from_tag


def delete_duplicates(list_of_matching_string):
    """
    Delete duplicate from lists
    """
    return list(dict.fromkeys(list_of_matching_string))


def check_file_fresh_baked(test_file):
    """
    Get sure that the test file is generated by the converter
    """
    path = Path(test_file)
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    assert timestamp == now, "xml file not generated"


def find_matches(xml_file, desired_matches):
    """
        Read xml file and find desired matches. Return a list of two lists in the form:
    [[matching_line],[matching_line_index]]
    """
    with open(xml_file, "r", encoding="utf-8") as file:
        xml_reference = file.readlines()
    lines = []
    lines_index = []
    found_matches = []
    for i, line in enumerate(xml_reference):
        for desired_match in desired_matches:
            if str(desired_match) in str(line):
                lines.append(line)
                lines_index.append(i)
                found_matches.append(desired_match)
    # ascertain that all the desired matches were found in file
    found_matches_clean = delete_duplicates(found_matches)
    assert len(found_matches_clean) == len(
        desired_matches
    ), "some desired_matches were \nnot found in file"
    return [lines, lines_index]


def compare_matches(ref_xml_file, test_yml_file, test_xml_file, desired_matches):
    """
        Check if a new xml file is generated
    and if test xml file is equal to reference xml file
    """
    # Reference file is read
    ref_matches = find_matches(ref_xml_file, desired_matches)
    # Test file is generated
    runner = CliRunner()
    result = runner.invoke(nyaml2nxdl.launch_tool, ["--input-file", test_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)
    # Test file is read
    test_matches = find_matches(test_xml_file, desired_matches)
    assert test_matches == ref_matches


def test_links():
    """
    Check the correct parsing of links
    """
    ref_xml_link_file = "tests/data/Ref_NXtest_links.nxdl.xml"
    test_yml_link_file = "tests/data/NXtest_links.yaml"
    test_xml_link_file = "tests/data/NXtest_links.nxdl.xml"
    # ref_xml_link_file = os.path.abspath(data_path + '/Ref_NXtest_links.nxdl.xml')
    # test_yml_link_file = os.path.abspath(data_path + '/NXtest_links.yaml')
    # test_xml_link_file = os.path.abspath(data_path + '/NXtest_links.nxdl.xml')
    desired_matches = ["<link", "/>"]
    compare_matches(
        ref_xml_link_file, test_yml_link_file, test_xml_link_file, desired_matches
    )
    os.remove("tests/data/NXtest_links.nxdl.xml")
    sys.stdout.write("Test on links okay.\n")


def test_docs():
    """In this test an xml file in converted to yml and then back to xml.
    The xml trees of the two files are then compared.
    """
    ref_xml_file = "tests/data/Ref_NXellipsometry-docCheck.nxdl.xml"
    test_yml_file = "tests/data/NXellipsometry-docCheck.yaml"
    test_xml_file = "tests/data/NXellipsometry-docCheck.nxdl.xml"
    desired_matches = ["<doc", "</doc>"]
    compare_matches(ref_xml_file, test_yml_file, test_xml_file, desired_matches)
    os.remove("tests/data/NXellipsometry-docCheck.nxdl.xml")
    sys.stdout.write("Test on documentation formatting okay.\n")


def test_nxdl2yaml_doc_format_and_nxdl_part_as_comment():
    """
    This test for two reason:
        1. In test-1 an nxdl file with all kind of doc formats are translated
    to yaml to check if they are correct.
        2. In test-2: Check the nxdl that comes at the end of yaml file as comment.
    """
    ref_xml_file = "tests/data/Ref_NXentry.nxdl.xml"
    ref_yml_file = "tests/data/Ref_NXentry.yaml"
    test_yml_file = "tests/data/Ref_NXentry_parsed.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    result = filecmp.cmp(ref_yml_file, test_yml_file, shallow=False)
    assert (
        result
    ), "Ref YML and parsed YML\
has not the same structure!!"
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml doc formatting okay.\n")


def test_fileline_error():
    """
    In this test the yaml fileline in the error message is tested.
    """
    test_yml_file = "tests/data/NXfilelineError1.yaml"
    out_nxdl = "tests/data/NXfilelineError1.nxdl.xml"
    out_yaml = "tests/data/temp_NXfilelineError1.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", test_yml_file])
    assert result.exit_code == 1
    assert "13" in str(result.exception)
    os.remove(out_nxdl)
    os.remove(out_yaml)

    test_yml_file = "tests/data/NXfilelineError2.yaml"
    out_nxdl = "tests/data/NXfilelineError2.nxdl.xml"
    out_yaml = "tests/data/temp_NXfilelineError2.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", test_yml_file])
    assert result.exit_code == 1
    assert "21" in str(result.exception)
    os.remove(out_nxdl)
    os.remove(out_yaml)

    test_yml_file = "tests/data/NXfilelineError3.yaml"
    out_nxdl = "tests/data/NXfilelineError3.nxdl.xml"
    out_yaml = "tests/data/temp_NXfilelineError3.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", test_yml_file])
    assert result.exit_code == 1
    assert "25" in str(result.exception)
    os.remove(out_nxdl)
    os.remove(out_yaml)

    sys.stdout.write("Test on xml -> yml fileline error handling okay.\n")


def test_symbols():
    """
    Check the correct parsing of symbols
    """
    ref_xml_symbol_file = "tests/data/Ref_NXnested_symbols.nxdl.xml"
    test_yml_symbol_file = "tests/data/NXnested_symbols.yaml"
    test_xml_symbol_file = "tests/data/NXnested_symbols.nxdl.xml"
    desired_matches = ["<symbols>", "</symbols>", "<symbols"]
    compare_matches(
        ref_xml_symbol_file, test_yml_symbol_file, test_xml_symbol_file, desired_matches
    )
    os.remove("tests/data/NXnested_symbols.nxdl.xml")
    sys.stdout.write("Test on symbols okay.\n")


def test_attributes():
    """
    Check expected attributes in NeXus fields, groups, and attributes.
    Check proper doc elements.
    """
    ref_xml_attribute_file = "tests/data/Ref_NXattributes.nxdl.xml"
    test_yml_attribute_file = "tests/data/NXattributes.yaml"
    test_xml_attribute_file = "tests/data/NXattributes.nxdl.xml"
    desired_matches = [
        "<attribute",
        "</attribute>",
        "<doc>",
        "</doc>",
        "<field",
        "</field>",
        "<group",
        "</group>",
    ]
    compare_matches(
        ref_xml_attribute_file,
        test_yml_attribute_file,
        test_xml_attribute_file,
        desired_matches,
    )
    os.remove("tests/data/NXattributes.nxdl.xml")
    sys.stdout.write("Test on attributes okay.\n")


def test_extends():
    """
    Check the correct handling of extends keyword
    """
    ref_xml_attribute_file = "tests/data/Ref_NXattributes.nxdl.xml"
    test_yml_attribute_file = "tests/data/NXattributes.yaml"
    test_xml_attribute_file = "tests/data/NXattributes.nxdl.xml"
    runner = CliRunner()
    result = runner.invoke(
        nyaml2nxdl.launch_tool, ["--input-file", test_yml_attribute_file]
    )
    assert result.exit_code == 0
    ref_root_node = ET.parse(ref_xml_attribute_file).getroot()
    test_root_node = ET.parse(test_xml_attribute_file).getroot()
    assert ref_root_node.attrib == test_root_node.attrib
    os.remove("tests/data/NXattributes.nxdl.xml")
    sys.stdout.write("Test on extends keyword okay.\n")


def test_symbols_and_enum_docs():
    """
        Check the correct handling of empty attributes
    or attributes fields, e.g. doc
    """
    ref_xml_file = "tests/data/Ref_NXmytests.nxdl.xml"
    test_yml_file = "tests/data/NXmytests.yaml"
    test_xml_file = "tests/data/NXmytests.nxdl.xml"
    desired_matches = [
        "<attribute",
        "</attribute>",
        "<doc>",
        "</doc>",
        "<symbols>",
        "</symbols>",
        "<symbols",
        "<dimensions",
        "</dimensions>",
        "<dim",
    ]
    compare_matches(ref_xml_file, test_yml_file, test_xml_file, desired_matches)
    os.remove("tests/data/nyaml2nxdl/NXmytests.nxdl.xml")
    sys.stdout.write("Test on docs in enumeration and symbols okay.\n")


def test_xml_parsing():
    """
        In this test an xml file in converted to yml and then back to xml.
    The xml trees of the two files are then compared.
    """
    ref_xml_file = "tests/data/Ref_NXellips.nxdl.xml"
    test_yml_file = "tests/data/Ref_NXellips_parsed.yaml"
    test_xml_file = "tests/data/Ref_NXellips_parsed.nxdl.xml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", test_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)

    test_tree = ET.parse(test_xml_file)
    test_tree_flattened = set([i.tag.split("}", 1)[1] for i in test_tree.iter()])

    ref_tree = ET.parse(ref_xml_file)
    ref_tree_flattened = set([i.tag.split("}", 1)[1] for i in ref_tree.iter()])

    assert (
        test_tree_flattened == ref_tree_flattened
    ), "Ref XML and parsed XML\
has not the same tree structure!!"
    os.remove("tests/data/Ref_NXellips_parsed.nxdl.xml")
    os.remove("tests/data/Ref_NXellips_parsed.yaml")
    sys.stdout.write("Test on xml -> yml -> xml okay.\n")


def test_yml_parsing():
    """In this test an xml file in converted to yml and then back to xml.
    The xml trees of the two files are then compared.
    """
    ref_yml_file = "tests/data/Ref_NXellipsometry.yaml"
    test_xml_file = "tests/data/Ref_NXellipsometry.nxdl.xml"
    test_yml_file = "tests/data/Ref_NXellipsometry_parsed.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", ref_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", test_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    test_yml_tree = nyaml2nxdl_forward_tools.yml_reader(test_yml_file)

    ref_yml_tree = nyaml2nxdl_forward_tools.yml_reader(ref_yml_file)

    assert list(test_yml_tree) == list(
        ref_yml_tree
    ), "Ref YML and parsed YML \
has not the same root entries!!"
    os.remove("tests/data/Ref_NXellipsometry_parsed.yaml")
    os.remove("tests/data/Ref_NXellipsometry.nxdl.xml")
    sys.stdout.write("Test on yml -> xml -> yml okay.\n")


def test_yml_consistency_comment_parsing():
    """Test comments parsing from yaml. Convert 'yaml' input file to '.nxdl.xml' and
    '.nxdl.xml' to '.yaml'
    """

    ref_yml_file = "tests/data/Ref_NXcomment.yaml"
    test_yml_file = "tests/data/Ref_NXcomment_consistency.yaml"

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, ["--input-file", ref_yml_file, "--check-consistency"]
    )
    assert result.exit_code == 0, (
        f"Exception: {result.exception}, \nExecution Info:" "{result.exc_info}"
    )
    with open(ref_yml_file, "r", encoding="utf-8") as ref_yml:
        loader = LineLoader(ref_yml)
        ref_loaded_yaml = loader.get_single_data()
    ref_comment_blocks = CommentCollector(ref_yml_file, ref_loaded_yaml)
    ref_comment_blocks.extract_all_comment_blocks()

    with open(test_yml_file, "r", encoding="utf-8") as test_yml:
        loader = LineLoader(test_yml)
        test_loaded_yaml = loader.get_single_data()
    test_comment_blocks = CommentCollector(test_yml_file, test_loaded_yaml)
    test_comment_blocks.extract_all_comment_blocks()

    for ref_cmnt, test_cmnt in zip(ref_comment_blocks, test_comment_blocks):
        assert ref_cmnt == test_cmnt, "Comment is not consistent."

    os.remove(test_yml_file)


def test_yml2xml_comment_parsing():
    """To test comment that written in xml for element attributes, e.g.
    attribute 'rank' for 'dimension' element and attribute 'exists' for
    'NXentry' group element.
    """
    input_yml = "tests/data/NXcomment_yaml2nxdl.yaml"
    ref_xml = "tests/data/Ref_NXcomment_yaml2nxdl.nxdl.xml"
    test_xml = "tests/data/NXcomment_yaml2nxdl.nxdl.xml"

    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", input_yml])
    assert result.exit_code == 0

    ref_root = ET.parse(ref_xml).getroot()
    test_root = ET.parse(test_xml).getroot()

    def recursive_compare(ref_root, test_root):
        assert ref_root.attrib.items() == test_root.attrib.items(), (
            "Got different xml element" "Atribute."
        )
        if ref_root.text and test_root.text:
            assert (
                ref_root.text.strip() == test_root.text.strip()
            ), "Got differen element text."
        if len(ref_root) > 0 and len(test_root) > 0:
            for x, y in zip(ref_root, test_root):
                recursive_compare(x, y)

    recursive_compare(ref_root, test_root)

    os.remove(test_xml)


def test_conversion():
    root = Path(__file__).parent / "data" / "NXentry.nxdl.xml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", root])
    assert result.exit_code == 0
    # Replace suffixes
    yaml = root.parent / Path(root.with_suffix("").stem + "_parsed.yaml")
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", yaml])
    assert result.exit_code == 0
    new_root = yaml.with_suffix(".nxdl.xml")
    with open(root, encoding="utf-8", mode="r") as tmp_f:
        root_content = tmp_f.readlines()
    with open(new_root, encoding="utf-8", mode="r") as tmp_f:
        new_root_content = tmp_f.readlines()
    assert root_content == new_root_content
    Path.unlink(yaml)
    Path.unlink(new_root)


def test_yaml2nxdl_doc():
    """To test the doc style from yaml to nxdl."""
    pwd = Path(__file__).parent

    doc_file = pwd / "data/doc_yaml2nxdl.yaml"
    ref_doc_file = pwd / "data/ref_doc_yaml2nxdl.nxdl.xml"
    out_doc_file = (
        pwd / "data/doc_yaml2nxdl.nxdl.xml"
    )  # doc_file.with_suffix('.nxdl.xml')
    # Test yaml2nxdl
    # Generates '../data/doc_text.nxdl.xml'
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, ["--input-file", str(doc_file)])
    if result.exit_code != 0:
        Path.unlink(out_doc_file)
    assert result.exit_code == 0, f"Error: Having issue running input file {doc_file}."

    ref_nxdl = ET.parse(str(ref_doc_file)).getroot()
    out_nxdl = ET.parse(str(out_doc_file)).getroot()

    def compare_nxdl_doc(parent1, parent2):
        if len(parent1) > 0 and len(parent2) > 0:
            for par1, par2 in zip(parent1, parent2):
                compare_nxdl_doc(par1, par2)

        elif (
            remove_namespace_from_tag(parent1.tag) == "doc"
            and remove_namespace_from_tag(parent2.tag) == "doc"
        ):
            assert (
                parent1.text == parent2.text
            ), f"DOCS ARE NOT SAME: node {parent1}, node {parent2}"

    compare_nxdl_doc(ref_nxdl, out_nxdl)

    Path.unlink(out_doc_file)


def test_nxdl2yaml_doc():
    """To test the doc style from nxdl to yaml."""

    pwd = Path(__file__).parent
    nxdl_file = pwd / "data/doc_nxdl2yaml.nxdl.xml"
    ref_yaml = pwd / "data/ref_doc_nxdl2yaml.yaml"
    parsed_yaml_file = pwd / "data/doc_nxdl2yaml_parsed.yaml"

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, ["--input-file", str(nxdl_file), "--do-not-store-nxdl"]
    )

    if result.exit_code != 0:
        Path.unlink(parsed_yaml_file)

    assert result.exit_code == 0, "Error in converter execuation."

    with open(ref_yaml, mode="r", encoding="utf-8") as yaml1, open(
        parsed_yaml_file, mode="r", encoding="utf-8"
    ) as yaml2:
        yaml_dict1 = LineLoader(yaml1).get_single_data()
        yaml_dict2 = LineLoader(yaml2).get_single_data()

    def compare_yaml_doc(yaml_dict1, yaml_dict2):
        for k_val1, k_val2 in zip(yaml_dict1.items(), yaml_dict2.items()):
            key1, val1 = k_val1
            key2, val2 = k_val2
            if key1 == "doc" and key2 == "doc":
                assert val1 == val2, "Doc texts are not the same."
            elif isinstance(val1, dict) and isinstance(val2, dict):
                compare_yaml_doc(val1, val2)

    compare_yaml_doc(yaml_dict1, yaml_dict2)
    Path.unlink(parsed_yaml_file)


@pytest.mark.parametrize(
    "test_input,output,is_valid",
    [
        (
            """
    xref:
        spec: <spec>
        term: <term>
        url: <url>
    """,
            "    This concept is related to term `<term>`_ "
            "of the <spec> standard.\n.. _<term>: <url>",
            True,
        ),
        (
            """
    xref:
        spec: <spec>
         term: <term>
        url: <url>
    """,
            "Found invalid xref. Please make sure that your xref entries are valid yaml.",
            False,
        ),
        (
            """
    xref:
        spec: <spec>
        term: <term>
        url: <url>
        term: <term2>
    """,
            "Invalid xref. It contains nested or duplicate keys.",
            False,
        ),
        (
            """
    xref:
        spec: <spec>
        term: <term>
        url: <url>
        hallo: <term2>
    """,
            "Invalid xref. Too many keys.",
            False,
        ),
        (
            """
    xref:
        spec: <spec>
        my_key: <term>
        url: <url>
    """,
            "Invalid xref key `my_key`. Must be one of `term`, `spec` or `url`.",
            False,
        ),
        (
            """
    xref:
        spec: <spec>
        term:
            test: <nested_value>
        url: <url>
    """,
            "Invalid xref. It contains nested or duplicate keys.",
            False,
        ),
    ],
)
def test_handle_xref(test_input, output, is_valid):
    """
    Tests whether the xref generates a correct docstring.
    """
    if is_valid:
        assert handle_each_part_doc(test_input) == output
        return

    with pytest.raises(ValueError) as err:
        handle_each_part_doc(test_input)

    assert output == err.value.args[0]
