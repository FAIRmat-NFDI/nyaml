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
Tests for nyaml -> nxdl conversion (yaml2nxdl direction).
"""

import os
import re
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import lxml.etree as ET
import pytest
import yaml
from click.testing import CliRunner

from nyaml import cli as nyaml_cli
from nyaml.helper import remove_namespace_from_tag
from nyaml.nyaml2nxdl import get_nxdl_copyright_license, handle_each_part_doc

LATEST_COPYRIGHT_YEAR = f"{datetime.now().year}-{datetime.now().year}"
LATEST_COPYRIGHT = rf"# Copyright \(C\) {LATEST_COPYRIGHT_YEAR} NeXus International Advisory Committee \(NIAC\)"
COPYRIGHT_REPLACEMENT = (
    f"# Copyright (C) 2010-2020 NeXus International Advisory Committee (NIAC)"
)

DATA = Path(__file__).parent / "data" / "yaml2nxdl"


def check_and_replace_latest_copyright(nxdl_file):
    content = nxdl_file.read_text()
    generated_copyright = re.findall(LATEST_COPYRIGHT, content, re.DOTALL)
    assert len(generated_copyright) == 1, (
        f"No copyright or not correct copyright year found in {nxdl_file}"
    )
    content = re.sub(LATEST_COPYRIGHT, COPYRIGHT_REPLACEMENT, content)
    nxdl_file.write_text(content)


def delete_duplicates(list_of_matching_string):
    return list(dict.fromkeys(list_of_matching_string))


def check_file_fresh_baked(test_file):
    path = Path(test_file)
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    assert timestamp == now, "xml file not generated"


def find_matches(xml_file, desired_matches):
    with open(xml_file, encoding="utf-8") as file:
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
    found_matches_clean = delete_duplicates(found_matches)
    assert len(found_matches_clean) == len(desired_matches), (
        "some desired_matches were \nnot found in file"
    )
    return [lines, lines_index]


def compare_matches(ref_xml_file, test_yml_file, test_xml_file, desired_matches):
    ref_matches = find_matches(ref_xml_file, desired_matches)
    runner = CliRunner()
    result = runner.invoke(nyaml_cli.launch_tool, [test_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)
    test_matches = find_matches(test_xml_file, desired_matches)
    assert test_matches == ref_matches


def test_links():
    ref_xml = DATA / "Ref_NXtest_links.nxdl.xml"
    test_yml = DATA / "NXtest_links.yaml"
    test_xml = DATA / "NXtest_links.nxdl.xml"
    desired_matches = ["<link", "/>"]
    compare_matches(str(ref_xml), str(test_yml), str(test_xml), desired_matches)
    os.remove(test_xml)
    sys.stdout.write("Test on links okay.\n")


def test_nametypes_nyaml2nxdl():
    ref_xml = DATA / "ref_allowed_nameType.nxdl.xml"
    test_yml = DATA / "allowed_nameType.yaml"
    test_xml = DATA / "allowed_nameType.nxdl.xml"
    desired_matches = ["partial", "specified", "any"]
    compare_matches(str(ref_xml), str(test_yml), str(test_xml), desired_matches)
    os.remove(test_xml)
    sys.stdout.write("Test on nameType okay.\n")


@pytest.mark.parametrize(
    "input_tuple, exit_code, expected_error",
    [
        # Wrong name type
        (
            ("groupGROUP(NXobject)", "my_name_type"),
            1,
            'Name "groupGROUP" has nameType="my_name_type", but only one of ("specified", "any", "partial") is allowed.',
        ),
        (
            ("my_field", "my_name_type"),
            1,
            'Name "my_field" has nameType="my_name_type", but only one of ("specified", "any", "partial") is allowed.',
        ),
        (
            (r"\@MYattribute", "my_name_type"),
            1,
            r'Name "\@MYattribute" has nameType="my_name_type", but only one of ("specified", "any", "partial") is allowed.',
        ),
        (
            ("link(link)", "my_name_type"),
            1,
            'Name "link(link)" has nameType="my_name_type", but only one of ("specified", "any", "partial") is allowed.',
        ),
        # Unnamed groups
        (
            ("(NXobject)", "specified"),
            1,
            'Unnamed group should have either no nameType or nameType="any". Found nameType="specified".',
        ),
        (
            ("(NXobject)", "partial"),
            1,
            'Unnamed group should have either no nameType or nameType="any". Found nameType="partial".',
        ),
        # Lower case names
        (
            ("lower_case_group_any(NXobject)", "any"),
            0,
            'Warning: Name "lower_case_group_any" (all lowercase) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            ("lower_case_field_any", "any"),
            0,
            'Warning: Name "lower_case_field_any" (all lowercase) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            (r"\@lower_case_attribute_any", "any"),
            0,
            r'Warning: Name "\@lower_case_attribute_any" (all lowercase) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            ("lower_case_link_any(link)", "any"),
            0,
            'Warning: Name "lower_case_link_any(link)" (all lowercase) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            ("lower_case_group_partial(NXobject)", "partial"),
            0,
            'Error: Name "lower_case_group_partial" (all lowercase) has nameType="partial", but nothing can be replaced. Consider introducing upper case letters or dropping nameType="partial".',
        ),
        (
            ("lower_case_field_partial", "partial"),
            0,
            'Error: Name "lower_case_field_partial" (all lowercase) has nameType="partial", but nothing can be replaced. Consider introducing upper case letters or dropping nameType="partial".',
        ),
        (
            (r"\@lower_case_attribute_partial:", "partial"),
            0,
            r'Error: Name "\@lower_case_attribute_partial:" (all lowercase) has nameType="partial", but nothing can be replaced. Consider introducing upper case letters or dropping nameType="partial".',
        ),
        (
            ("lower_case_link_any(link)", "partial"),
            0,
            'Error: Name "lower_case_link_any(link)" (all lowercase) has nameType="partial", but nothing can be replaced. Consider introducing upper case letters or dropping nameType="partial".',
        ),
        # Upper case names
        (
            ("OBJECT(NXobject)", "partial"),
            0,
            'Warning: Name "OBJECT" (all uppercase) has nameType="partial". Since the name only has uppercase letters, there is no difference to nameType="any".',
        ),
        (
            ("FIELD", "partial"),
            0,
            'Warning: Name "FIELD" (all uppercase) has nameType="partial". Since the name only has uppercase letters, there is no difference to nameType="any".',
        ),
        (
            (r"\@ATTRIBUTE", "partial"),
            0,
            r'Warning: Name "\@ATTRIBUTE" (all uppercase) has nameType="partial". Since the name only has uppercase letters, there is no difference to nameType="any".',
        ),
        (
            ("LINK(link)", "partial"),
            0,
            'Warning: Name "LINK(link)" (all uppercase) has nameType="partial". Since the name only has uppercase letters, there is no difference to nameType="any".',
        ),
        # Mixed upper and lower case names
        (
            ("objectOBJECTobjectOBJECT", ""),
            0,
            'Name "objectOBJECTobjectOBJECT" (mixed upper and lower case) has no nameType, assuming "specified".',
        ),
        (
            ("fieldFIELDfieldFIELD", ""),
            0,
            'Name "fieldFIELDfieldFIELD" (mixed upper and lower case) has no nameType, assuming "specified".',
        ),
        (
            (r"\@attributeATTRIBUTEattributeATTRIBUTE", ""),
            0,
            r'Name "\@attributeATTRIBUTEattributeATTRIBUTE" (mixed upper and lower case) has no nameType, assuming "specified".',
        ),
        (
            ("linkLINKlinkLINK(link)", ""),
            0,
            'Name "linkLINKlinkLINK(link)" (mixed upper and lower case) has no nameType, assuming "specified".',
        ),
        (
            ("objectOBJECTobjectOBJECT", "any"),
            0,
            'Warning: Name "objectOBJECTobjectOBJECT" (mixed upper and lower case) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            ("fieldFIELDfieldFIELD", "any"),
            0,
            'Warning: Name "fieldFIELDfieldFIELD" (mixed upper and lower case) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            (r"\@attributeATTRIBUTEattributeATTRIBUTE", "any"),
            0,
            r'Warning: Name "\@attributeATTRIBUTEattributeATTRIBUTE" (mixed upper and lower case) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
        (
            ("linkLINKlinkLINK", "any"),
            0,
            'Warning: Name "linkLINKlinkLINK" (mixed upper and lower case) has nameType="any", which makes it fully renameable. Is that intentional?',
        ),
    ],
)
def test_prohibited_nameType(tmp_path, input_tuple, exit_code, expected_error):
    """Run nyaml2nxdl on individual incorrect elements and check errors."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    key, name_type_value = input_tuple

    yaml_data = OrderedDict(
        {
            "category": "base",
            "doc": "Test",
            "NXtest": OrderedDict({key: {r"\nameType": name_type_value}}),
        }
    )

    test_file = Path(tmp_path) / "test.yaml"
    with open(test_file, "w") as file:
        yaml.dump(yaml_data, file, default_flow_style=False, allow_unicode=True)

    runner = CliRunner()
    result = runner.invoke(
        nyaml_cli.launch_tool,
        [str(test_file), "--output-file", str(Path(tmp_path) / "out.nxdl.xml")],
    )

    assert result.exit_code == exit_code
    assert expected_error in (str(result.output) + str(result.exception))


