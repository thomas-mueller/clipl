import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)

import ROOT
import Artus.HarryPlotter.analysisbase as analysisbase
import hashlib

class FunctionPlot(analysisbase.AnalysisBase):
	def __init__(self):
		super(FunctionPlot, self).__init__()

	def modify_argument_parser(self, parser, args):
		self.function_options = parser.add_argument_group("Function draw options")
		self.function_options.add_argument("--functions", type=str, nargs="+", default=None,
						help="Function to include in plot, ROOT syntax.")
		self.function_options.add_argument("--function-nicknames", type=str, nargs="+",
						help="Nickname of the function")
		self.function_options.add_argument("--function-parameters", type=str, nargs="+", default=None,
						help="Comma-Separated function parameters for functions given with --function. If a fit is performed, these are the starting parameters for the fit.")
		self.function_options.add_argument("--function-fit", type=str, nargs="+", default=None,
						help="Fit function to histogram with nickname as argument")
		self.function_options.add_argument("--function-ranges", type=str, nargs="+", default=None,
						help="Function range. Default is whole plot range if histogram is drawn. Format x_min,x_max.")
		self.function_options.add_argument("--fit-backend", type=str, nargs="+", default="ROOT",
						help="Fit backend. ROOT and RooFit are available. Check sourcecode which parts of RooFit are implemented. [Default: %(default)s]")

	def prepare_args(self, parser, plotData):
		self.prepare_list_args(plotData, ["functions", "function_parameters", "function_nicknames",
						                  "function_fit", "function_ranges", "fit_backend"])
		tmp_x_range = []
		for x_range in plotData.plotdict["function_ranges"]:
			if x_range==None:
				log.debug("Trying to determine the function range automatically")
				if plotData.plotdict["x_lims"]!=None:
					tmp_x_range.append(plotData.plotdict["x_lims"])
				elif plotData.plotdict["root_objects"] != None:
					x_high = []
					x_low = []
					for key, histo in plotData.plotdict["root_objects"].iteritems():
						x_high.append( histo.GetXaxis().GetXmax() )
						x_low.append( histo.GetXaxis().GetXmin() )
					tmp_x_range.append( [ min(x_low), min(x_high)] )
				else:
					log.fatal("Please provide fucntion ranges for the FunctionPlot Module")
					sys.exit(1)
			else:
				tmp_x_range.append( [float (x) for x in  x_range.split(",")] )
		plotData.plotdict["function_ranges"] = tmp_x_range
		
		plotData.plotdict["function_nicknames"] = [nick if nick != None else ("function_nick%d" % index) for index, nick in enumerate(plotData.plotdict["function_nicknames"])]
		plotData.plotdict["nicks"] += plotData.plotdict["function_nicknames"]

		tmp_function_parameters = []
		for function_parameter in plotData.plotdict["function_parameters"]:
			tmp_function_parameters.append([float (x) for x in  function_parameter.split(",")])
		plotData.plotdict["function_parameters"] = tmp_function_parameters

		super(FunctionPlot, self).prepare_args(parser, plotData)


	def run(self, plotData=None):
		super(FunctionPlot, self).run()
		if plotData.plotdict["functions"] == None:
			log.info("You are using the FunctionPlot module. Please provide at least one input function with --function")
			os.exit(1)
		else:
			for i, (function, function_nick, function_parameters, fit_nickname, x_range, fit_backend) in enumerate(zip( 
			                                                 plotData.plotdict["functions"], 
			                                                 plotData.plotdict["function_nicknames"],
			                                                 plotData.plotdict["function_parameters"],
			                                                 plotData.plotdict["function_fit"],
			                                                 plotData.plotdict["function_ranges"],
			                                                 plotData.plotdict["fit_backend"])):
				if fit_nickname != None and fit_nickname in plotData.plotdict["root_objects"].keys(): 
					root_histogram = plotData.plotdict["root_objects"][fit_nickname]
					plotData.plotdict["root_objects"][function_nick] = self.create_function(function, x_range[0], x_range[1], 
					                                           function_parameters, 
					                                           nick=fit_nickname, 
					                                           root_histogram=root_histogram,
					                                           fit_backend=fit_backend)
				else: 
					plotData.plotdict["root_objects"][function_nick] = self.create_function(function, x_range[0], x_range[1], function_parameters)


	def create_function(self, function, x_min, x_max, start_parameters, nick="", root_histogram=None, fit_backend="ROOT"):
		"""
		creates a function from input formula from either ROOT or RooFit backend.

		does the fit and adds the fitted function to the dictionary
		"""
		# todo: ensure to have as many start parameters as parameters in formula
		if fit_backend == "RooFit":
			root_function, mean, sigma, width = self.do_roofit(function, x_min, x_max, start_parameters, root_histogram)
		elif fit_backend == "ROOT":
			root_function = self.do_rootfit(function, x_min, x_max, start_parameters, nick, root_histogram)
		else:
			print "No valid fit backend selected"
			exit()
		return root_function

	@staticmethod
	def create_tf1(function, x_min, x_max, start_parameters, nick="", root_histogram=None):
		formula_name = ("function_" + nick).format(hashlib.md5("_".join([str(function), str(x_min), str(x_max),
		                                                                str(start_parameters), str(nick), 
		                                                                str(root_histogram.GetName() if root_histogram != None else "")])).hexdigest())
		return ROOT.TF1(formula_name, function, x_min, x_max)

	@staticmethod
	def do_rootfit(function, x_min, x_max, start_parameters, nick="", root_histogram=None):
		root_function = FunctionPlot.create_tf1(function, x_min, x_max, start_parameters, nick, root_histogram)
		# set parameters for fit or just for drawing the function
		for parameter_index in range(root_function.GetNpar()):
			root_function.SetParameter(parameter_index, start_parameters[parameter_index])
		root_histogram.Fit(root_function.GetName(), "", "", x_min, x_max)
		return root_function

	@staticmethod
	def do_roofit(function, x_min, x_max, start_parameters, root_histogram):

		integral = root_histogram.Integral()
		x = ROOT.RooRealVar("x", "x", x_min, x_max)
		dh = ROOT.RooDataHist("dh", "dh", ROOT.RooArgList(x), root_histogram)

		frame = x.frame()
		ROOT.RooAbsData.plotOn(dh, frame)

		mean  = ROOT.RooRealVar("mean", "mean", start_parameters[0],
			                                    start_parameters[1],
			                                    start_parameters[2])
		sigma = ROOT.RooRealVar("sigma","sigma",start_parameters[3],
			                                    start_parameters[4],
			                                    start_parameters[5])
		width = ROOT.RooRealVar("width","width",start_parameters[6],
			                                    start_parameters[7],
			                                    start_parameters[8])
		if (function == "voigtian"):
			function = ROOT.RooVoigtian("func","func",x,mean,width,sigma)
		elif (function == "breitwiegner"):
			function = ROOT.RooBreitWiegner("func","func",x,mean,sigma)
		elif (function == "gaus"):
			function = ROOT.RooGaussian("func","func",x,mean,sigma)
		else:
			print "selected fit function " + function + " currently not supported from functionplot modul with RooFit backend."
			exit()
		
		filters = function.fitTo(dh,ROOT.RooLinkedList())
		function.plotOn(frame, ROOT.RooLinkedList())
		#TODO: normalization does not work for some reason
		#function.plotOn(frame, ROOT.RooFit.Normalization(1.0, ROOT.RooAbsReal.Relative))
		root_function = ROOT.RooCurve(function, x, x_min, x_max, 1000)
		return root_function, mean, sigma, width

	@staticmethod
	def get_roofit_parameter(function, x_min, x_max, start_parameters, root_histogram, parameter):
		retVal = [0,0,0]
		root_function, retVal[0], retVal[1], retVal[2] = FunctionPlot.do_roofit(function, x_min, x_max, start_parameters, root_histogram)
		return retVal[parameter].getVal(), retVal[parameter].getError()

	def get_parameters(self, root_function):
		parameters = []
		parameter_errors = []
		chi_square = root_function.GetChisquare()
		ndf = root_function.GetNDF()
		for parameter_index in range(root_function.GetNpar()):
			parameters.append(root_function.GetParameter(parameter_index))
			parameter_errors.append(root_function.GetParError(parameter_index))
		return parameters, parameter_errors, chi_square, ndf
