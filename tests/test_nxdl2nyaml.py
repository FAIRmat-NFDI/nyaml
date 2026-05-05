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
Tests for the NXDL → YAML conversion direction (nxdl2nyaml).
"""

import filecmp
import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner
from helpers import (
    check_file_fresh_baked,
    compare_log_and_reference,
    compare_yaml_content,
)

from nyaml import cli as nyaml2nxdl
from nyaml.helper import LineLoader

NXDL2NYAML_DATA_DIR = Path(__file__).parent / "data" / "nxdl2yaml"


def test_nxdl2yaml_nameType():
    """
    Check the correct handling of the nameType attribute for the direction
    nxdl->nyaml.
    """
    ref_xml_file = str(NXDL2NYAML_DATA_DIR / "allowed_nameType.nxdl.xml")
    ref_yml_file = str(NXDL2NYAML_DATA_DIR / "ref_allowed_nameType.yaml")
    test_yml_file = str(NXDL2NYAML_DATA_DIR / "allowed_nameType_parsed.yaml")

    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    result = filecmp.cmp(ref_yml_file, test_yml_file, shallow=False)

    assert result, "Ref YML and parsed YML don't have the same structure!"
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml nameType okay.\n")

    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    result = filecmp.cmp(ref_yml_file, test_yml_file, shallow=False)
    assert result, (
        "Ref YML and parsed YML\
has not the same structure!!"
    )
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml doc formatting okay.\n")


@pytest.mark.parametrize(
    "test_input",
    [
        ("NXdimensionsType"),
    ],
)
def test_dimension(test_input):
    """
    Tests if the conversion of specific test files from NXDL to YAML results as expected.
    Expected output files shall have the corresponding name with the prefix Ref_.
    """
    test_xml_input_file = str(NXDL2NYAML_DATA_DIR / f"{test_input}.nxdl.xml")
    test_yml_output_file = str(NXDL2NYAML_DATA_DIR / f"{test_input}_parsed.yaml")
    ref_yml_output_file = str(NXDL2NYAML_DATA_DIR / f"Ref_{test_input}.yaml")
    runner = CliRunner()
    result = runner.invoke(nyaml2nxdl.launch_tool, [test_xml_input_file])
    assert result.exit_code == 0

    compare_log_and_reference(test_yml_output_file, ref_yml_output_file)

    os.remove(test_yml_output_file)


def test_nxdl2yaml_doc_format_and_nxdl_part_as_comment():
    """
    This test for two reasons:
            1. In test-1 an nxdl file with all kind of doc formats are translated
    to yaml to check if they are correct.
            2. In test-2: Check the nxdl that comes at the end of yaml file as comment.
    """
    ref_xml_file = str(NXDL2NYAML_DATA_DIR / "Ref_NXentry.nxdl.xml")
    ref_yml_file = str(NXDL2NYAML_DATA_DIR / "Ref_NXentry.yaml")
    test_yml_file = str(NXDL2NYAML_DATA_DIR / "Ref_NXentry_parsed.yaml")
    result = CliRunner().invoke(nyaml2nxdl.launch_tool, [ref_xml_file])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    result = filecmp.cmp(ref_yml_file, test_yml_file, shallow=False)
    assert result, (
        "Ref YML and parsed YML\
has not the same structure!!"
    )
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml doc formatting okay.\n")


def test_nxdl2yaml_enumerations():
    """
    Check the correct handling of enumerations (closed and open ones) for the direction
    nxdl->nyaml.
    """
    ref_xml_file = str(NXDL2NYAML_DATA_DIR / "enumerations.nxdl.xml")
    ref_yml_file = str(NXDL2NYAML_DATA_DIR / "ref_enumerations.yaml")
    test_yml_file = str(NXDL2NYAML_DATA_DIR / "enumerations_parsed.yaml")

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, ["--do-not-store-nxdl", str(ref_xml_file)]
    )
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml_file)

    result = filecmp.cmp(ref_yml_file, test_yml_file, shallow=False)

    assert result, "Ref YML and parsed YML don't have the same structure!"
    os.remove(test_yml_file)
    sys.stdout.write("Test on xml -> yml doc formatting okay.\n")


def test_nxdl2yaml_doc():
    """To test the doc style from nxdl to yaml."""

    nxdl_file = str(NXDL2NYAML_DATA_DIR / "doc_nxdl2yaml.nxdl.xml")
    ref_yaml = str(NXDL2NYAML_DATA_DIR / "ref_doc_nxdl2yaml.yaml")
    parsed_yaml_file = str(NXDL2NYAML_DATA_DIR / "doc_nxdl2yaml_parsed.yaml")

    result = CliRunner().invoke(
        nyaml2nxdl.launch_tool, ["--do-not-store-nxdl", str(nxdl_file)]
    )

    if result.exit_code != 0:
        os.remove(parsed_yaml_file)

    assert result.exit_code == 0, "Error in converter execution."

    with (
        open(ref_yaml, encoding="utf-8") as yaml1,
        open(parsed_yaml_file, encoding="utf-8") as yaml2,
    ):
        yaml_dict1 = LineLoader(yaml1).get_single_data()
        yaml_dict2 = LineLoader(yaml2).get_single_data()

    compare_yaml_content(yaml_dict1, yaml_dict2, ["doc"])
    os.remove(parsed_yaml_file)


@pytest.mark.parametrize(
    "test_input",
    [
        "NXattributes",
        "NXdimensionsType",
    ],
)
def test_backward_conversion(test_input):
    """
    Tests if the conversion of specific test files from NXDL to YAML results as expected.
    Expected output files shall have the corresponding name with the prefix Ref_.
    """
    test_xml_input_file = str(NXDL2NYAML_DATA_DIR / f"{test_input}.nxdl.xml")
    test_yml_output_file = str(NXDL2NYAML_DATA_DIR / f"{test_input}_parsed.yaml")
    ref_yml_output_file = str(NXDL2NYAML_DATA_DIR / f"Ref_{test_input}.yaml")
    runner = CliRunner()
    result = runner.invoke(nyaml2nxdl.launch_tool, [test_xml_input_file])
    assert result.exit_code == 0

    compare_log_and_reference(test_yml_output_file, ref_yml_output_file)

    os.remove(test_yml_output_file)
