#!/usr/bin/python
#! -*- encoding=utf-8 -*-
"""
----------------------------------------------------------------------
Copyright 2019 Tigerwing XU (tigerwingxys@qq.com)

Licensed under the Apache License, Version 2.0 (the "License")
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-------------------------------------------------------------------------
"""

from collections import defaultdict
import logging
import re

logger = logging.getLogger("xXMLParser")


# the element's status of parsing process
INITIAL = 0
PARSING = 1
CLOSED = 2

class XXMLElement(object) :
    def __init__(self):
        self._attrs = defaultdict(None)
        self._childrens = []
        self.father = None
        self.parsing_state = INITIAL
        self.name = ''
        self.text = ''

    def get_element(self, name):
        if not name or name == '':
            return None
        for ele in self._childrens:
            if name == ele.name:
                return ele
        return None

    def get_childs(self):
        return self._childrens

    def add_a_child(self, ee=None):
        ee = ee or XXMLElement()
        ee.father = self
        self._childrens.append(ee)
        return ee

    def get_attrs(self):
        return self._attrs

    def set_attribute(self, name, value):
        self._attrs[name] = value

    def get_attribute(self, name):
        if not name or name == '':
            return ''
        return self._attrs[name]

    def clear(self):
        self._attrs.clear()
        self._childrens.clear()

    def to_str(self, tree_level):
        astr = '    '*tree_level
        astr += '['+self.name+']'
        if not self.text == '':
            astr += ', Text['+self.text+']'
        if len(self._attrs) > 0:
            astr += ', Attributes['+','.join(list(map(lambda x: '='.join([x, str(self._attrs[x])]), self._attrs.keys()))) + ']'
        astr += '\n'
        if len(self._childrens) > 0:
            for item in self._childrens:
                astr += item.to_str(tree_level+1)
        return astr


# match xml tag begin or end or nullTag
catch_tag = r"(?<=<)\w+\b"
catch_text = r"(?<=>).*(?=<)"
catch_tag_end = r'(?<=</)\w+(?=[\s]*>)'
catch_tag_null = r"/>"
# match key="value" attributes
catch_attributes = r'\b\w+=[\'"].*?[\'"]|\w+=.+\b'
# match all Tags, <a> something </a> or <a/> or <a xx="ss"> or </a>...
# catch_all_elements = r'((<\w+[^\n/<]*[/]?>).*(</\w+[\s]*>))|(<\w+[^\n/<]*[\/]?>)|(</\w+[\s]*>)'
catch_comment_begin = r'<!--'
catch_comment_end = r'-->'

p_tag = re.compile(catch_tag)
p_attribute = re.compile(catch_attributes)
p_text = re.compile(catch_text)
p_tag_end = re.compile(catch_tag_end)
p_tag_null = re.compile(catch_tag_null)
# p_all_elements = re.compile(catch_all_elements)
p_comment_begin = re.compile(catch_comment_begin)
p_comment_end = re.compile(catch_comment_end)


class XXMLParser(object):
    def __init__(self):
        self._document = XXMLElement()
        self._document.name = 'ROOT'

    def parse_xml(self, xxml):
        if not xxml or xxml == '':
            return None
        self._document.clear()

        one_element = self._document
        one_element.parsing_state = PARSING
        # result = p_all_elements.findall(xxml)
        comment_begin = False
        result = xxml
        if type(xxml) == str:
            result = xxml.splitlines()
        for match in result:
            one_line = match.strip()

            # discard comment line
            if not comment_begin:
                if p_comment_begin.search(one_line):
                    comment_begin = True
                    if p_comment_end.search(one_line):
                        comment_begin = False
                    continue
            else:
                if p_comment_end.search(one_line):
                    comment_begin = False
                continue

            one_element = XXMLParser.parse_one_element(self, one_line, one_element)

        self._document.parsing_state = CLOSED
        return self._document

    @staticmethod
    def parse_match_pattern(self, pattern, src_str):
        result = re.compile(pattern).search(src_str)
        if not result:
            return False
        else:
            return True

    @staticmethod
    def parse_one_element(self, one_line: str, one_element: XXMLElement) -> XXMLElement:
        if one_element.parsing_state == INITIAL:
            one_element.parsing_state = PARSING

            m = p_tag.search(one_line)
            if m:
                one_element.name = m.group()

            m = p_text.search(one_line)
            if m:
                one_element.text = m.group()

            r = p_attribute.findall(one_line)
            for attr in r:
                keys = attr.split('=')
                if len(keys) > 1:
                    one_element.set_attribute(keys[0],keys[1])

            if p_tag_null.search(one_line):
                one_element.parsing_state = CLOSED
                return one_element

            m = p_tag_end.search(one_line)
            if m:
                end_name = m.group()
                if end_name == one_element.name:
                    one_element.parsing_state = CLOSED
                    return one_element
                else:
                    # error, current element not closed, but met its parents's END tag.
                    logger.error("INITIAL branch-- tag_name:"+one_element.name+
                                 " still not closed, but met a tagEND:"+end_name)
                    # todo robust processing here ...
            else:
                return one_element
        elif one_element.parsing_state == PARSING:
            m = p_tag.search(one_line)
            # when current element is parsing, the coming new begin tag will create a child element
            if m:
                child_element = one_element.add_a_child()
                child_element.name = m.group()
                one_element = child_element
                one_element.parsing_state = PARSING

            m = p_text.search(one_line)
            if m:
                one_element.text = m.group()

            r = p_attribute.findall(one_line)
            for attr in r:
                keys = attr.split('=')
                if len(keys) > 1:
                    one_element.set_attribute(keys[0],keys[1])

            if p_tag_null.search(one_line):
                one_element.parsing_state = CLOSED
                return one_element

            m = p_tag_end.search(one_line)
            if m:
                end_name = m.group()
                if end_name == one_element.name:
                    one_element.parsing_state = CLOSED
                    return one_element
                else:
                    # error, current element not closed, but met its parents's END tag.
                    logger.error("PARSING branch-- tag_name:" + one_element.name +
                                 " still not closed, but met a tagEND:" + end_name)
                    # todo robust processing here ...
            else:
                return one_element
        else:
            # current element is closed, first check if met parents's end tag
            m = p_tag_end.search(one_line)
            end_name = ''
            if m:
                end_name = m.group()
                if end_name == one_element.father.name:
                    one_element.father.parsing_state = CLOSED
                    return one_element.father

            one_element = one_element.father.add_a_child();
            one_element.parsing_state = PARSING

            m = p_tag.search(one_line)
            if m:
                one_element.name = m.group()

            m = p_text.search(one_line)
            if m:
                one_element.text = m.group()

            r = p_attribute.findall(one_line)
            for attr in r:
                keys = attr.split('=')
                if len(keys) > 1:
                    one_element.set_attribute(keys[0],keys[1])

            if p_tag_null.search(one_line) or end_name == one_element.name:
                one_element.parsing_state = CLOSED
                return one_element

        return one_element


if __name__ == "__main__":

    xparser = XXMLParser()
    xxml = '<autoanswer>no</autoanswer>\r<blacklist>\r<item>555</item>\r<item>556</item>\r' + \
        '<!-- this is a comment line -->\r' + \
        '<!-- this is a comment line for 3 lines:one\r' + \
        'two\rthree-->\r' + \
        '</blacklist>\r<tagnull test=\'auto\' value=123/>'
    doc = xparser.parse_xml(xxml)
    astr = doc.to_str(0)
    print(astr)

    with open('examples.xml') as f:
        doc = xparser.parse_xml(f.readlines())
        astr = doc.to_str(0)
        print(astr)



