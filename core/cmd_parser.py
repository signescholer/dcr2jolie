# coding=utf-8
"""Contains methods for command line interaction"""
import argparse

def parse_args():
    """ #modified
    Creates the argument parser for the command line
    :return: the args that were parsed from the command line
    """

    parser = argparse.ArgumentParser(prog='epp_dcr.py', usage='epp_dcr.py [--xml file]')

    parser.add_argument('--xml', nargs="?", default='input/House_for_sale.xml',
                        help='The input path for the DCR Graph xml')

    return parser.parse_args()