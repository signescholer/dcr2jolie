# coding=utf-8
"""
Used to make the execution of the test as a package possible
"""
import os
import sys

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../core'))
sys.path.insert(0, path)
