#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)

import sys

import clipl.harry as harry


if __name__ == "__main__":
	"""This script executes all steps necessary to create a plot."""
	if len(sys.argv) == 1:
		sys.argv.append("-h")
		
	harry.HarryPlotter()

