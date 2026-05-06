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
Tests for the YAML → NXDL conversion direction (nyaml2nxdl).
"""

import os
import sys
from collections import OrderedDict
from pathlib import Path

import lxml.etree as ET
import pytest
import yaml
from click.testing import CliRunner
from helpers import check_and_replace_latest_copyright, compare_matches

from nyaml import cli as nyaml2nxdl
from nyaml.helper import (
    LIMITED_RESERVED_KEYWORDS,
    RESERVED_KEYWORDS,
    remove_namespace_from_tag,
)
from nyaml.nyaml2nxdl import handle_each_part_doc

NYAML2NXDL_DATA_DIR = Path(__file__).parent / "data" / "yaml2nxdl"


def test_links():
    """
    Check the correct parsing of links
    """
    ref_xml_link_file = str(NYAML2NXDL_DATA_DIR / "Ref_NXtest_links.nxdl.xml")
    test_yml_link_file = str(NYAML2NXDL_DATA_DIR / "NXtest_links.yaml")
    test_xml_link_file = str(NYAML2NXDL_DATA_DIR / "NXtest_links.nxdl.xml")
    # ref_xml_link_file = os.path.abspath(data_path + '/Ref_NXtest_links.nxdl.xml')
    # test_yml_link_file = os.path.abspath(data_path + '/NXtest_links.yaml')
    # test_xml_link_file = os.path.abspath(data_path + '/NXtest_links.nxdl.xml')
    desired_matches = ["<link", "/>"]
    compare_matches(
        ref_xml_link_file, test_yml_link_file, test_xml_link_file, desired_matches
    )
    os.remove(test_xml_link_file)
    sys.stdout.write("Test on links okay.\n")


def test_nametypes_nyaml2nxdl():
    """
    Check the correct handling of the nameType attribute for the direction
    nyaml->nxdl.
    """
    ref_xml_file = str(NYAML2NXDL_DATA_DIR / "ref_allowed_nameType.nxdl.xml")
    test_yml_file = str(NYAML2NXDL_DATA_DIR / "allowed_nameType.yaml")
    test_xml_file = str(NYAML2NXDL_DATA_DIR / "allowed_nameType.nxdl.xml")
    desired_matches = ["partial", "specified", "any"]
    compare_matches(ref_xml_file, test_yml_file, test_xml_file, desired_matches)
    os.remove(test_xml_file)
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
def test_nyaml2nxdl_prohibited_nameType(
    tmp_path, input_tuple, exit_code, expected_error
):
    """Run nyaml2nxdl on individual incorrect elements and check errors."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    key, name_type_value = input_tuple

    yaml_data = OrderedDict(
        {
            r"\category": "base",
            r"\doc": "Test",
            "NXtest": OrderedDict({key: {r"\nameType": name_type_value}}),
        }
    )

    test_file = Path(tmp_path) / "test.yaml"
    output_file = Path(tmp_path) / "out.nxdl.xml"
    with open(test_file, "w") as file:
        yaml.dump(yaml_data, file, default_flow_style=False, allow_unicode=True)

    runner = CliRunner()
    result = runner.invoke(
        nyaml2nxdl.launch_tool,
        [str(test_file), "--output-file", str(output_file)],
    )

    assert result.exit_code == exit_code
    assert expected_error in (str(result.output) + str(result.exception))
    os.remove(test_file)
    os.remove(output_file)


def test_file_line_error():
    """
    In this test the yaml file line in the error message is tested.
    """
    for n, expected_line in [(1, "13"), (2, "21"), (3, "25")]:
        test_yml = NYAML2NXDL_DATA_DIR / f"NXfilelineError{n}.yaml"
        out_nxdl = NYAML2NXDL_DATA_DIR / f"NXfilelineError{n}.nxdl.xml"
        out_yaml = NYAML2NXDL_DATA_DIR / f"temp_NXfilelineError{n}.yaml"
        result = CliRunner().invoke(nyaml2nxdl.launch_tool, [str(test_yml)])
        assert result.exit_code == 1
        assert expected_line in str(result.exception)
        os.remove(out_nxdl)
        os.remove(out_yaml)
    sys.stdout.write("Test on xml -> yml file line error handling okay.\n")


