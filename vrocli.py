#!/usr/bin/env python

import os
import click
import sys
import hashlib
import io
import logging
import re
from utils import logger, read_config, confirm_action, extract_actions_from_module_file, list_modules
from package import Package
from vroserver import VroServer

def print_version(ctx, param, value):
    """ Print version of vRO CLI
    """
    if not value or ctx.resilient_parsing:
        return
    click.echo('vRO CLI - Version 1.0')
    ctx.exit()


def abort_if_false(ctx, param, value):
    """ Abort the program is user input is false on confirmation prompt
    """
    if not value:
        ctx.abort()


@click.group(options_metavar='<options>')
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('--version', is_flag=True, callback=print_version,
    expose_value=False, is_eager=True)
def vrocli(verbose=False):
    """ vRealize Automation coder/command line interface
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


@vrocli.command('list', options_metavar='',
                short_help='List configured items (servers or packages)')
@click.argument('itemtype', nargs=1, metavar='<string>')
def list(itemtype):
    """ List configured items (servers or packages)
    """
    lookup = None
    if (itemtype == 'server') or (itemtype == 'servers'):
        lookup = 'vro_servers'
    if (itemtype == 'package') or (itemtype == 'packages'):
        lookup = 'packages'
    if not lookup:
        logger.error(""" Invalid itemtype to list from configuration: 
        only 'server'(s)/'package'(s) values are accepted.""")
        exit(-1)
    click.echo("%s configured items are:" % lookup)
    for item in config[lookup]:
        click.echo("  > %s" % str(item))


@vrocli.command('push', options_metavar='<options>',
                short_help='(Optionnaly build and) Push a package to a vRO server')
@click.option('-s', '--server', nargs=1, metavar='<string>',
    help='Name of vRO server (must be in configuration file)')
@click.option('-p', '--package', nargs=1, metavar='<string>',
    help="Package name to use (must be in configuration file)")
@click.option('-b', '--build', is_flag=True, default=False,
    help="Do you want to build the package from local files before pushing?")
@click.option('--yes', is_flag=True, callback=abort_if_false,
    expose_value=False,
    prompt='This action will replace your remote work. Continue?')
def push(package, server, build):
    """ (Optionnaly build and) Push a package to a vRO server
    """
    if build:
        _build_package(package)
    p = Package(package, config)
    v = VroServer(server, config)
    v.push(p.name, p.build)


@vrocli.command('pull', options_metavar='<options>',
    short_help='Get (and optionnaly expand) a package from a vRO server')
@click.option('-s', '--server', nargs=1, metavar='<string>',
    help='Name of vRO server (must be in configuration file)')
@click.option('-p', '--package', nargs=1, metavar='<string>',
    help="Package name to us (must be in configuration file)")
@click.option('-e', '--expand', is_flag=True, default=False,
    help="Do you want to expand the package to local files after downloading?")
@click.option('--yes', is_flag=True, callback=abort_if_false,
    expose_value=False,
    prompt='This action will replace any local current work. Continue?')
def pull(package, server, expand):
    """ Get (and optionnaly expand) a package from a vRO server
    """
    p = Package(package, config)
    v = VroServer(server, config)
    v.pull(p.name, p.src_package)
    if expand:
        _expand_package(package)


@vrocli.command('build', options_metavar='<options>',
    short_help='Build a package file from the local files structure')
@click.option('-p', '--package', nargs=1, metavar='<string>',
    help="Package name to use")
@click.option('--yes', is_flag=True, callback=abort_if_false,
    expose_value=False,
    prompt='This action will built a new package based on local work. Continue?')
def build_package(package):
    """ Build a package file from the local files structure
    """
    _build_package(package)


@vrocli.command('expand', options_metavar='<options>',
    short_help='Expand a package file to a local files structure')
@click.option('-p', '--package', nargs=1, metavar='<string>',
    help="Package name to use")
@click.option('--yes', is_flag=True, callback=abort_if_false,
    expose_value=False,
    prompt='This action will replace any local current work. Continue?')
def expand_package(package):
    """ Expand a package file to a local files structure
    """
    _expand_package(package)


def _build_package(package):
    """ Build a package file from the local files structure
    """
    logger.info("Building package from local content")
    # new package obj
    p = Package(package, config)
    # extract action from js src file to xml one
    for m in list_modules(p.wd):
        extract_actions_from_module_file(
            m[0],
            "".join(m[1][1:]),
            p.expand_target
        )
    p.rebuild()


def _expand_package(package):
    """ Expand a package file to a local files structure
    """
    # new package obj
    p = Package(package, config)
    # unzip
    p.unzip()
    # convert to js files
    p.expand()


if __name__ == '__main__':
    config = read_config()
    vrocli()
