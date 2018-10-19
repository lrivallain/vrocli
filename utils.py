#!/usr/bin/env python

import logging
import yaml
import re
import os
import coloredlogs
import click

# create logger
logger = logging.getLogger()
# colored console output
ch = logging.StreamHandler()
formatter = coloredlogs.ColoredFormatter("%(asctime)s > %(levelname)s\t> %(message)s",
                                        "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
#ch.setLevel(logging.INFO)
logger.addHandler(ch)
# file output
fh = logging.FileHandler(filename="./vrocli.log")
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                            "%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logging.captureWarnings(True)


def read_config():
    """ Read the configuration file and return the config object
    """
    with open('.vrocli.yml', 'r') as conffile:
        try:
            config = yaml.load(conffile)['vrocli']
            logger = logging.getLogger()
            logger.setLevel(config['log_level'])
            return config
        except yaml.YAMLError as e:
            logger.error(e)
            exit(-1)


def confirm_action(message):
    """ Prompt user for a confirmation to proceed action
    """
    if not click.confirm(message + " Continue?"):
        logger.info("User cancels action. Exiting...")
        exit(0)
    else: return


def get_id_from_comments(raw_action):
    """ Extract the id of an action from the raw js action
    """
    act_id_re = re.compile(r"/\*[ ]*id:(?P<id>[\w-]+)")
    act_id_m = act_id_re.search(raw_action)
    if act_id_m:
        return act_id_m.group(1)
    else:
        logger.error("Cannot find id in the following data: %s" % raw_action)
        exit(-1)


def get_description_from_comments(act_comments):
    """ Extract description from the jsdoc comment section
    """
    desc_re = re.compile(r"\*[ ]+(?!@)(.*)")
    return "\n".join(desc_re.findall(act_comments))


def get_params_from_comments(act_comments):
    """ Returns list of params found in a jsdoc comment section
    """
    params_re = re.compile(
        r"[ ]+\*[ ]+@param[ ]+\{(?P<type>.*)}[ ]+(?P<var_name>\w+)[ ]*(?P<desc>.*)")
    act_params = []
    for param_g in params_re.findall(act_comments):
        p_type, p_name, p_desc = param_g
        param = {'type': p_type, 'name': p_name, 'desc': p_desc}
        act_params.append(param)
    return act_params


def get_return_from_comment(act_comments):
    """ Returns the result of action found in a jsdoc comment section
    """
    returns_re = re.compile(r"[ ]+\*[ ]+@return[ ]+\{(.*)\}.*")
    returns_m = returns_re.search(act_comments)
    if returns_m:
        return returns_m.group(1)
    else:
        return None


from action import Action
def extract_actions_from_module_file(module_name, module_content, target):
    """ Returns actions object for a specific src module
    """
    # split module content to actions
    action_re = re.compile(r"/\*[ ]*VRO[ ]+ACTION[ ]+START[ ]*\*/(?P<action>.*?)/\*[ ]*VRO[ ]+ACTION[ ]+END[ ]*\*/",
        re.MULTILINE | re.DOTALL)
    # get comments and code from action
    unraw_action_re = re.compile(r"/\*\*(?P<comments>.*?)\*/.*?function[ ]+(?P<function>[\w-]+)[ ]*\(\).*?\{.*?(?P<code>.*?)^\}",
        re.MULTILINE | re.DOTALL)
    
    actions = []
    for raw_action in action_re.findall(module_content):
        act_id = get_id_from_comments(raw_action)
        unraw_action_m = unraw_action_re.search(raw_action)
        # test match before continuing: else raise error in logs
        if unraw_action_m:
            act_name = unraw_action_m.group('function')
            act_script = unraw_action_m.group('code').strip()
            act_comments = unraw_action_m.group('comments')
            # read description
            act_desc = get_description_from_comments(act_comments)
            # find return data
            act_return = get_return_from_comment(act_comments)
            # find params
            act_params = get_params_from_comments(act_comments)
            action = Action(
                id=act_id,
                name=act_name,
                description=act_desc,
                params=act_params,
                script=act_script,
                category=module_name,
                js_result=act_return
            )
            logger.debug("Found action with name %s and ID %s" % (act_name, act_id))
            actions.append(action)
            action.xml_render(target)
        else:
            logger.error(
                "Invalid syntax in following supposed-to-be vRO action: %s" % raw_action)
    return actions


def list_modules(path):
    """ Returns a list of modules (name,content) found in a path
    """
    modules = []
    for root, dirs, files in os.walk(path): # pylint: disable=unused-variable
        for file in files:
            if file.endswith(".js"):
                with open(os.path.join(path, file), 'r') as modfile:
                    content = modfile.readlines()
                    module_re = r"/\*\* @module +([\w.]+) +\*/"
                    m = re.search(module_re, content[0])
                    # test if its supposed to be a module
                    if m and m.group(1):
                        # great its a module ! lets see its content
                        logger.debug("Module detected %s" % m.group(1))
                        modules.append((m.group(1), content))
    return modules
