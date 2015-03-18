# -*- coding: utf-8 -*-

"""
"""

import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)

import os
import ROOT
import sys

import Artus.HarryPlotter.plotbase as plotbase
import Artus.HarryPlotter.plotdata as plotdata
import Artus.HarryPlotter.utility.extrafunctions as extrafunctions

ROOT.PyConfig.IgnoreCommandLineOptions = True


class RootPlotContainer(plotdata.PlotContainer):
	def __init__(self, canvas=None, plot_pad=None, subplot_pad=None):
		self.canvas = canvas
		self.plot_pad = plot_pad
		self.subplot_pad = subplot_pad
	
	def finish(self):
		self.canvas.RedrawAxis()
		if not self.plot_pad is None:
			self.plot_pad.RedrawAxis()
			self.plot_pad.Update()
		if not self.subplot_pad is None:
			self.subplot_pad.RedrawAxis()
			self.subplot_pad.Update()
		self.canvas.Update()
		
	def save(self, filename):
		self.canvas.SaveAs(filename)


class PlotRoot(plotbase.PlotBase):
	def __init__(self):
		super(PlotRoot, self).__init__()
		
		self.text_boxes = []
		
		self.first_plot_histogram = None
		self.first_subplot_histogram = None
	
	def modify_argument_parser(self, parser, args):
		super(PlotRoot, self).modify_argument_parser(parser, args)
		
		self.formatting_options.add_argument("--x-grid", action='store_true', default=False,
		                                     help="Place an x-axes grid on the plot.")
		self.formatting_options.add_argument("--y-grid", action='store_true', default=False,
		                                     help="Place an y-axes grid on the plot.")
		self.formatting_options.add_argument("--marker-styles", nargs="+", default=[20], type=int,
		                                     help="Marker style of plots marker. [Default: %(default)s]")
		self.formatting_options.add_argument("--marker-sizes", nargs="+", default=[1.0], type=float,
		                                     help="Marker sizes of plots marker. [Default: %(default)s]")
		self.formatting_options.add_argument("--fill-styles", type=int, nargs="+",
		                                     help="Fill styles for histograms. Defaults choosen according to draw options.")
		self.formatting_options.add_argument("--line-styles", nargs="+", default=[1], type=int,
		                                     help="Line style of plots line. [Default: %(default)s]")
		self.formatting_options.add_argument("--line-widths", nargs="+", default=[1], type=int,
		                                     help="Line width of plots line. [Default: %(default)s]")
		self.formatting_options.add_argument("--legend", type=float, nargs="*", default=None,
		                                     help="Legend position. The four arguments define the rectangle (x1 y1 x2 y2) for the legend. Without (or with too few) arguments, the default values from [0.6, 0.6, 0.9, 0.9] are used. [Default: %(default)s]")
		self.formatting_options.add_argument("--stacks-errband", action='store_true', default=False,
		                                     help="Draw error band on top of the stacked plots.")
		self.formatting_options.add_argument("--stacks-errband-names", nargs="+",
		                                     help="Nick names for stacked plots for which an error band will be shown. [Default: all but first stack nick]")
		
	def prepare_args(self, parser, plotData):
		super(PlotRoot, self).prepare_args(parser, plotData)
		
		self.prepare_list_args(
				plotData,
				["nicks", "colors", "labels", "markers", "marker_styles", "marker_sizes", "line_styles", "line_widths", "x_errors", "y_errors", "stacks", "axes", "fill_styles"],
				n_items = max([len(plotData.plotdict[l]) for l in ["nicks", "stacks"] if plotData.plotdict[l] is not None]
		))
		
		# defaults for colors
		for index, color in enumerate(plotData.plotdict["colors"]):
			if color == None:
				plotData.plotdict["colors"][index] = index + 1
			else:
				root_color = None
				if color.startswith("k"):
					root_color = getattr(ROOT, color)
				elif color.startswith("#"):
					root_color = ROOT.TColor.GetColor(color)
				else:
					root_color = eval(color)
				plotData.plotdict["colors"][index] = root_color
		self.set_default_ratio_colors(plotData)
		
		# defaults for markers
		for index, (marker, fill_style, stack) in enumerate(zip(plotData.plotdict["markers"],
		                                                        plotData.plotdict["fill_styles"],
		                                                        plotData.plotdict["stacks"])):
			if marker is None:
				if index == 0:
					marker = "E" if len(plotData.plotdict["markers"]) > 1 else "HIST"
				else:
					marker = "LINE" if plotData.plotdict["stacks"].count(stack) == 1 else "HIST"
				# TODO: defaults for 2D/3D histograms
			
			if fill_style is None:
				fill_style = 0
				if "HIST" in marker.upper():
					fill_style = 1001
				elif "LINE" in marker.upper():
					marker = marker.upper().replace("LINE", "HIST")
					fill_style = 0
				elif "E" in marker.upper():
					fill_style = 3003
			
			plotData.plotdict["markers"][index] = marker
			plotData.plotdict["fill_styles"][index] = fill_style
		
		# defaults for stacked plots shaded error band
		if plotData.plotdict["stacks_errband_names"] == None: plotData.plotdict["stacks_errband_names"] = [" ".join(set(plotData.plotdict["stacks"][1:]))]
		plotData.plotdict["stacks_errband_names"] = [nicks.split() for nicks in plotData.plotdict["stacks_errband_names"]]
		for nicks in plotData.plotdict["stacks_errband_names"]:
			for nick in nicks:
				if nick not in plotData.plotdict["stacks"]:
					log.critical("Stack name \"%s\" of argument --%s does not exist in argument --stack!" % (nick, "stacks_errband_names".replace("_", "-")))
					sys.exit(1)
		
		# defaults for legend position
		if not plotData.plotdict["legend"] is None:
			plotData.plotdict["legend"] += [0.6, 0.6, 0.9, 0.9][len(plotData.plotdict["legend"]):]
			plotData.plotdict["legend"] = plotData.plotdict["legend"][:4]
	
	def run(self, plotData):
		super(PlotRoot, self).run(plotData)

	def set_style(self, plotData):
		super(PlotRoot, self).set_style(plotData)
		
		# load TDR Style
		cwd = os.getcwd()
		os.chdir(os.path.expandvars("$CMSSW_BASE/src"))
		ROOT.gROOT.LoadMacro(os.path.expandvars("$CMSSW_BASE/src/Artus/HarryPlotter/python/utility/tdrstyle.C")) # +"+") # compilation currently does not work
		ROOT.setTDRStyle()
		os.chdir(cwd)

	def create_canvas(self, plotData):
		super(PlotRoot, self).create_canvas(plotData)
		
		canvas = None if plotData.plot is None else plotData.plot.canvas
		plot_pad = None if plotData.plot is None else plotData.plot.plot_pad
		subplot_pad = None if plotData.plot is None else plotData.plot.subplot_pad
		
		if canvas is None:
			# TODO: Creating the canvas like this leads to segmentation faults
			canvas = ROOT.TCanvas("canvas", "")
			canvas.Draw()

		#Modify right side margin for 2d-plots
		if not isinstance(plotData.plotdict["root_objects"][plotData.plotdict["nicks"][0]], ROOT.TGraph):
			if plotData.plotdict["root_objects"][plotData.plotdict["nicks"][0]].GetDimension() == 2:
				canvas.SetRightMargin(0.15)
		
		if len(plotData.plotdict["subplot_nicks"]) > 0:
			self.plot_subplot_slider_y = 0.35
			canvas.cd()
			if plot_pad is None:
				plot_pad = ROOT.TPad("plot_pad", "", 0.0, self.plot_subplot_slider_y, 1.0, 1.0)
				plot_pad.SetNumber(1)
				plot_pad.Draw()
			if subplot_pad is None:
				subplot_pad = ROOT.TPad("subplot_pad", "", 0.0, 0.0, 1.0, self.plot_subplot_slider_y)
				subplot_pad.SetNumber(2)
				subplot_pad.Draw()
			
			plot_pad.SetBottomMargin(0.02)
			subplot_pad.SetBottomMargin(0.35)
		
		else:
			plot_pad = canvas
		
		plotData.plot = RootPlotContainer(canvas, plot_pad, subplot_pad)

	def prepare_histograms(self, plotData):
		super(PlotRoot, self).prepare_histograms(plotData)
		
		for nick, color, marker, marker_style, marker_size, fill_style, line_style, line_width in zip(
				plotData.plotdict["nicks"],
				plotData.plotdict["colors"],
				plotData.plotdict["markers"],
				plotData.plotdict["marker_styles"],
				plotData.plotdict["marker_sizes"],
				plotData.plotdict["fill_styles"],
				plotData.plotdict["line_styles"],
				plotData.plotdict["line_widths"]
		):
			root_object = plotData.plotdict["root_objects"][nick]
			if plotData.plotdict["title"]:
				root_object.SetTitle(plotData.plotdict["title"])
			
			root_object.SetLineColor(color)
			root_object.SetLineStyle(line_style)
			root_object.SetLineWidth(line_width)
			
			root_object.SetMarkerColor(color)
			root_object.SetMarkerStyle(marker_style)
			root_object.SetMarkerSize(marker_size)
			
			root_object.SetFillColor(color)
			root_object.SetFillStyle(fill_style)

			# tick labels
			if plotData.plotdict["x_tick_labels"] and len(plotData.plotdict["x_tick_labels"]) > 0:
				for x_bin in range(min(root_object.GetNbinsX(), len(plotData.plotdict["x_tick_labels"]))):
					root_object.GetXaxis().SetBinLabel(x_bin+1, plotData.plotdict["x_tick_labels"][x_bin])
			
			if plotData.plotdict["y_tick_labels"] and len(plotData.plotdict["y_tick_labels"]) > 0:
				for y_bin in range(min(root_object.GetNbinsY(), len(plotData.plotdict["y_tick_labels"]))):
					root_object.GetYaxis().SetBinLabel(y_bin+1, plotData.plotdict["y_tick_labels"][y_bin])
			
			if plotData.plotdict["z_tick_labels"] and len(plotData.plotdict["z_tick_labels"]) > 0:
				for z_bin in range(min(root_object.GetNbinsZ(), len(plotData.plotdict["z_tick_labels"]))):
					root_object.GetZaxis().SetBinLabel(z_bin+1, plotData.plotdict["z_tick_labels"][z_bin])
	
	def make_plots(self, plotData):
		super(PlotRoot, self).make_plots(plotData)
		
		self.x_min = sys.float_info.max
		self.x_max = -sys.float_info.max
		
		self.y_min = sys.float_info.max
		self.y_max = -sys.float_info.max
		self.y_subplot_min = sys.float_info.max
		self.y_subplot_max = -sys.float_info.max
		
		self.z_min = sys.float_info.max
		self.z_max = -sys.float_info.max
		
		index_plot = -1
		index_subplot = -1
		for index, (nick, subplot, marker) in enumerate(zip(
				plotData.plotdict["nicks"],
				plotData.plotdict["subplots"],
				plotData.plotdict["markers"]
		)):
			pad = None
			
			# select pad to plot on
			if subplot == True:
				index_subplot += 1
				pad = plotData.plot.subplot_pad
				y_min = self.y_subplot_min
				y_max = self.y_subplot_max
			else:
				index_plot += 1
				pad = plotData.plot.plot_pad
				y_min = self.y_min
				y_max = self.y_max
			
			root_object = plotData.plotdict["root_objects"][nick]
			
			draw_option = marker
			if ((not subplot) and (index_plot > 0)) or (subplot and (index_subplot > 0)):
				draw_option += " SAME"
			
			pad.cd()
			axes_histogram = None
			if isinstance(root_object, ROOT.TH1):
				axes_histogram = self._draw_histogram(pad, root_object, draw_option)
			elif isinstance(root_object, ROOT.TGraph):
				axes_histogram = self._draw_graph(
						pad,
						root_object,
						draw_option+(" A" if index == 0 else ""),
						plotData.plotdict["x_lims"],
						plotData.plotdict["y_subplot_lims" if subplot else "y_lims"],
						plotData.plotdict["z_lims"])
			else:
				log.error("ROOT plotting is not (yet) implemented for objects of type %s!" % type(root_object))
			
			if axes_histogram:
				if subplot and (index_subplot == 0):
					self.first_subplot_histogram = axes_histogram
				elif (not subplot) and (index_plot == 0):
					self.first_plot_histogram = axes_histogram
				
				# trace min. and max. values of axes
				dimension = PlotRoot._get_dimension(axes_histogram)
				if axes_histogram.GetXaxis().GetXmin() < self.x_min: self.x_min = axes_histogram.GetXaxis().GetXmin()
				if axes_histogram.GetXaxis().GetXmax() > self.x_max: self.x_max = axes_histogram.GetXaxis().GetXmax()
				if dimension > 1:
					if axes_histogram.GetYaxis().GetXmin() < y_min: y_min = axes_histogram.GetYaxis().GetXmin()
					if axes_histogram.GetYaxis().GetXmax() > y_max: y_max = axes_histogram.GetYaxis().GetXmax()
				else:
					if axes_histogram.GetMinimum() < y_min: y_min = axes_histogram.GetMinimum()
					if axes_histogram.GetMaximum() > y_max: y_max = axes_histogram.GetMaximum()
				if dimension > 2:
					if axes_histogram.GetZaxis().GetXmin() < self.z_min: self.z_min = axes_histogram.GetZaxis().GetXmin()
					if axes_histogram.GetZaxis().GetXmax() > self.z_max: self.z_max = axes_histogram.GetZaxis().GetXmax()
				else:
					if axes_histogram.GetMinimum() < self.z_min: self.z_min = axes_histogram.GetMinimum()
					if axes_histogram.GetMaximum() > self.z_max: self.z_max = axes_histogram.GetMaximum()
			
			if subplot:
				self.y_sub_min = y_min
				self.y_sub_max = y_max
			else:
				self.y_min = y_min
				self.y_max = y_max
	
	def _draw_histogram(self, pad, root_histogram, draw_option):
		assert isinstance(root_histogram, ROOT.TH1)
		pad.cd()
		root_histogram.Draw(draw_option)
		return root_histogram
	
	def _draw_graph(self, pad, root_graph, draw_option, x_lims, y_lims, z_lims):
		assert isinstance(root_graph, ROOT.TGraph)
		pad.cd()
		PlotRoot._set_axis_limits(root_graph, x_lims, y_lims, z_lims)
		root_graph.Draw(draw_option)
		root_histogram = root_graph.GetHistogram()
		return root_histogram
	
	def modify_axes(self, plotData):
		super(PlotRoot, self).modify_axes(plotData)
	
		# axis labels
		self.first_plot_histogram.GetXaxis().SetTitle(plotData.plotdict["x_label"])
		self.first_plot_histogram.GetYaxis().SetTitle(plotData.plotdict["y_label"])
		self.first_plot_histogram.GetZaxis().SetTitle(plotData.plotdict["z_label"])
		if not self.first_subplot_histogram is None:
			self.first_subplot_histogram.GetXaxis().SetTitle(plotData.plotdict["x_label"])
			self.first_subplot_histogram.GetYaxis().SetTitle(plotData.plotdict["y_subplot_label"])
	
		# logaritmic axis
		if plotData.plotdict["x_log"]: plotData.plot.plot_pad.SetLogx()
		if plotData.plotdict["y_log"]: plotData.plot.plot_pad.SetLogy()
		if plotData.plotdict["z_log"]: plotData.plot.plot_pad.SetLogz()
		if not plotData.plot.subplot_pad is None:
			if plotData.plotdict["x_log"]: plotData.plot.subplot_pad.SetLogx()
	
		# axis limits
		x_lims = plotData.plotdict["x_lims"] if not plotData.plotdict["x_lims"] is None else [self.x_min, self.x_max]
		y_lims = plotData.plotdict["y_lims"] if not plotData.plotdict["y_lims"] is None else [self.y_min, self.y_max]
		z_lims = plotData.plotdict["z_lims"] if not plotData.plotdict["z_lims"] is None else [self.z_min, self.z_max]
		PlotRoot._set_axis_limits(self.first_plot_histogram, x_lims, y_lims, z_lims)
		
		if not self.first_subplot_histogram is None:
			y_subplot_lims = plotData.plotdict["y_subplot_lims"] if not plotData.plotdict["y_subplot_lims"] is None else [self.y_subplot_min, self.y_subplot_max]
			z_subplot_lims = None # TODO: z-lims for possible 3D subplots
			PlotRoot._set_axis_limits(self.first_subplot_histogram, x_lims, y_subplot_lims, z_subplot_lims)
		
		if not self.first_subplot_histogram is None:
			self.first_plot_histogram.GetXaxis().SetLabelSize(0)
			self.first_plot_histogram.GetXaxis().SetTitleSize(0)
			self.first_plot_histogram.GetYaxis().SetLabelSize(self.first_plot_histogram.GetYaxis().GetLabelSize() / (1.0 - self.plot_subplot_slider_y))
			self.first_plot_histogram.GetYaxis().SetTitleSize(self.first_plot_histogram.GetYaxis().GetTitleSize() / (1.0 - self.plot_subplot_slider_y))
			
			self.first_plot_histogram.GetYaxis().SetTitleOffset(self.first_plot_histogram.GetYaxis().GetTitleOffset() * (1.0 - self.plot_subplot_slider_y))
			
			self.first_subplot_histogram.GetXaxis().SetLabelSize(self.first_subplot_histogram.GetXaxis().GetLabelSize() / self.plot_subplot_slider_y)
			self.first_subplot_histogram.GetXaxis().SetTitleSize(self.first_subplot_histogram.GetXaxis().GetTitleSize() / self.plot_subplot_slider_y)
			self.first_subplot_histogram.GetYaxis().SetLabelSize(self.first_subplot_histogram.GetYaxis().GetLabelSize() / self.plot_subplot_slider_y)
			self.first_subplot_histogram.GetYaxis().SetTitleSize(self.first_subplot_histogram.GetYaxis().GetTitleSize() / self.plot_subplot_slider_y)
			
			self.first_subplot_histogram.GetXaxis().SetTitleOffset(2.0 * self.first_subplot_histogram.GetXaxis().GetTitleOffset() * self.plot_subplot_slider_y)
			self.first_subplot_histogram.GetYaxis().SetTitleOffset(self.first_subplot_histogram.GetYaxis().GetTitleOffset() * self.plot_subplot_slider_y)
			
			self.first_subplot_histogram.GetYaxis().SetNdivisions(5, 0, 0)
		
		# redraw axes only and update the canvas
		plotData.plot.plot_pad.cd()
		self.first_plot_histogram.Draw("AXIS SAME")
		plotData.plot.plot_pad.Update()
		
		if not plotData.plot.subplot_pad is None:
			plotData.plot.subplot_pad.cd()
			if not self.first_subplot_histogram is None:
				self.first_subplot_histogram.Draw("AXIS SAME")
			plotData.plot.subplot_pad.Update()
		
		plotData.plot.canvas.Update()
			
		
	def add_grid(self, plotData):
		super(PlotRoot, self).add_grid(plotData)
		
		plotData.plot.plot_pad.cd()
		if (plotData.plotdict["grid"] or plotData.plotdict["x_grid"]):
			plotData.plot.plot_pad.SetGridx()
		if (plotData.plotdict["grid"] or plotData.plotdict["y_grid"]):
			plotData.plot.plot_pad.SetGridy()
		
		if not plotData.plot.subplot_pad is None:
			plotData.plot.subplot_pad.cd()
			if (plotData.plotdict["subplot_grid"] == True):
				plotData.plot.subplot_pad.SetGrid()
	
	def add_labels(self, plotData):
		super(PlotRoot, self).add_labels(plotData)
		
		plotData.plot.plot_pad.cd()
		self.legend = None
		if plotData.plotdict["legend"] != None:
			self.legend = ROOT.TLegend(*plotData.plotdict["legend"]);
			for nick, subplot, marker, label in zip(
					plotData.plotdict["nicks"],
					plotData.plotdict["subplots"],
					plotData.plotdict["markers"],
					plotData.plotdict["labels"]
			):
				if subplot == True:
					# TODO handle possible subplot legends
					continue
				root_object = plotData.plotdict["root_objects"][nick]
				if (not label is None) and (label != ""):
					self.legend.AddEntry(root_object, label, "LP" if "e" in marker.lower() else "F")
			self.legend.Draw()
	
	def add_texts(self, plotData):
		super(PlotRoot, self).add_texts(plotData)
		if plotData.plotdict["texts"] != [None]:
			plotData.plot.plot_pad.cd()
			for x, y, text in zip(plotData.plotdict['texts_x'], plotData.plotdict['texts_y'], plotData.plotdict['texts']):
				self.text_boxes.append(ROOT.TPaveText(0.0, 0.0, 1.0, 1.0, "NDC"))
				self.text_boxes[-1].AddText(x, y, text*5)
				self.text_boxes[-1].SetFillStyle(0)
				self.text_boxes[-1].SetShadowColor(0)
				self.text_boxes[-1].SetTextSize(0.05)
				self.text_boxes[-1].Draw("SAME")
	
	@staticmethod
	def _get_dimension(root_object):
		dimension = 2
		if isinstance(root_object, ROOT.TH1):
			dimension = root_object.GetDimension()
		elif isinstance(root_object, ROOT.TGraph2D):
			dimension = 3
		elif isinstance(root_object, ROOT.TGraph):
			dimension = 2
		else:
			log.warning("Retrieving the dimension of the plot is not yet implemented for objects of type %s!. Assume 2D plot." % str(type(axes_histogram)))
		return dimension
	
	@staticmethod
	def _set_axis_limits(root_object, x_lims=None, y_lims=None, z_lims=None):
		dimension = PlotRoot._get_dimension(root_object)
		
		if not x_lims is None:
			root_object.GetXaxis().SetRangeUser(*x_lims)
			root_object.GetXaxis().SetLimits(*x_lims)
		
		if (dimension > 1) and (not y_lims is None):
			root_object.GetYaxis().SetRangeUser(*y_lims)
			root_object.GetYaxis().SetLimits(*y_lims)
		
		if (dimension > 2) and (not z_lims is None):
			root_object.GetZaxis().SetRangeUser(*y_lims)
			root_object.GetZaxis().SetLimits(*y_lims)

