# -*- coding: utf-8 -*-

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)

import clipl.analysisbase as analysisbase


class GetCorrelationFactor(analysisbase.AnalysisBase):
	"""For TH2: print correlation factor and add to plotData.plotdict['texts']"""

	def run(self, plotData=None):
		super(GetCorrelationFactor, self).run(plotData)

		for nick, histo in plotData.plotdict['root_objects'].iteritems():
			try:
				log.info("Correlation for nick '{}': {:.3f}".format(nick, histo.GetCorrelationFactor()))
				if plotData.plotdict['texts'] == [None]:
					plotData.plotdict['texts'] = []
				plotData.plotdict['texts'].append('Correlation factor: {:.3f}'.format(histo.GetCorrelationFactor()))
			except AttributeError:
				log.warning("No 'GetCorrelationFactor()' for histogram with nick '{}'".format(nick))
