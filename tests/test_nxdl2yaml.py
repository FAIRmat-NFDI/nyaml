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
Tests for nxdl -> nyaml conversion (nxdl2yaml direction).
"""

import filecmp
import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner

from nyaml import cli as nyaml_cli
from nyaml.helper import LineLoader

DATA = Path(__file__).parent / "data" / "nxdl2yaml"


def check_file_fresh_baked(test_file):
    path = Path(test_file)
    timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    assert timestamp == now, "yaml file not generated"


def compare_yaml_content(yaml_dict1, yaml_dict2, test_key_list):
    for k_val1, k_val2 in zip(yaml_dict1.items(), yaml_dict2.items()):
        key1, val1 = k_val1
        key2, val2 = k_val2
        for ref_key in test_key_list:
            if key1 == ref_key and key2 == ref_key:
                assert val1 == val2, f"{ref_key} content is not the same."
            elif isinstance(val1, dict) and isinstance(val2, dict):
                compare_yaml_content(val1, val2, test_key_list)


def test_nameType():
    ref_xml = DATA / "allowed_nameType.nxdl.xml"
    ref_yml = DATA / "ref_allowed_nameType.yaml"
    test_yml = DATA / "allowed_nameType_parsed.yaml"

    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(ref_xml)])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml)
    assert filecmp.cmp(ref_yml, test_yml, shallow=False), (
        "Ref YML and parsed YML don't have the same structure!"
    )
    os.remove(test_yml)
    sys.stdout.write("Test on xml -> yml nameType okay.\n")

    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(ref_xml)])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml)
    assert filecmp.cmp(ref_yml, test_yml, shallow=False), (
        "Ref YML and parsed YML don't have the same structure!!"
    )
    os.remove(test_yml)
    sys.stdout.write("Test on xml -> yml nameType (second run) okay.\n")


def test_doc_format_and_nxdl_part_as_comment():
    """Test doc format variety in NXDL->YAML and the stored NXDL comment at end of YAML."""
    ref_xml = DATA / "Ref_NXentry.nxdl.xml"
    ref_yml = DATA / "Ref_NXentry.yaml"
    test_yml = DATA / "Ref_NXentry_parsed.yaml"

    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(ref_xml)])
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml)
    assert filecmp.cmp(ref_yml, test_yml, shallow=False), (
        "Ref YML and parsed YML don't have the same structure!!"
    )
    os.remove(test_yml)
    sys.stdout.write("Test on xml -> yml doc formatting okay.\n")


def test_enumerations():
    ref_xml = DATA / "enumerations.nxdl.xml"
    ref_yml = DATA / "ref_enumerations.yaml"
    test_yml = DATA / "enumerations_parsed.yaml"

    result = CliRunner().invoke(
        nyaml_cli.launch_tool, ["--do-not-store-nxdl", str(ref_xml)]
    )
    assert result.exit_code == 0
    check_file_fresh_baked(test_yml)
    assert filecmp.cmp(ref_yml, test_yml, shallow=False), (
        "Ref YML and parsed YML don't have the same structure!"
    )
    os.remove(test_yml)
    sys.stdout.write("Test on xml -> yml enumerations okay.\n")


def test_doc():
    nxdl_file = DATA / "doc_nxdl2yaml.nxdl.xml"
    ref_yaml = DATA / "ref_doc_nxdl2yaml.yaml"
    parsed_yaml = DATA / "doc_nxdl2yaml_parsed.yaml"

    result = CliRunner().invoke(
        nyaml_cli.launch_tool, ["--do-not-store-nxdl", str(nxdl_file)]
    )
    if result.exit_code != 0:
        Path.unlink(parsed_yaml)
    assert result.exit_code == 0, "Error in converter execution."

    with (
        open(ref_yaml, encoding="utf-8") as yaml1,
        open(parsed_yaml, encoding="utf-8") as yaml2,
    ):
        yaml_dict1 = LineLoader(yaml1).get_single_data()
        yaml_dict2 = LineLoader(yaml2).get_single_data()

    compare_yaml_content(yaml_dict1, yaml_dict2, ["doc"])
    Path.unlink(parsed_yaml)


@pytest.mark.parametrize(
    "test_input",
    [
        "NXdimensionsType",
    ],
)
def test_backward_conversion(test_input):
    """Tests NXDL to YAML conversion; output must match Ref_ prefixed reference file."""
    test_xml = DATA / f"{test_input}.nxdl.xml"
    test_yml = DATA / f"{test_input}_parsed.yaml"
    ref_yml = DATA / f"Ref_{test_input}.yaml"

    result = CliRunner().invoke(nyaml_cli.launch_tool, [str(test_xml)])
    assert result.exit_code == 0

    with open(test_yml, encoding="utf-8") as logfile:
        log = logfile.readlines()
    with open(ref_yml, encoding="utf-8") as reffile:
        ref = reffile.readlines()
    assert log == ref

    os.remove(test_yml)
