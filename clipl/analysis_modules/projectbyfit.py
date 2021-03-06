# -*- coding: utf-8 -*-

"""
"""

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)
import sys
import ROOT
import hashlib
import clipl.analysisbase as analysisbase

import clipl.analysis_modules.functionfit as functionfit
import clipl.analysis_modules.projectionY as projectionY
import copy

class ProjectByFit(analysisbase.AnalysisBase):
	def __init__(self):
		super(ProjectByFit, self).__init__()
		self.replace = True

	def modify_argument_parser(self, parser, args):
		self.projectbyfit_options = parser.add_argument_group("Options for ProjectByFit module. See TH2::FitSlicesY for documentation. \
								Pay attention that the fit will be performed on histogram set for Y-Axis, in bins of X-Axis (should be controlled using --x-bins option).")
		self.projectbyfit_options.add_argument("--projection-functions", type=str, nargs="+", default=None,
								help="Functions to project along Y-Axis. Basically functions which will be fitted in terms of Y-Axis histogram")
		self.projectbyfit_options.add_argument("--projection-parameters", type=str, nargs="+", default=None,
								help="Starting parameters for the fit, comma seperated.")
		self.projectbyfit_options.add_argument("--projection-to-plot", type=str, nargs="+", default="0",
								help="Parameter number that should be plotted or TFormula to combine parameters of fit. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-fit-range", type=str, nargs="+", default=None,
								help="Y-Range to perform the fit in the format \"low,high\". Default is the whole range of the input 2D Histogram Y-Axis.\
								The number of passed arguments should correspond to the number of arguments in --projection-to-nick.")
		self.projectbyfit_options.add_argument("--projection-to-nick", type=str, nargs="+", default="nick0",
								help="Nickname of 2D input histogram. The starting histogram by default will be replaced by a fit-evaluated.\
								The number of passed arguments should correspond to the number of arguments in --projection-fit-range. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-fit-backend", type=str, nargs="+", default="ROOT",
								help="Fit backend. ROOT and RooFit are available. Check sourcecode which parts of RooFit are implemented. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-bins-minx", type=str, nargs="+", default="0",
								help="Fit starting from this bin along X. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-bins-maxx", type=str, nargs="+", default="-1",
								help="Fit starting from this bin along X. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-options", type=str, nargs="+", default="QNR",
								help="The argument option can be used to change the fit options. If debug mode is enabled the 'Q' option will be always removed. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-cuts-bins-filled", type=str, nargs="+", default="0",
								help="Fit for bins in X for which the corresponding projection along Y has more than **cut** bins filled. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-fit-slices-z", type="bool", nargs="?", default=False, const=True,
								help="Call `void TH3::FitSlicesZ`. The fitted distribution should be set along Z-Axis. Root reference: https://root.cern.ch/doc/v608/classTH3.html#a927fb729e31d90ecbcc2b5e4f9e23900 . [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-bins-miny", type=str, nargs="+", default="0",
								help="Fit starting from this bin along Y. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-bins-maxy", type=str, nargs="+", default="-1",
								help="Fit starting from this bin along Y. [Default: %(default)s]")
		self.projectbyfit_options.add_argument("--projection-result-nicks", nargs="+",
								help="Nick names for the resulting ratio graphs. \
								If the nicknames ARE Not specified the initial histogram will be replaced \
								UNLESS this behaviour is rewritten by the --projection-not-override option.\
								If the nicknames ARE specified the initial histogram will be replaced \
								UNLESS this behaviour is rewritten by the --projection-not-override option.")
		self.projectbyfit_options.add_argument("--projection-not-override", type="bool", nargs="?", default=False, const=True,
								help="Force not to override the initial histograms. [Default: %(default)s]")

	def prepare_args(self, parser, plotData):
		super(ProjectByFit, self).prepare_args(parser, plotData)
		self.prepare_list_args(plotData, ["projection_functions", "projection_parameters", "projection_to_plot",
			                              "projection_fit_range", "projection_to_nick", "projection_fit_backend",
			                              "projection_bins_minx", "projection_bins_maxx", "projection_options",
			                              "projection_cuts_bins_filled", "projection_fit_slices_z", "projection_bins_miny",
			                              "projection_bins_maxy", "projection_result_nicks", "projection_not_override"])
		plotData.plotdict["projection_fit_range"] = [ x.replace("\\", "") if x != None else x for x in plotData.plotdict["projection_fit_range"] ]

		for index, (not_override, projection_to_nick, projection_result_nicks) in enumerate(zip(*[plotData.plotdict[k] for k in ["projection_not_override", "projection_to_nick", "projection_result_nicks"]])):
			if projection_result_nicks is None:
				plotData.plotdict["projection_result_nicks"][index] = "projection_result_nicks_{nick}".format(nick="_".join([projection_to_nick]))

			if not plotData.plotdict["projection_result_nicks"][index] in plotData.plotdict["nicks"] and not_override:
				plotData.plotdict["nicks"].append(plotData.plotdict["projection_result_nicks"][index])

	def run(self, plotData=None):
		super(ProjectByFit, self).run()

		result_histograms = {}

		for function, start_parameter, parameter_to_plot, fit_range, nick, \
		    fit_backend, bin_minx, bins_maxx, option, cut_bins_filled, bin_miny, \
		    bin_maxy, fit_slices_z, result_nick, not_override in zip(plotData.plotdict["projection_functions"],
		                                                             plotData.plotdict["projection_parameters"],
		                                                             plotData.plotdict["projection_to_plot"],
		                                                             plotData.plotdict["projection_fit_range"],
		                                                             plotData.plotdict["projection_to_nick"],
		                                                             plotData.plotdict["projection_fit_backend"],
		                                                             plotData.plotdict["projection_bins_minx"],
		                                                             plotData.plotdict["projection_bins_maxx"],
		                                                             plotData.plotdict["projection_options"],
		                                                             plotData.plotdict["projection_cuts_bins_filled"],
		                                                             plotData.plotdict["projection_bins_miny"],
		                                                             plotData.plotdict["projection_bins_maxy"],
		                                                             plotData.plotdict["projection_fit_slices_z"],
		                                                             plotData.plotdict["projection_result_nicks"],
		                                                             plotData.plotdict["projection_not_override"]):

			histogram_ND = plotData.plotdict["root_objects"][nick]

			if log.isEnabledFor(logging.DEBUG): option.translate(None, "Q")
			if not histogram_ND.ClassName().startswith("TH3" if fit_slices_z else "TH2"):
				log.critical("The ProjectByFit Module only works on projecting " + ("TH3" if fit_slices_z else "TH2") + " histograms to " + ("TH2" if fit_slices_z else "TH1") + " histograms, but " + histogram_ND.ClassName() + " was provided as input.")
				sys.exit(1)

			# Estimating fit range
			if fit_range != None:
				fit_min = float(fit_range.split(",")[0])
				fit_max = float(fit_range.split(",")[1])
			elif not fit_slices_z:
				fit_min = histogram_ND.GetYaxis().GetXmin()
				fit_max = histogram_ND.GetYaxis().GetXmax()
			elif fit_slices_z:
				fit_min = histogram_ND.GetZaxis().GetXmin()
				fit_max = histogram_ND.GetZaxis().GetXmax()
			start_parameters = [float(x) for x in start_parameter.split(",")]

			# Getting fitted histogram
			if fit_backend == "ROOT":
				root_function = functionfit.FunctionFit.create_tf1(function, fit_min, fit_max, start_parameters, nick=nick)
				if not fit_slices_z:
					aSlices = ROOT.TObjArray()
					histogram_ND.FitSlicesY(root_function,  int(bin_minx), int(bins_maxx), int(cut_bins_filled), option, aSlices)
					if log.isEnabledFor(logging.DEBUG): aSlices[int(parameter_to_plot)].Print("all")
				else:
					histogram_ND.FitSlicesZ(root_function,  int(bin_minx), int(bins_maxx), int(bin_miny), int(bin_maxy), int(cut_bins_filled), option)

				if parameter_to_plot.isdigit():
					fitted_histogram = copy.deepcopy(ROOT.gDirectory.Get(histogram_ND.GetName() + "_" + str(parameter_to_plot)))
				else:
					fitted_histograms = []
					for i in range(len(start_parameters)):
						fitted_histograms.append(copy.deepcopy(ROOT.gDirectory.Get(histogram_ND.GetName() + "_" + str(i))))
					fitted_histogram = self.postprocess_fits(fitted_histograms, parameter_to_plot)
			elif fit_backend == "RooFit":
				fitted_histogram = self.fitSlicesRooFit(histogram_ND, function, start_parameters, parameter_to_plot)
			else:
				log.critical("No such backend")
				sys.exit(1)

			if not_override:
				result_histograms[result_nick] = fitted_histogram
			else:
				result_histograms[nick] = fitted_histogram

		plotData.plotdict["root_objects"].update(result_histograms)

	@staticmethod
	def fitSlicesRooFit(histogram_2D, function, start_parameters, parameter_to_plot):
		name = histogram_2D.GetName()
		result_histo = ROOT.TH1F(histogram_2D.GetName() + "_projection", "",
		                         histogram_2D.GetNbinsX(),
		                         histogram_2D.GetXaxis().GetXmin(),
		                         histogram_2D.GetXaxis().GetXmax())

		slice_generator =  projectionY.ProjectionY.histoSlice(histogram_2D)
		for ibin, fit_histogram in enumerate(slice_generator):
			val, error = functionfit.FunctionFit.get_roofit_parameter(function,
		                         fit_histogram.GetXaxis().GetXmin(),
		                         fit_histogram.GetXaxis().GetXmax(),
		                         start_parameters,
		                         fit_histogram,
		                         parameter_to_plot)
			result_histo.SetBinContent(ibin + 1, val)
			result_histo.SetBinError(ibin + 1, error)

		return result_histo

	@staticmethod
	def postprocess_fits(fitted_histograms, equation):
		result_histo = ROOT.TH1F(fitted_histograms[0].GetName() + "_projection", "",
								 fitted_histograms[0].GetNbinsX(),
								 fitted_histograms[0].GetXaxis().GetXmin(),
								 fitted_histograms[0].GetXaxis().GetXmax())
		root_formula = ROOT.TFormula("postprocess_fits", equation)

		for ibin in xrange(1, fitted_histograms[0].GetNbinsX() + 1):
			for i, fitted_histogram in enumerate(fitted_histograms):
				root_formula.SetParameter(i, fitted_histogram.GetBinContent(ibin))
			result_histo.SetBinContent(ibin, root_formula.Eval(0))

		return result_histo