def test_fileline_error():
    for n, expected_line in [(1, "13"), (2, "21"), (3, "25")]:
        test_yml = DATA / f"NXfilelineError{n}.yaml"
        out_nxdl = DATA / f"NXfilelineError{n}.nxdl.xml"
        out_yaml = DATA / f"temp_NXfilelineError{n}.yaml"
        result = CliRunner().invoke(nyaml_cli.launch_tool, [str(test_yml)])
        assert result.exit_code == 1
        assert expected_line in str(result.exception)
        os.remove(out_nxdl)
        os.remove(out_yaml)
    sys.stdout.write("Test on fileline error handling okay.\n")


def test_symbols():
    ref_xml = DATA / "Ref_NXnested_symbols.nxdl.xml"
    test_yml = DATA / "NXnested_symbols.yaml"
    test_xml = DATA / "NXnested_symbols.nxdl.xml"
    desired_matches = ["<symbols>", "</symbols>", "<symbols"]
    compare_matches(str(ref_xml), str(test_yml), str(test_xml), desired_matches)
    os.remove(test_xml)
    sys.stdout.write("Test on symbols okay.\n")


def test_symbols_and_enum_docs():
    ref_xml = DATA / "Ref_NXmytests.nxdl.xml"
    test_yml = DATA / "NXmytests.yaml"
    test_xml = DATA / "NXmytests.nxdl.xml"
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
    compare_matches(str(ref_xml), str(test_yml), str(test_xml), desired_matches)
    os.remove(test_xml)
    sys.stdout.write("Test on docs in enumeration and symbols okay.\n")


