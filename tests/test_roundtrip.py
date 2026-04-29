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
Tests for bidirectional (roundtrip) conversions: nxdl→yaml→nxdl and yaml→nxdl→yaml.
"""

import os
import re
import sys
from pathlib import Path

import lxml.etree as ET
from click.testing import CliRunner
from helpers import check_file_fresh_baked, compare_yaml_content

from nyaml import cli as nyaml2nxdl
from nyaml import nyaml2nxdl as nyaml2nxdl_forward_tools
from nyaml.comment_collector import CommentCollector
from nyaml.helper import LineLoader
from nyaml.nyaml2nxdl import get_nxdl_copyright_license


def test_xml_parsing():
    """In this test an xml file is converted to yml and then back to xml.
    The xml trees of the two files are then compared.
    """
    ref_xml_file = "tests/data/Ref_NXellipsometry.nxdl.xml"
    test_yml_file = "tests/data/Ref_NXellipsometry_parsed.yaml"
    test_xml_file = "tests/data/Ref_NXellipsometry_parsed.nxdl.xml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [test_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)

    test_tree = ET.parse(test_xml_file)
    test_tree_flattened = {i.tag.split("}", 1)[1] for i in test_tree.iter()}

    ref_tree = ET.parse(ref_xml_file)
    ref_tree_flattened = {i.tag.split("}", 1)[1] for i in ref_tree.iter()}

    assert test_tree_flattened == ref_tree_flattened, (
        "Ref XML and parsed XML\
has not the same tree structure!!"
    )
    os.remove(test_xml_file)
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml -> xml okay.\n")


def test_yml_parsing():
    """In this test a yml file is converted to xml and then back to yml.
    The yml trees of the two files are then compared.
    """
    ref_yml_file = "tests/data/Ref_NXellipsometry.yaml"
    test_xml_file = "tests/data/Ref_NXellipsometry.nxdl.xml"
    test_yml_file = "tests/data/Ref_NXellipsometry_parsed.yaml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [ref_yml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_xml_file)
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [test_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    test_yml_tree = nyaml2nxdl_forward_tools.yml_reader(test_yml_file)

    ref_yml_tree = nyaml2nxdl_forward_tools.yml_reader(ref_yml_file)

    assert list(test_yml_tree) == list(ref_yml_tree), (
        "Ref YML and parsed YML \
has not the same root entries!!"
    )
    os.remove("tests/data/Ref_NXellipsometry_parsed.yaml")
    sys.stdout.write("Test on yml -> xml -> yml okay.\n")


def test_yml_consistency_comment_parsing():
    """Test comments parsing from yaml. Convert 'yaml' input file to '.nxdl.xml' and
    '.nxdl.xml' to '.yaml'
    """

    ref_yml_file = "tests/data/Ref_NXcomment.yaml"
    test_yml_file = "tests/data/Ref_NXcomment_consistency.yaml"

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, ["--check-consistency", ref_yml_file]
    )
    assert result.exit_code == 0, (
        f"Exception: {result.exception}, \nExecution Info:{{result.exc_info}}"
    )
    with open(ref_yml_file, encoding="utf-8") as ref_yml:
        loader = LineLoader(ref_yml)
        ref_loaded_yaml = loader.get_single_data()
    ref_comment_blocks = CommentCollector(ref_yml_file, ref_loaded_yaml)
    ref_comment_blocks.extract_all_comment_blocks()

    with open(test_yml_file, encoding="utf-8") as test_yml:
        loader = LineLoader(test_yml)
        test_loaded_yaml = loader.get_single_data()
    test_comment_blocks = CommentCollector(test_yml_file, test_loaded_yaml)
    test_comment_blocks.extract_all_comment_blocks()

    for reference_comment, test_comment in zip(ref_comment_blocks, test_comment_blocks):
        assert reference_comment == test_comment, "Comment is not consistent."

    os.remove(test_yml_file)


def test_conversion():
    """
    Test conversion of NXentry: nxdl -> yaml -> nxdl
    """
    root = Path(__file__).parent / "data" / "NXentry.nxdl.xml"
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [str(root)])
    assert result.exit_code == 0
    # Replace suffixes
    yaml = root.parent / Path(root.with_suffix("").stem + "_parsed.yaml")
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [str(yaml)])
    assert result.exit_code == 0
    new_root = yaml.with_suffix(".nxdl.xml")
    with open(root, encoding="utf-8") as tmp_f:
        root_content = tmp_f.readlines()
    with open(new_root, encoding="utf-8") as tmp_f:
        new_root_content = tmp_f.readlines()
    assert root_content == new_root_content
    Path.unlink(yaml)
    Path.unlink(new_root)


def test_check_copyright_license_in_full_modification_yaml_cycle(tmp_path):
    """Test that modifying a yaml (derived from nxdl) and converting back preserves
    the original license text.
    """
    pwd = Path(__file__).parent
    nxdl_file = pwd / "data" / "Ref_NXentry_License.nxdl.xml"
    yaml_file = tmp_path / "Ref_NXentry_License_parsed.yaml"
    modified_yaml_gen = tmp_path / "Ref_NXentry_License_modified.yaml"
    modified_yaml_ref = pwd / "data" / "Ref_NXentry_License_modified.yaml"
    latest_nxdl = tmp_path / "Ref_NXentry_License_modified.nxdl.xml"

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, [str(nxdl_file), "--output-file", str(yaml_file)]
    )
    assert result.exit_code == 0, (
        f"Error in converter execution input file {nxdl_file}."
    )
    content = yaml_file.read_text()
    find_pattern = r"my nice doc string in root level, line 2."
    replace_pattern = "my nice doc string in root level, line 2. Modified."
    updated_content = re.sub(find_pattern, replace_pattern, content)
    modified_yaml_gen.write_text(updated_content)
    # Compare two yaml and modified yaml
    with (
        open(modified_yaml_gen, encoding="utf-8") as gen_yaml,
        open(modified_yaml_ref, encoding="utf-8") as ref_yaml,
    ):
        gen_yaml_dict = LineLoader(gen_yaml).get_single_data()
        ref_yaml_dict = LineLoader(ref_yaml).get_single_data()
    compare_yaml_content(gen_yaml_dict, ref_yaml_dict, ["doc"])

    # Convert modified yaml to nxdl
    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool,
        [str(modified_yaml_gen), "--output-file", str(latest_nxdl)],
    )

    gen_license_text = get_nxdl_copyright_license(latest_nxdl)
    original_license_text = get_nxdl_copyright_license(nxdl_file)
    assert gen_license_text == original_license_text, "License text is not correct."


def test_check_copyright_license_in_modified_yaml(tmp_path):
    """While converting the modified yaml to nxdl the license text should
    come from stored nxdl file.
    """
    pwd = Path(__file__).parent
    yaml_file = pwd / "data/Ref_NXentry.yaml"
    modified_yaml = tmp_path / "NXentry_modified.yaml"
    output = tmp_path / "NXentry_modified.nxdl.xml"

    content = yaml_file.read_text()
    find_pattern = r"my nice doc string in root level, line 2."
    replace_pattern = "my nice doc string in root level, line 2. Modified."
    updated_content = re.sub(find_pattern, replace_pattern, content)
    modified_yaml.write_text(updated_content)

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, [str(modified_yaml), "--output-file", str(output)]
    )
    assert result.exit_code == 0, (
        f"Error in converter execution input file {modified_yaml}."
    )

    expected_text = (
        r"Copyright \(C\) 2010-2020 NeXus International Advisory Committee \(NIAC\)"
    )

    license_text = get_nxdl_copyright_license(output)
    assert license_text, "License text not found in nxdl file."
    text_list = re.findall(expected_text, license_text, re.DOTALL)

    assert len(text_list) == 1, "License text is not correct."
