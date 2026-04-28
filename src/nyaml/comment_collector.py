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
Collect comments in a list by CommentCollector class and each comment is an instance of Comment
class. Each `Comment` instance(sometimes referred to as 'comment block') consists of text and line
info or neighboring info where the comment must be placed.

The class Comment is an abstract class for general functions or method to be implemented
XMLComment and YAMLComment class.
"""

import os
from collections.abc import Iterator
from typing import Any

from nyaml.helper import LineLoader

__all__ = ["Comment", "CommentCollector", "XMLComment", "YAMLComment"]


# pylint: disable=inconsistent-return-statements
class CommentCollector:
    """CommentCollector will store a full comment ('Comment') object in
    _comment_chain.
    """

    def __init__(
        self,
        input_file: str | os.PathLike[str] = None,
        loaded_obj: object | dict = None,
    ):
        """
        Initialise CommentCollector
        parameters:
            input_file: raw input file (xml, yml)
            loaded_obj: file loaded by third party library
        """
        self._comment_chain: list[YAMLComment | XMLComment] = []
        self.file: str = os.fspath(input_file)
        self._comment_tracker = 0
        self._comment_hash: dict[tuple, Comment] = {}
        self.comment: type[XMLComment] | type[YAMLComment] = None
        if self.file and not loaded_obj:
            if self.file.endswith(".xml"):
                self.comment = XMLComment
            elif self.file.split(".")[-1] == "yaml":
                self.comment = YAMLComment
                with open(self.file, encoding="utf-8") as plain_text_yaml:
                    loader = LineLoader(plain_text_yaml)
                    self.comment.__yaml_dict__ = loader.get_single_data()
            else:
                raise ValueError("Input file must be a 'yaml' or 'nxdl.xml' type.")
        elif self.file and loaded_obj:
            if self.file.split(".")[-1] == "yaml" and isinstance(loaded_obj, dict):
                self.comment = YAMLComment
                self.comment.__yaml_dict__ = loaded_obj
            else:
                raise ValueError(
                    "Incorrect inputs for CommentCollector e.g. Wrong file extension."
                )

        else:
            raise ValueError("Incorrect inputs for CommentCollector")

    def extract_all_comment_blocks(self) -> None:
        """Collect all comments.

        Note here that comment means (comment text + element or line info
        intended for comment.
        """
        id_ = 0
        single_comment = self.comment(comment_id=id_)
        with open(self.file, encoding="UTF-8") as enc_f:
            lines = enc_f.readlines()
            # Make an empty line for last comment if no empty lines in original file
            if lines[-1] != "":
                lines.append("")
            end_line_num = len(lines) - 1
            for line_num, line in enumerate(lines):
                if single_comment.is_storing_single_comment():
                    # If the last comment comes without post nxdl fields, groups and attributes
                    if "++ SHA HASH ++" in line:
                        # Handle with stored nxdl.xml file that is not part of yaml
                        single_comment.process_each_line("post_comment", (line_num + 1))
                        self._comment_chain.append(single_comment)
                        break
                    if line_num < end_line_num:
                        # Processing file from Line number 1
                        single_comment.process_each_line(line, (line_num + 1))
                    else:
                        # For processing last line of file
                        single_comment.process_each_line(
                            line + "post_comment", (line_num + 1)
                        )
                        self._comment_chain.append(single_comment)
                else:
                    self._comment_chain.append(single_comment)
                    single_comment = self.comment(last_comment=single_comment)
                    single_comment.process_each_line(line, (line_num + 1))

    def get_next_comment(self) -> "YAMLComment | XMLComment":
        """
        Return comment from comment_chain that must come earlier in order.
        """
        return self._comment_chain[self._comment_tracker]

    def get_comment_by_line_info(
        self, comment_locs: tuple[str, int | str]
    ) -> "Comment | None":
        """
        Get comment using line information.
        """
        if comment_locs in self._comment_hash:
            return self._comment_hash[comment_locs]

        line_annotation, line_loc = comment_locs
        for comment in self._comment_chain:
            if isinstance(comment, YAMLComment) and line_annotation in comment:
                line_loc_ = comment.get_line_number(line_annotation)
                if line_loc == line_loc_:
                    self._comment_hash[comment_locs] = comment
                    return comment
        return None

    def remove_comment(self, ind: int) -> None:
        """Remove a comment from comment list."""
        if ind < len(self._comment_chain):
            del self._comment_chain[ind]
        else:
            raise ValueError("Oops! Index is out of range.")

    def reload_comment(self) -> None:
        """
        Update self._comment_tracker after done with last comment.
        """
        self._comment_tracker += 1

    def __contains__(self, comment_locs: tuple) -> bool:
        """
        Confirm wether the comment corresponds to key_line and line_loc
            is exist or not.
            comment_locs is equivalent to (line_annotation, line_loc) e.g.
            (__line__doc and 35)
        """
        if not isinstance(comment_locs, tuple):
            raise TypeError(
                "Comment_locs should be 'tuple' containing line annotation "
                "(e.g.__line__doc) and line_loc (e.g. 35)."
            )
        line_annotation, line_loc = comment_locs
        for comment in self._comment_chain:
            if isinstance(comment, YAMLComment) and line_annotation in comment:
                line_loc_ = comment.get_line_number(line_annotation)
                if line_loc == line_loc_:
                    self._comment_hash[comment_locs] = comment
                    return True
        return False

    def __getitem__(
        self, ind: int | slice
    ) -> "YAMLComment | XMLComment | list[YAMLComment | XMLComment]":
        """Get comment from  self.obj._comment_chain by index."""
        if isinstance(ind, int):
            if ind >= len(self._comment_chain):
                raise IndexError(
                    f"Oops! Comment index {ind} in {self.__class__} is out of range!"
                )
            return self._comment_chain[ind]

        if isinstance(ind, slice):
            start_n = ind.start or 0
            end_n = ind.stop or len(self._comment_chain)
            return self._comment_chain[start_n:end_n]

    def __iter__(self) -> Iterator["YAMLComment | XMLComment"]:
        """get comment iteratively"""
        return iter(self._comment_chain)


# pylint: disable=too-many-instance-attributes
class Comment:
    """
    This class is building yaml comment and the intended line for what comment is written.
    """

    def __init__(self, comment_id: int = -1, last_comment: "Comment" = None) -> None:
        """Comment object can be considered as a block element that includes
        document element (an entity for what the comment is written).
        """
        self._element: dict[str, Any] = {}
        self._element_text: str = None
        self._is_element_found: bool = None
        self._is_element_stored: bool = None

        self._comment: str = ""
        # If Multiple comments for one element or entity
        self._comment_list: list[str] = []
        self.last_comment: Comment = last_comment if last_comment else None
        if comment_id >= 0 and last_comment:
            self.cid = comment_id
            self.last_comment = last_comment
        elif comment_id == 0 and not last_comment:
            self.cid = comment_id
            self.last_comment = None
        elif last_comment:
            self.cid = self.last_comment.cid + 1
            self.last_comment = last_comment
        else:
            raise ValueError("Neither last comment nor comment id found")
        self._comment_start_found: bool = False
        self._comment_end_found: bool = False
        self.is_storing_single_comment = lambda: (
            not (self._comment_end_found and self._is_element_stored)
        )

    def get_comment_text_list(self) -> list | str:
        """
        Extract comment text from entire comment (comment text + element or
        line for what comment is intended)
        """

    def append_comment(self, text: str) -> None:
        """
        Append lines of the same comment.
        """

    def store_element(self, *args: Any) -> None:
        """
        Store comment text and line or element that is intended for comment.
        """

    def __contains__(self, line_key: str) -> bool:
        """For checking whether __line__<NAME> is in _element dict or not."""
        return line_key in self._element


class XMLComment(Comment):
    """
    XMLComment to store xml comment element.
    """

    def __init__(self, comment_id: int = -1, last_comment: "Comment" = None) -> None:
        super().__init__(comment_id, last_comment)

    def process_each_line(self, text: str, line_num: int) -> None:
        """Take care of each line of text. Through which function the text
        must be passed should be decide here.
        """
        text = text.strip()
        if text and line_num:
            self.append_comment(text)
            if self._comment_end_found and not self._is_element_found:
                # for multiple comment if exist
                if self._comment:
                    self._comment_list.append(self._comment)
                    self._comment = ""

            if self._comment_end_found:
                self.store_element(text)

    def append_comment(self, text: str) -> None:
        # Comment in single line
        if "<!--" == text[0:4]:
            self._comment_start_found = True
            self._comment_end_found = False
            self._comment = self._comment + text.replace("<!--", "")
            if "-->" == text[-4:]:
                self._comment_end_found = True
                self._comment_start_found = False
                self._comment = self._comment.replace("-->", "")

        elif "-->" == text[0:4] and self._comment_start_found:
            self._comment_end_found = True
            self._comment_start_found = False
            self._comment = self._comment + "\n" + text.replace("-->", "")
        elif self._comment_start_found:
            self._comment = self._comment + "\n" + text

    # pylint: disable=arguments-differ, arguments-renamed
    def store_element(self, text: str) -> None:
        def collect_xml_attributes(text_part: list[str]) -> None:
            for part in text_part:
                part = part.strip()
                if part and part.endswith('">'):
                    self._is_element_stored = True
                    self._is_element_found = False
                    part = part[0:-2]
                elif part and part.endswith('"/>'):
                    self._is_element_stored = True
                    self._is_element_found = False
                    part = part[0:-3]
                elif part and part.endswith("/>"):
                    self._is_element_stored = True
                    self._is_element_found = False
                    part = part[0:-2]
                elif part and part.endswith(">"):
                    self._is_element_stored = True
                    self._is_element_found = False
                    part = part[0:-1]
                elif part and part.endswith('"'):
                    part = part[0:-1]

                if '="' in part:
                    lf_prt, rt_prt = part.split('="')
                    if ":" in lf_prt:
                        continue
                else:
                    continue
                self._element[lf_prt] = str(rt_prt)

        if not self._element:
            self._element = {}
        # First check for comment part has been collected perfectly
        if text.startswith("</"):
            pass
        elif text.startswith("<") and not text.startswith("<!--"):
            self._is_element_found = True
            text = text.replace("<", "", 1)
            text_part = text.split(" ")
            # collect tag
            self._element["tag"] = text_part[0]
            self._element["attrib"] = {}
            collect_xml_attributes(text_part[1:])

        elif self._is_element_found:
            text_part = text.split(" ")
            collect_xml_attributes(text_part)

    def get_element_info(self) -> dict[str, Any]:
        """
            The method returns info dict that includes:
        'tag' and 'attrib' keys.
        """
        return self._element

    def get_comment_text_list(self) -> list | str:
        """
        This method returns list of comment text. As some xml element might have
        multiple separated comment intended for a single element.
        """
        return self._comment_list


class YAMLComment(Comment):
    """
    This class for storing comment text as well as location of the comment e.g. line
    number of other in the file.
    NOTE:
     1. Do not delete any element from yaml dictionary (for loaded_obj. check: Comment_collector
     class. because this loaded file has been exploited in nyaml2nxdl forward tools.)
    """

    # Make this class unhashable (needed since we are overwriting __eq__)
    __hash__ = None

    # Class level variable. The main reason behind that to follow structure of
    # abstract class 'Comment'
    __yaml_dict__: dict = {}
    __yaml_line_info: dict = {}
    __comment_escape_char = {"--": "-\\-"}

    def __init__(self, comment_id: int = -1, last_comment: "Comment" = None) -> None:
        """Initialization of YAMLComment follow Comment class."""
        super().__init__(comment_id, last_comment)
        self.collect_yaml_line_info(
            YAMLComment.__yaml_dict__, YAMLComment.__yaml_line_info
        )

    def process_each_line(self, text: str, line_num: int) -> None:
        """Process each line.

        Take care of each line of text. Through which function the text
        must be passed should be decide here.
        """
        text = text.strip()
        self.append_comment(text)
        if self._comment_end_found and not self._is_element_found:
            if self._comment:
                self._comment_list.append(self._comment)
                self._comment = ""

        if self._comment_end_found:
            line_key = ""
            ind = text.find(":")
            if ind > 0:
                line_key = "__line__" + text[0:ind]

            for l_num, l_key in self.__yaml_line_info.items():
                if line_num == int(l_num) and line_key == l_key:
                    self.store_element(line_key, line_num)
                    break
                # Comment comes very end of the file
                if text == "post_comment" and line_key == "":
                    line_key = "__line__post_comment"
                    self.store_element(line_key, line_num)

    def has_post_comment(self) -> bool:
        """Ensure if this is a post comment or not.

        Post comment means the comment that comes at the very end without having any
        nxdl element(class, group, filed and attribute.).
        """
        for key, _ in self._element.items():
            if "__line__post_comment" == key:
                return True
        return False

    def append_comment(self, text: str) -> None:
        """Append comment texts to the associated comment.

            Collects all the line of the same comment and
        append them with that single comment.
        """
        # check for escape char
        text = self.replace_escape_char(text)
        # Empty line after last line of comment
        if not text and self._comment_start_found:
            self._comment_end_found = True
            self._comment_start_found = False
        # For empty line inside doc or yaml file.
        elif not text:
            return
        elif text.startswith("# "):
            self._comment_start_found = True
            self._comment_end_found = False
            self._comment = "" if not self._comment else self._comment + "\n"
            self._comment = self._comment + text[2:]
        elif text.startswith("#"):
            self._comment_start_found = True
            self._comment_end_found = False
            self._comment = "" if not self._comment else self._comment + "\n"
            self._comment = self._comment + text[1:]
        elif "post_comment" == text:
            self._comment_end_found = True
            self._comment_start_found = False
        # for any line after 'comment block' found
        elif self._comment_start_found:
            self._comment_start_found = False
            self._comment_end_found = True

    # pylint: disable=arguments-differ
    def store_element(self, line_key: str, line_number: int) -> None:
        """Store comment contents and information of comment location."""
        self._element = {}
        self._element[line_key] = int(line_number)
        self._is_element_found = False
        self._is_element_stored = True

    def get_comment_text_list(self) -> list[str]:
        """
        Return list of comments.
        """
        return self._comment_list

    def get_line_number(self, line_key: str) -> int:
        """
        Return line no for which line the comment is created.
        """
        return self._element[line_key]

    def get_line_info(self) -> tuple[str, int]:
        """
        Return line annotation and line number from a comment.
        """
        for line_anno, line_loc in self._element.items():
            return line_anno, line_loc
        raise ValueError("Comment element is empty; no line info available.")

    def replace_escape_char(self, text: str) -> str:
        """Replace escape char according to __comment_escape_char dict"""
        for ecp_char, ecp_alt in YAMLComment.__comment_escape_char.items():
            text = text.replace(ecp_char, ecp_alt)
        return text

    def get_element_location(self) -> tuple[str, int]:
        """Return yaml line '__line__<KEY>' info and and line number"""
        if len(self._element) == 0:
            raise ValueError(
                f"Comment element should be one or more but got {self._element}"
            )
        return next(iter(self._element.items()))

    def collect_yaml_line_info(
        self, yaml_dict: dict, line_info_dict: dict[int, str]
    ) -> None:
        """Collect __line__key and corresponding value from
        a yaml file dictionary in another dictionary.
        """
        for line_key, line_n in yaml_dict.items():
            if "__line__" in str(line_key):
                line_info_dict[line_n] = str(line_key)

        for _, val in yaml_dict.items():
            if isinstance(val, dict):
                self.collect_yaml_line_info(val, line_info_dict)

    def __contains__(self, line_key: str) -> bool:
        """For checking whether __line__<NAME> is in _element dict or not."""
        return line_key in self._element

    def __eq__(self, comment_obj: "Comment") -> bool:  # type: ignore[override]
        """Check the self has same value as right comment."""
        if not isinstance(comment_obj, Comment):
            raise TypeError(f"Expecting comment_obj as a instance of {Comment}")
        if len(self._comment_list) != len(comment_obj._comment_list):
            return False
        for left_comment, right_comment in zip(
            self._comment_list, comment_obj._comment_list
        ):
            left_comment_nested = left_comment.split("\n")
            right_comment_nested = right_comment.split("\n")
            for left_line, right_line in zip(left_comment_nested, right_comment_nested):
                if left_line.strip() != right_line.strip():
                    return False
        return True
