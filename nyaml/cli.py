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
Main file of nyaml2nxdl tool.

To write a definition for a instrument, experiment and/or process in nxdl.xml file from a YAML
file which details a hierarchy of data/metadata elements. It also allows both wa
conversion beteen YAML and nxdl.xml files that follows rules of NeXus ontology or data format.
"""
from pathlib import Path

import click

from nyaml.helper import (
    extend_yamlfile_by_nxdl_as_comment,
    get_sha256_hash,
    separate_hash_yaml_and_nxdl,
)
from nyaml.nxdl2nyaml import Nxdl2yaml
from nyaml.nyaml2nxdl import nyaml2nxdl

DEPTH_SIZE = 4 * " "
NXDL_SUFFIX = ".nxdl.xml"

# NOTE: Some handful links for nyaml2nxdl converter:
# https://manual.nexusformat.org/nxdl_desc.html?highlight=optional


def generate_nxdl_or_retrieve_nxdl(yaml_file, out_xml_file, verbose):
    """
    Generate yaml, nxdl and hash.

    If the extracted hash is exactly the same as produced from generated yaml then
    retrieve the nxdl part from provided yaml.
    Else, generate nxdl from separated yaml with the help of nyaml2nxdl function
    """
    file_path = Path(yaml_file)
    pa_path, rel_file = file_path.parent, file_path.name
    sep_yaml = (pa_path / f"temp_{rel_file}").as_posix()
    hash_found = separate_hash_yaml_and_nxdl(yaml_file, sep_yaml, out_xml_file)

    if hash_found:
        gen_hash = get_sha256_hash(sep_yaml)
        if hash_found == gen_hash:
            Path(sep_yaml).unlink()
            return

    nyaml2nxdl(sep_yaml, out_xml_file, verbose)
    Path(sep_yaml).unlink()


def split_name_and_extension(file_path):
    """
    Split file name into extension and rest of the file name.

    return file raw name and extension
    """
    path = Path(file_path)
    ext = "".join(path.suffixes)
    full_path_stem = file_path[0 : file_path.index(ext)]
    return full_path_stem, ext[1:]


@click.command()
@click.argument("input-file")
@click.option(
    "--output-file",
    required=False,
    help="Specify the output file path for the converted file.",
)
@click.option(
    "--check-consistency",
    is_flag=True,
    default=False,
    help=(
        "Check whether YAML and NXDL can be recursively converted, "
        "ensuring version consistency."
    ),
)
@click.option(
    "--do-not-store-nxdl",
    is_flag=True,
    default=False,
    help=(
        "Prevent the input NXDL file from being stored as a "
        "comment at the end of the output YAML file."
    ),
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help=(
        "Display keywords and value types in standard output "
        "to assist in identifying issues in YAML files."
    ),
)
# def launch_tool(input_file, verbose, check_consistency):
def launch_tool(input_file, verbose, do_not_store_nxdl, check_consistency, output_file):
    """
    Main function that distinguishes the input file format and launches the tools.
    """

    if Path(input_file).is_file():
        raw_name, ext = split_name_and_extension(input_file)
    else:
        raise ValueError("Need a valid input file.")
    if ext == "yaml":
        xml_out_file = (
            f"{raw_name}{NXDL_SUFFIX}" if output_file is None else output_file
        )
        generate_nxdl_or_retrieve_nxdl(input_file, xml_out_file, verbose)

        # For consistency running
        if check_consistency:
            yaml_out_file = f"{raw_name}_consistency.{ext}"
            converter = Nxdl2yaml([], [])
            converter.print_yml(xml_out_file, yaml_out_file, verbose)
            Path(xml_out_file).unlink()
    elif ext == "nxdl.xml":
        # if not append:
        yaml_out_file = (
            f"{raw_name}_parsed.yaml" if output_file is None else output_file
        )
        converter = Nxdl2yaml([], [])
        converter.print_yml(input_file, yaml_out_file, verbose)
        # Store nxdl.xml file in output yaml file under SHA HASH
        yaml_hash = get_sha256_hash(yaml_out_file)
        # Lines as divider between yaml and nxdl
        top_lines = [
            (
                "\n# ++++++++++++++++++++++++++++++++++ SHA HASH"
                " ++++++++++++++++++++++++++++++++++\n"
            ),
            f"# {yaml_hash}\n",
        ]
        if not do_not_store_nxdl:
            extend_yamlfile_by_nxdl_as_comment(
                yaml_file=yaml_out_file,
                file_to_be_appended=input_file,
                top_lines_list=top_lines,
            )

        # Taking care of consistency running
        if check_consistency:
            xml_out_file = f"{raw_name}_consistency.{ext}"
            generate_nxdl_or_retrieve_nxdl(yaml_out_file, xml_out_file, verbose)
            Path.unlink(yaml_out_file)
    else:
        raise ValueError("Provide correct file with extension '.yaml or '.nxdl.xml")


if __name__ == "__main__":
    launch_tool().parse()  # pylint: disable=no-value-for-parameter
