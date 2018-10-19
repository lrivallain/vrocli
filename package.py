#!/usr/bin/env python

import logging
import os
from lxml import etree
import zipfile
import re
from utils import logger
from action import Action


class Package():
    def __init__(self, name, config):
        self.name = name
        package_conf = self.is_configured(config)
        self.src_package = package_conf.get('package',
            config['default_paths']['packages'] + name + '.package')
        self.expand_target = package_conf.get('expand_target',
            config['default_paths']['expand_target'] + name)
        self.wd = package_conf.get('working_dir',
            config['default_paths']['working_dir'] + name)
        self.build = package_conf.get('build_target',
            config['default_paths']['build_target'] + name + '.package')


    def is_configured(self , config):
        try:
            return config['packages'][self.name]
        except KeyError:
            logger.error("Package %s is not configured. Ensure to add it to your local configuration before to use it." 
                % self.name)
            exit(-1)


    def expand(self):
        """ Expand actions from source path to target one
        """
        categories = []
        if not os.path.exists(self.wd):
            os.makedirs(self.wd)

        elements_path = os.path.join(self.expand_target, 'elements')
        for root, dirs, files in os.walk(elements_path):  # pylint: disable=unused-variable
            for elem in dirs:
                logger.info('Unboxing item with id %s' % elem)
                act_id = elem
                act_data = os.path.join(elements_path, elem, 'data')
                try:
                    act_tree = etree.parse(act_data)
                except etree.XMLSyntaxError:
                    act_tree = None
                try:
                    act_name = act_tree.xpath("/dunes-script-module")[0].get('name')
                except IndexError:
                    act_name = None
                except AttributeError:
                    act_name = None
                if act_tree and act_name:
                    act_return = act_tree.xpath("/dunes-script-module")[0].get('result-type')
                    try:
                        act_desc = act_tree.xpath(
                            "/dunes-script-module/description")[0].text
                    except IndexError:
                        act_desc = ""
                    act_script = act_tree.xpath("/ dunes-script-module/script")[0].text
                    act_params = []
                    for par in act_tree.xpath("/ dunes-script-module/param"):
                        act_params.append({
                            'name': par.get('n'),
                            'type': par.get('t'),
                            'desc': par.text
                        })

                    act_cat_tree = etree.parse(os.path.join(
                        elements_path, elem, 'categories'))
                    act_cat = act_cat_tree.xpath("/categories/category/name")[0].text
                    action = Action(
                        id=act_id,
                        name=act_name,
                        description=act_desc,
                        params=act_params,
                        script=act_script,
                        category=act_cat,
                        xml_result=act_return
                    )
                    mod_file = os.path.join(self.wd, act_cat + '.js')
                    if not act_cat in categories:
                        logger.debug("New module found: %s" % act_cat)
                        # new module file
                        categories.append(act_cat)
                        with open(mod_file, 'w') as outfile:
                            outfile.write("/** @module " + act_cat + " */\n\n")
                    logger.debug('Rendering action to module file')
                    action.js_render(mod_file)
                else:
                    logger.info("Item with ID %s was ignored as it is not a vRO action" 
                        % act_id)
        logger.info("Actions expanded in: %s" % self.wd)


    def unzip(self):
        """ Unzip a package file to the expand target
        """
        if not os.path.isfile(self.src_package):
            print("Package not found %s" % self.src_package)
            exit(-1)
        if not os.path.exists(self.expand_target):
            os.makedirs(self.expand_target)
        logger.info("Extracting package content")
        zip_ref = zipfile.ZipFile(self.src_package, 'r')
        zip_ref.extractall(self.expand_target)
        zip_ref.close()


    def rebuild(self):
        """ Rebuild a .package file from local expanded files
        """
        logger.info("Building new package at %s" % self.build)
        with zipfile.ZipFile(self.build, "w", zipfile.ZIP_DEFLATED) as zipf:
            len_dir_path = len(self.expand_target)
            for root, _, files in os.walk(self.expand_target):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path[len_dir_path:])