def test_enumerations():
    ref_xml = DATA / "ref_enumerations.nxdl.xml"
    test_yml = DATA / "enumerations.yaml"
    test_xml = DATA / "enumerations.nxdl.xml"
    desired_matches = [
        "<enumeration",
        "</enumeration>",
        "<item",
        "</item>",
        "<doc>",
        "</doc>",
        "<!--",
    ]
    compare_matches(str(ref_xml), str(test_yml), str(test_xml), desired_matches)
    os.remove(test_xml)
    sys.stdout.write("Test on open/closed enumerations okay.\n")


def test_doc():
    pwd = Path(__file__).parent
    doc_file = DATA / "doc_yaml2nxdl.yaml"
    ref_doc_file = DATA / "ref_doc_yaml2nxdl.nxdl.xml"
    out_doc_file = DATA / "doc_yaml2nxdl.nxdl.xml"

    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(doc_file)])
    if result.exit_code != 0:
        Path.unlink(out_doc_file)
    assert result.exit_code == 0, f"Error running {doc_file}."
    check_and_replace_latest_copyright(out_doc_file)
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
            assert parent1.text == parent2.text, (
                f"DOCS ARE NOT SAME: node {parent1}, node {parent2}"
            )

    compare_nxdl_doc(ref_nxdl, out_nxdl)
    Path.unlink(out_doc_file)


