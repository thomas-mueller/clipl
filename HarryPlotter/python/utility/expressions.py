
# -*- coding: utf-8 -*-

import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)


"""
	This module contains a dictionary for expressions.
"""
class ExpressionsDict(object):
	def __init__(self, additional_expressions=None):
		self.expressions_dict = {}
		
		# example:
		# self.expressions_dict['deltaphijet1jet2'] = '(abs(abs(abs(jet1phi-jet2phi)-TMath::Pi())-TMath::Pi()))'
		
		if not additional_expressions is None:
			self.expressions_dict.update(additional_expressions)

	def get_expression(self, expression):
		return self.expressions_dict.get(expressions.lower(), expression)

	def replace_expressions(self, expression):
		"""Replace any occurence of a dictionary key in the given string."""
		for key, value in self.expressions_dict.iteritems():
			expression = expression.replace(key, value)
		return expression