def test_symbols():
    """
    Check the correct parsing of symbols
    """
    ref_xml_symbol_file = str(NYAML2NXDL_DATA_DIR / "Ref_NXnested_symbols.nxdl.xml")
    test_yml_symbol_file = str(NYAML2NXDL_DATA_DIR / "NXnested_symbols.yaml")
    test_xml_symbol_file = str(NYAML2NXDL_DATA_DIR / "NXnested_symbols.nxdl.xml")
    desired_matches = ["<symbols>", "</symbols>", "<symbols"]
    compare_matches(
        ref_xml_symbol_file, test_yml_symbol_file, test_xml_symbol_file, desired_matches
    )
    os.remove(str(NYAML2NXDL_DATA_DIR / "NXnested_symbols.nxdl.xml"))
    sys.stdout.write("Test on symbols okay.\n")


def test_symbols_and_enum_docs():
    """
        Check the correct handling of empty attributes
    or attributes fields, e.g. doc
    """
    ref_xml_file = str(NYAML2NXDL_DATA_DIR / "Ref_NXmytests.nxdl.xml")
    test_yml_file = str(NYAML2NXDL_DATA_DIR / "NXmytests.yaml")
    test_xml_file = f"{NYAML2NXDL_DATA_DIR}/NXmytests.nxdl.xml"
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
    compare_matches(
        str(ref_xml_file), str(test_yml_file), str(test_xml_file), desired_matches
    )
    os.remove(f"{NYAML2NXDL_DATA_DIR}/NXmytests.nxdl.xml")
    sys.stdout.write("Test on docs in enumeration and symbols okay.\n")


def test_enumerations_nyaml2nxdl():
    """
    Check the correct handling of enumerations (closed and open ones) for the direction
    nyaml->nxdl.
    """
    ref_xml = NYAML2NXDL_DATA_DIR / "ref_enumerations.nxdl.xml"
    test_yml = NYAML2NXDL_DATA_DIR / "enumerations.yaml"
    test_xml = NYAML2NXDL_DATA_DIR / "enumerations.nxdl.xml"
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


def test_yaml2nxdl_doc():
    """To test the doc style from yaml to nxdl."""

    doc_file = str(NYAML2NXDL_DATA_DIR / "doc_yaml2nxdl.yaml")
    ref_doc_file = str(NYAML2NXDL_DATA_DIR / "ref_doc_yaml2nxdl.nxdl.xml")
    out_doc_file = str(
        NYAML2NXDL_DATA_DIR / "doc_yaml2nxdl.nxdl.xml"
    )  # doc_file.with_suffix('.nxdl.xml')
    # Test yaml2nxdl
    # Generates '../data/doc_text.nxdl.xml'
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [doc_file])
    if result.exit_code != 0:
        os.remove(out_doc_file)
    assert result.exit_code == 0, f"Error: Having issue running input file {doc_file}."
    # Check copyright year and replace it according to the ref file
    check_and_replace_latest_copyright(Path(out_doc_file))
    ref_nxdl = ET.parse(ref_doc_file).getroot()
    out_nxdl = ET.parse(out_doc_file).getroot()

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

    os.remove(out_doc_file)


def test_yaml2nxdl_no_tabs(tmp_path):
    """
    Test the proper conversion of yaml2nxdl without producing tabs.
    """

    doc_file = NYAML2NXDL_DATA_DIR / "no_tabs_yaml2nxdl.yaml"
    ref_doc_file = NYAML2NXDL_DATA_DIR / "ref_no_tabs_yaml2nxdl.nxdl.xml"
    out_doc_file = tmp_path / "no_tabs_yaml2nxdl.nxdl.xml"
    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, [str(doc_file), "--output-file", str(out_doc_file)]
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