def test_no_tabs(tmp_path):
    doc_file = DATA / "no_tabs_yaml2nxdl.yaml"
    ref_doc_file = DATA / "ref_no_tabs_yaml2nxdl.nxdl.xml"
    out_doc_file = tmp_path / "no_tabs_yaml2nxdl.nxdl.xml"

    result = CliRunner().invoke(
        nyaml_cli.launch_tool, [str(doc_file), "--output-file", str(out_doc_file)]
    )
    assert result.exit_code == 0, f"Error running {doc_file}."
    check_and_replace_latest_copyright(out_doc_file)
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
            assert parent1.text == parent2.text, (
                f"DOCS ARE NOT SAME: node {parent1}, node {parent2}"
            )

    compare_nxdl_doc(ref_nxdl, out_nxdl)


def test_copyright_license_new_yaml(tmp_path):
    pass


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
            "This concept is related to term `<term>`_ "
            "of the <spec> standard.\n\n.. _<term>: <url>",
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
    """Tests whether the xref generates a correct docstring."""
    if is_valid:
        assert handle_each_part_doc(test_input) == output
        return

    with pytest.raises(ValueError) as err:
        handle_each_part_doc(test_input)

    assert output == err.value.args[0]


@pytest.mark.parametrize(
    "test_input",
    [
        "NXattributes",
        "NXcomment",
        "NXdimensionsType",
        "NXellipsometry-docCheck",
        "NXfit",
    ],
)
def test_forward_conversion(test_input):
    """Tests YAML to NXDL conversion; output must match Ref_ prefixed reference file."""
    test_yml = DATA / f"{test_input}.yaml"
    test_xml = DATA / f"{test_input}.nxdl.xml"
    ref_xml = DATA / f"Ref_{test_input}.nxdl.xml"
    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(test_yml)])
    assert result.exit_code == 0

    check_and_replace_latest_copyright(test_xml)

    with open(test_xml, encoding="utf-8") as logfile:
        log = logfile.readlines()
    with open(ref_xml, encoding="utf-8") as reffile:
        ref = reffile.readlines()
    assert log == ref

    os.remove(test_xml)


@pytest.mark.parametrize(
    "keyword",
    sorted(
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
            "rank",
        }
    ),
)
def test_reserved_keyword_as_field_name(tmp_path, keyword):
    """A bare (unescaped) reserved keyword as a YAML key inside a group must
    produce <field name="<keyword>"/> in the NXDL output, not activate keyword
    dispatch (which requires the \\keyword escape prefix)."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    yaml_data = OrderedDict(
        {
            "category": "base",
            "doc": "Reserved keyword concept test",
            "NXtest": OrderedDict({keyword: None}),
        }
    )

    test_file = tmp_path / "test.yaml"
    out_file = tmp_path / "test.nxdl.xml"
    with open(test_file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    result = CliRunner().invoke(
        nyaml_cli.launch_tool,
        [str(test_file), "--output-file", str(out_file)],
    )
    assert result.exit_code == 0, f"Conversion failed: {result.output}"

    tree = ET.parse(str(out_file))
    fields = [
        el
        for el in tree.iter()
        if remove_namespace_from_tag(el.tag) == "field" and el.get("name") == keyword
    ]
    assert len(fields) == 1, (
        f"Expected exactly one <field name='{keyword}'/> for bare '{keyword}', "
        f"got {len(fields)}"
    )
