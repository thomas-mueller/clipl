# -*- coding: utf-8 -*-

"""
"""

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)

import sys

import clipl.processor as processor


class AnalysisBase(processor.Processor):
	def __init__(self):
		super(AnalysisBase, self).__init__()
	
	def prepare_args(self, parser, plotData):
		super(AnalysisBase, self).prepare_args(parser, plotData)
	
	def run(self, plotData=None):
		super(AnalysisBase, self).run(plotData)