# the copyright-year needs to be a part of the yaml file as not necessarily
# every yaml file that gets a yaml2nxdl conversion is necessarily a new definition
# namely the current use case does not allow people to recover accidentally
# removed XML files when they still have their corresponding YAML file, upon conversion
# the copyright will then be changed to a copyright year as if the definition was
# just defined completely from scratch anew which is incorrect.
def test_copyright_license_new_yaml(tmp_path):
    pass
    """While converting the newly developed yaml to nxdl the license text should have
    the latest year.
    """
    """
    pwd = Path(__file__).parent
    input_file = pwd / "data/dim_keyword.yaml"
    output = tmp_path / "dim_keyword.nxdl.xml"

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, [str(input_file), "--output-file", str(output)]
    )
    assert result.exit_code == 0, (
        f"Error in converter execution input file {input_file}."
    )
    # Check if the latest copyright year is written
    check_and_replace_latest_copyright(output)
    """


@pytest.mark.parametrize(
    "test_input,output,is_valid",
    [
        (
            """
    \\xref:
        \\spec: <spec>
        \\term: <term>
        \\url: <url>
    """,
            "This concept is related to term `<term>`_ "
            "of the <spec> standard.\n\n.. _<term>: <url>",
            True,
        ),
        (
            """
    \\xref:
        \\spec: <spec>
         \\term: <term>
        \\url: <url>
    """,
            "Found invalid xref. Please make sure that your xref entries are valid yaml.",
            False,
        ),
        (
            """
    \\xref:
        \\spec: <spec>
        \\term: <term>
        \\url: <url>
        \\term: <term2>
    """,
            "Invalid xref. It contains nested or duplicate keys.",
            False,
        ),
        (
            """
    \\xref:
        \\spec: <spec>
        \\term: <term>
        \\url: <url>
        \\hallo: <term2>
    """,
            "Invalid xref. Too many keys.",
            False,
        ),
        (
            """
    \\xref:
        \\spec: <spec>
        \\my_key: <term>
        \\url: <url>
    """,
            "Invalid xref key `\\my_key`. Must be one of `\\term`, `\\spec` or `\\url`.",
            False,
        ),
        (
            """
    \\xref:
        \\spec: <spec>
        \\term:
            test: <nested_value>
        \\url: <url>
    """,
            "Invalid xref. It contains nested or duplicate keys.",
            False,
        ),
        (
            """
    \\xref:
        spec: <spec>
        \\term: <term>
        \\url: <url>
    """,
            "Invalid xref key `spec`. Must be one of `\\term`, `\\spec` or `\\url`.",
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
        ("NXattributes"),
        ("NXcomment"),
        ("NXdimensionsType"),
        ("NXellipsometry-docCheck"),
        ("NXfit"),
    ],
)
def test_forward_conversion(test_input):
    """
    Tests if the conversion of specific test files from YAML to NXDL results as expected.
    Expected output files shall have the corresponding name with the prefix Ref_.
    """

    test_yml_input_file = str(NYAML2NXDL_DATA_DIR / f"{test_input}.yaml")
    test_xml_output_file = str(NYAML2NXDL_DATA_DIR / f"{test_input}.nxdl.xml")
    ref_xml_output_file = str(NYAML2NXDL_DATA_DIR / f"Ref_{test_input}.nxdl.xml")
    runner = CliRunner()
    result = runner.invoke(nyaml2nxdl.launch_tool, [str(test_yml_input_file)])
    assert result.exit_code == 0

    check_and_replace_latest_copyright(Path(test_xml_output_file))

    with open(test_xml_output_file, encoding="utf-8") as logfile:
        log = logfile.readlines()
    with open(ref_xml_output_file, encoding="utf-8") as reference_file:
        ref = reference_file.readlines()
    assert log == ref

    os.remove(test_xml_output_file)


@pytest.mark.parametrize("keyword", sorted(RESERVED_KEYWORDS))
def test_reserved_keyword_as_field_name(tmp_path, keyword):
    """A bare (unescaped) reserved keyword as a YAML key inside a group must
    produce <field name="<keyword>"/> in the NXDL output, not activate keyword
    dispatch (which requires the \\keyword escape prefix)."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    yaml_data = OrderedDict(
        {
            r"\category": "base",
            r"\doc": "Reserved keyword concept test",
            "NXtest": OrderedDict({keyword: None}),
        }
    )

    test_file = tmp_path / "test.yaml"
    out_file = tmp_path / "test.nxdl.xml"
    with open(test_file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool,
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


@pytest.mark.parametrize(
    "keyword",
    LIMITED_RESERVED_KEYWORDS["definition"] - RESERVED_KEYWORDS,
)
def test_definition_keyword_as_field_name(tmp_path, keyword):
    """A bare (unescaped) definition-context keyword used as a YAML key inside a
    group body must produce <field name="<keyword>"/> in the NXDL output, not
    activate any definition-level behavior (which only applies at the root level
    and requires the \\keyword escape prefix there)."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    yaml_data = OrderedDict(
        {
            r"\category": "base",
            r"\doc": "Definition-context keyword concept test",
            "NXtest": OrderedDict({keyword: None}),
        }
    )

    test_file = tmp_path / "test.yaml"
    out_file = tmp_path / "test.nxdl.xml"
    with open(test_file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool,
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


@pytest.mark.parametrize(
    "escaped_attr, xml_attr, xml_attr_value",
    [
        (r"\target", "target", "/entry"),
        (r"\napimount", "napimount", "nxfile://path/to/file#/entry"),
        (r"\nameType", "nameType", "any"),
    ],
)
def test_link_keywords_as_xml_attributes(
    tmp_path, escaped_attr, xml_attr, xml_attr_value
):
    """Escaped link-context keywords (\\target, \\napimount, \\nameType) inside a
    link body must produce the corresponding XML attribute on <link>, not a child
    field element."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    yaml_data = OrderedDict(
        {
            r"\category": "base",
            r"\doc": "Link-context keyword test",
            "NXtest": OrderedDict(
                {"my_link(link)": OrderedDict({escaped_attr: xml_attr_value})}
            ),
        }
    )

    test_file = tmp_path / "test.yaml"
    out_file = tmp_path / "test.nxdl.xml"
    with open(test_file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool,
        [str(test_file), "--output-file", str(out_file)],
    )
    assert result.exit_code == 0, f"Conversion failed: {result.output}"

    tree = ET.parse(str(out_file))
    links = [el for el in tree.iter() if remove_namespace_from_tag(el.tag) == "link"]
    assert len(links) == 1, f"Expected exactly one <link> element, got {len(links)}"
    assert links[0].get(xml_attr) == xml_attr_value, (
        f"Expected <link {xml_attr}='{xml_attr_value}'/>, "
        f"got {xml_attr}='{links[0].get(xml_attr)}'"
    )


@pytest.mark.parametrize(
    "keyword",
    sorted(LIMITED_RESERVED_KEYWORDS["definition"] | {"doc", "symbols"}),
)
def test_bare_definition_keyword_at_root_raises_error(tmp_path, keyword):
    """A bare (unescaped) definition-level keyword at the root of the YAML must
    raise an error. These keywords (category, doc, symbols, type, deprecated, …)
    require the \\keyword escape prefix at the root level; without it they are
    ambiguous and should never silently activate definition behavior."""

    def ordered_dict_representer(dumper, value):
        return dumper.represent_mapping("tag:yaml.org,2002:map", value.items())

    yaml.add_representer(OrderedDict, ordered_dict_representer)

    # Build a valid root definition but inject the bare keyword alongside it
    yaml_data = OrderedDict(
        {
            r"\category": "base",
            r"\doc": "Bare definition keyword test",
            keyword: "some_value",  # bare, no \ prefix — must be rejected
            "NXtest": None,
        }
    )

    test_file = tmp_path / "test.yaml"
    out_file = tmp_path / "test.nxdl.xml"
    with open(test_file, "w") as f:
        yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True)

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool,
        [str(test_file), "--output-file", str(out_file)],
    )
    assert result.exit_code != 0, (
        f"Expected non-zero exit for bare root-level keyword '{keyword}', but got 0"
    )
    assert keyword in str(result.output) + str(result.exception), (
        f"Expected keyword '{keyword}' to appear in the error output"
    )
