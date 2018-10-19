#!/usr/bin/env python

import logging
import jinja2
import os
import re
import codecs
from utils import confirm_action, logger


template_path="./_templates"
template_js_file="action.js"
template_xml_file="action.xml"


class Action():
    def __init__(self, id, name, script, category, 
                js_result=None, xml_result=None, 
                description='', params=[]):
        self.id = id
        self.name = name
        self.description = description.strip()
        self.params = params
        self.script = script
        self.category = category
        if not (js_result or xml_result):
            logger.error("Missing at least one of result or xml_result to create an action.")
        if js_result:
            self.js_result = js_result
            if "[]" in js_result:
                self.xml_result = "Array/" + js_result.replace("[]", "")
            else:
                self.xml_result = js_result
        else:
            self.xml_result = xml_result
            if 'Array/' in xml_result:
                self.js_result = xml_result.split('/')[1] + '[]'
            else:
                self.js_result = xml_result


    def js_render(self, file):
        desc_as_comment = self.description.replace('\n', '\n * ')
        script = self.script.replace('\n', '\n    ')
        templateLoader = jinja2.FileSystemLoader(searchpath=template_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(template_js_file)
        outputText = template.render(action=self, 
                                    script=script,
                                    description=desc_as_comment)
        with open(file, 'a') as outfile:
            outfile.write(outputText)


    def xml_render(self, folder):
        script_re = re.compile("(^|\\n)([ ]{4})")
        script = script_re.sub(r"\1", self.script)
        file = os.path.join(folder, 'elements', self.id, 'data')
        templateLoader = jinja2.FileSystemLoader(searchpath=template_path)
        templateEnv = jinja2.Environment(loader=templateLoader)
        template = templateEnv.get_template(template_xml_file)
        outputText = template.render(action=self, script=script)
        with open(file, 'w', encoding="utf-16-be") as outfile:
            outfile.write('\ufeff')
            outfile.write(outputText)  # .encode('utf-16-be')

