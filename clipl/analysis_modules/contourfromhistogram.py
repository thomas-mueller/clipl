# -*- coding: utf-8 -*-

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)

import ROOT

import array
import hashlib
import sys

import clipl.analysis_modules.histogrammanipulationbase as histogrammanipulationbase
import clipl.utility.roottools as roottools


class ContourFromHistogram(histogrammanipulationbase.HistogramManipulationBase):
	""" Retrieve contour graphs from 2D histograms."""

	def modify_argument_parser(self, parser, args):
		super(ContourFromHistogram, self).modify_argument_parser(parser, args)

		self.contour_options = parser.add_argument_group("Contour options")
		self.contour_options.add_argument(
				"--2d-histogram-nicks", type=str, nargs="+",
				help="Nick names of the 2D input histograms."
		)
		self.contour_options.add_argument(
				"--contour-thresholds", type=str, nargs="+",
				help="Thresholds for the contours. Multiple contours for one histogram can be specified in one argument separated by a whitespace."
		)
		self.contour_options.add_argument(
				"--contour-modes", type=str, nargs="+", default=["histogram"],
				choices=["mergegraphs", "singlegraphs", "histogram"],
				help="Modes. \"mergegraphs\" merges all TGraphs for one contour into a single graph, \"singlegraphs\" preserves the single graphs with individual nicks and \"histogram\" only sets the contours of the histogram. [Default: %(default)s]"
		)
		self.contour_options.add_argument(
				"--contour-graph-nicks", type=str, nargs="+", default=[None],
				help="Nick names for the resulting graphs. If more than one threshold is specified, \"_<index>\" is appended to the nick name. The nick is not created in the \"histogram\" mode."
		)
		self.contour_options.add_argument(
				"--contour-minima-nicks", type=str, nargs="+", default=[None],
				help="Nick names for a graph showing the minimum of the contour. [Default: %(default)s]"
		)

	def prepare_args(self, parser, plotData):
		super(ContourFromHistogram, self).prepare_args(parser, plotData)
		self.prepare_list_args(plotData, ["2d_histogram_nicks", "contour_thresholds", "contour_modes", "contour_graph_nicks", "contour_minima_nicks"])
		
		for index, (histogram_nick, contour_thresholds, contour_graph_nicks) in enumerate(zip(*[plotData.plotdict[k] for k in ["2d_histogram_nicks", "contour_thresholds", "contour_graph_nicks"]])):
			contour_thresholds = [float(threshold) for threshold in contour_thresholds.split()]
			plotData.plotdict["contour_thresholds"][index] = contour_thresholds
		
			if contour_graph_nicks is None:
				contour_graph_nicks = "contour_"+histogram_nick
			contour_graph_nicks = contour_graph_nicks.split()
			exapand_all = (len(contour_graph_nicks) == 1 and len(contour_thresholds) > 1)
			contour_graph_nicks = (contour_graph_nicks+([contour_graph_nicks[0]]*len(contour_thresholds)))[:len(contour_thresholds)]
			contour_graph_nicks = ["%s_%d" % (n, i) if exapand_all or (i > 0 and n == contour_graph_nicks[0]) else n for i, n in enumerate(contour_graph_nicks)]
			plotData.plotdict["contour_graph_nicks"][index] = contour_graph_nicks
		
		self.whitelist = plotData.plotdict["2d_histogram_nicks"]

	def run(self, plotData=None):
		super(ContourFromHistogram, self).run(plotData)

		for index, (histogram_nick, contour_thresholds, contour_mode, contour_graph_nicks, contour_minima_nick) in enumerate(zip(*[plotData.plotdict[k] for k in ["2d_histogram_nicks", "contour_thresholds", "contour_modes", "contour_graph_nicks", "contour_minima_nicks"]])):
			
			histogram = plotData.plotdict["root_objects"][histogram_nick]
			self._manipulate_boundary_bins(histogram)
			
			contours = array.array("d", contour_thresholds)
			histogram.SetContour(len(contours), contours)
			
			if contour_minima_nick is not None:
				xBinMin, yBinMin, zBinMin = ROOT.Long(), ROOT.Long(), ROOT.Long()
				histogram.GetBinXYZ(histogram.GetMinimumBin(), xBinMin, yBinMin, zBinMin)
				xMin = histogram.GetXaxis().GetBinCenter(xBinMin)
				yMin = histogram.GetYaxis().GetBinCenter(yBinMin)
				
				minPoint = ROOT.TGraph(1)
				minPoint.SetPoint(0, xMin, yMin)
				plotData.plotdict["root_objects"][contour_minima_nick] = minPoint
			
			if contour_mode.lower() == "histogram":
				log.debug("Set contours %s for histogram \"%s\"." % (str(contour_thresholds), histogram_nick))
			else:
				# remove the stat. box drawn in this function
				ROOT.gStyle.SetOptStat(0)
				
				# without this canvas, no contours can be retrieved
				# https://root.cern.ch/root/html/tutorials/hist/ContourList.C.html#71
				tmp_canvas = ROOT.TCanvas("tmp_canvas", "");
				histogram.Draw("CONT LIST")
				tmp_canvas.Update()
				contours_list = ROOT.gROOT.GetListOfSpecials().FindObject("contours")
			
				for index, (contour_threshold, contour_graph_nick) in enumerate(zip(contour_thresholds, contour_graph_nicks)):
					contours_list_for_threshold = contours_list.At(index)
				
					n_graphs = contours_list_for_threshold.GetSize()
					if n_graphs == 0:
						continue
				
					if (contour_mode.lower() == "singlegraphs") or (n_graphs == 1):
						for graph_index in xrange(n_graphs):
							tmp_contour_graph_nick = contour_graph_nick
							if n_graphs > 1:
								tmp_contour_graph_nick = "%s_%d" % (contour_graph_nick, graph_index)
							if not tmp_contour_graph_nick in plotData.plotdict["nicks"]:
								plotData.plotdict["nicks"].insert(plotData.plotdict["nicks"].index(histogram_nick), tmp_contour_graph_nick)
					
							graph = contours_list_for_threshold.At(graph_index).Clone("contour_"+hashlib.md5(histogram.GetName()+str(graph_index)).hexdigest())
							graph.SetTitle("")
							plotData.plotdict["root_objects"][tmp_contour_graph_nick] = graph
							log.debug("Retrived contour \"%s\" for threshold %f from histogram \"%s\"." % (tmp_contour_graph_nick, contour_threshold, histogram_nick))
					else:
						"""
						multi_graph = ROOT.TMultiGraph("contour_"+histogram.GetName(), "")
						for graph_index in xrange(n_graphs):
							graph = contours_list_for_threshold.At(graph_index)
							graph.SetTitle("")
							multi_graph.Add(graph)
						plotData.plotdict["root_objects"][contour_graph_nick] = multi_graph
						plotData.plotdict["nicks"].insert(plotData.plotdict["nicks"].index(histogram_nick), contour_graph_nick)
						"""
						graph = roottools.RootTools.merge_graphs(
								[contours_list_for_threshold.At(index) for index in xrange(n_graphs)],
								allow_reversed=True, allow_shuffle=True
						)
						graph.SetTitle("")
						graph.SetName("contour_"+hashlib.md5(histogram.GetName()).hexdigest())
						plotData.plotdict["root_objects"][contour_graph_nick] = graph
						plotData.plotdict["nicks"].insert(plotData.plotdict["nicks"].index(histogram_nick), contour_graph_nick)
						log.debug("Retrived contour \"%s\" for threshold %f from histogram \"%s\"." % (contour_graph_nick, contour_threshold, histogram_nick))


	def _manipulate_bin(self, histogram, global_bin):
		if (histogram.GetBinContent(global_bin) == 0.0) and (histogram.GetBinError(global_bin) == 0.0):
			histogram.SetBinContent(global_bin, histogram.GetMaximum())
			"""
			x_bin = ROOT.Long()
			y_bin = ROOT.Long()
			z_bin = ROOT.Long()
			histogram.GetBinXYZ(global_bin, x_bin, y_bin, z_bin)
			
			neighbor_global_bins = []
			neighbor_global_bins.extend([histogram.GetBin(x_bin+shift, y_bin, z_bin) for shift in [-1, 1]])
			neighbor_global_bins.extend([histogram.GetBin(x_bin, y_bin+shift, z_bin) for shift in [-1, 1]])
			neighbor_global_bins.extend([histogram.GetBin(x_bin, y_bin, z_bin+shift) for shift in [-1, 1]])
			neighbor_global_bins = list(set(neighbor_global_bins))
			
			neighbor_bin_contents = [histogram.GetBinContent(global_bin) for global_bin in neighbor_global_bins]
			neighbor_bin_errors = [histogram.GetBinError(global_bin) for global_bin in neighbor_global_bins]
			
			neighbor_bin_contents = [content for content, error in zip(neighbor_bin_contents, neighbor_bin_errors) if (content != 0.0) and (error != 0)]
			if len(neighbor_bin_contents) > 0:
				average_neighbor_bin_content = sum(neighbor_bin_contents) / len(neighbor_bin_contents)
				histogram.SetBinContent(global_bin, average_neighbor_bin_content)
			"""

	def _manipulate_boundary_bins(self, histogram):
		for x_bin in xrange(0, histogram.GetNbinsX()+2):
			next_x_bin = x_bin + (1 if x_bin == 0 else (-1 if x_bin > histogram.GetNbinsX() else 0))
			for y_bin in xrange(0, histogram.GetNbinsY()+2):
				next_y_bin = y_bin + (1 if y_bin == 0 else (-1 if y_bin > histogram.GetNbinsY() else 0))
				for z_bin in xrange(0, histogram.GetNbinsZ()+2):
					next_z_bin = z_bin + (1 if z_bin == 0 else (-1 if z_bin > histogram.GetNbinsZ() else 0))
					
					global_bin = histogram.GetBin(x_bin, y_bin, z_bin)
					next_global_bin = histogram.GetBin(next_x_bin, next_y_bin, next_z_bin)
					if global_bin != next_global_bin:
						histogram.SetBinContent(global_bin, histogram.GetBinContent(next_global_bin))
						histogram.SetBinError(global_bin, histogram.GetBinError(next_global_bin))

