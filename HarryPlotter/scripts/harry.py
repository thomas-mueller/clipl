#### todo: re-enable live plotting
#### todo: allow push to webserver
#### todo: enable 2D plotting with stacked inputs
#### todo: allow formula plotting
#### todo: use dictionaries

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is the main plotting program

	It handles only the options, the main functionality is in python/harrycore.py
"""

import os
import argparse
import subprocess
import matplotlib

import Artus.HarryPlotter.harrycore as harrycore
import Artus.HarryPlotter.tools.plotrc as plotrc


def options(
			# standard values go here:
#			files=[os.environ['DATA'], os.environ['MC']],

			plots=['zmass'],
			out="out",
			formats=['png'],

			labels=["data", "MC"],
			colors=['black', '#CBDBF9'],
			markers=["o", "f"],
			lumi=19.712,
			energy=8,
			status=None,
			author=None,
			date=None,
			layout='generic',
			title="",
			eventnumberlabel=None,
			legloc='best',

			nbins=20,
			rebin=5,
			ratio=False,
			fit=None,
			filename=None,

	):
	"""Set standard options and read command line arguments.

	To be turned into a class with str method and init
	"""

	parser = argparse.ArgumentParser(
		description="%(prog)s does all the plotting.",
		epilog="Have fun.")

	#plots
	parser.add_argument('plots', type=str, nargs='*', default=plots,
		help="do only this plot/these plots. " +
			 "The function names are required here.")

	# source options
	source = parser.add_argument_group('Source options')
	parser.add_argument('-i', '--files', type=str, nargs='*',
		#default=files,
		help="Input root file(s). Specify their affiliation with -a.") # todo: allow many different input files, that are also not yet added
	parser.add_argument('-a', '--affiliation', type=str, nargs='*',
		help="Affiliation and name of input files. Specify the same name to produce stacked plots.")
#	parser.add_argument('--sample-name', type=str, nargs='*',
#		help="Name of the samples provided with --files. Necessary to produce stacked plots.")


	source.add_argument('--selection', '-S', type=str,
		default=None,
		help='selection (cut) expression, C++ expressions are valid')
	source.add_argument('--folder', type=str, nargs='*',
		default='incut',
		help="folder in rootfile. Specify only once if everything is in the same folder or multiple times for each input file.")

	# more general options
	general = parser.add_argument_group('General options')
	general.add_argument('-r', '--rebin', type=int, default=rebin,
		help="Rebinning value n")
	general.add_argument('-R', '--ratio', action='store_true',
		help="do a ratio plot from the first two input files")
	general.add_argument('--ratiosubplot', action='store_true',
		help="Add a ratio subplot")
	general.add_argument('-F', '--fit', type=str, default=fit,
		help="Do a fit. Options: vertical, chi2, gauss, slope, intercept")
	general.add_argument('--run', type=str, default=False,
		help='Some special options for runplots. Valid options are true or diff')
	general.add_argument('--nbins', type=int, default=nbins,
		help='number of bins in histogram. Default is %(default)s')
	general.add_argument('-Y', '--year', type=int, default=2012,
		help="Year of data-taking. Default is %(default)s") # generalize this information
	general.add_argument('--factor', type=float, default=1.0,
		help="additional external weight for each MC event %(default)s")
	general.add_argument('--efficiency', type=float, default= 1.0,
		help="trigger efficiency. Default is %(default)s")
	general.add_argument('--reweight', action='store_true',
		help="trigger efficiency. Default is %(default)s")

	# output settings
	output = parser.add_argument_group('Output options')
	output.add_argument('-o', '--out', type=str, default=out,
		help="output directory for plots")
	output.add_argument('-f', '--formats', type=str, nargs='+', default=formats,
		help="output format for the plots.  Default is %(default)s")
	output.add_argument('--filename', type=str, default=filename,
		help='specify a filename')
	output.add_argument('--root', type=str, default=False,
		help="Name of the histogramm which is then saved into a root file")
	output.add_argument('--save_individually', action='store_true',
		default=False,
		help='save each plot separately')

	# plot labelling and formatting
	formatting = parser.add_argument_group('Formatting options')
	formatting.add_argument('-l', '--lumi', type=float, default=lumi,
		help="luminosity for the given data in /fb. Default is %(default)s")
	formatting.add_argument('-e', '--energy', type=int, default=energy,
		help="centre-of-mass energy for the given samples in TeV. \
													   Default is %(default)s")

	formatting.add_argument('-s', '--status', type=str, default=status,
		help="status of the plot (e.g. CMS preliminary)")
	formatting.add_argument('-A', '--author', type=str, default=author,
		help="author name of the plot")
	formatting.add_argument('--date', type=str, default=date,
		help="show the date in the top left corner. 'iso' is YYYY-MM-DD, " +
			 "'today' is DD Mon YYYY and 'now' is DD Mon YYYY HH:MM.")
	formatting.add_argument('-E', '--eventnumberlabel', action='store_true',
		help="add event number label")
	formatting.add_argument('-t', '--title', type=str, default=title,
		 help="plot title")
	formatting.add_argument('--layout', type=str,
		default='generic',
		help="layout for the plots. E.g. 'document': serif, LaTeX, pdf; " +
			 "'slides': sans serif, big, png; 'generic': slides + pdf. " +
			 "This is not implemented yet.")
	formatting.add_argument('-g', '--legloc', type=str, nargs="?", default=legloc,
		help="Location of the legend. Default is %(default)s. Possible values " +
			 "are keywords like 'lower left' or coordinates like '0.5,0.1'.")
	formatting.add_argument('--subtext', type=str, default=None,
		help='Add subtext')
	formatting.add_argument('-C', '--colors', type=str, nargs='+', default=colors,
		help="colors for the plots in the order of the files. Default is: " +
			 ", ".join(colors))
#	formatting.add_argument('-k', '--labels', type=str, nargs='+', default=labels,
#		help="labels for the plots in the order of the files. Default is: " +
#			 ", ".join(labels))
	formatting.add_argument('-m', '--markers', type=str, nargs='+', default=markers,
		help="style for the plot in the order of the files. 'o' for points, \
			  '-' for lines, 'f' for fill. Default is: %s" % ", ".join(markers))
	formatting.add_argument('--errorbar', default=["True"], nargs='+',
		help="Include errorbars. Give one argument to count for all curves or one for each input file")

	formatting.add_argument('--text', type=str,
		default=None,
		help='Place a text at a certain location. Syntax is --text="abs" or \
														  --text="abc,0.5,0.9"')
	formatting.add_argument('-G', '--grid', action='store_true', default=False,
		help="Place an axes grid on the plot.")

	formatting.add_argument('--cutlabel', type=str,
		#default=None, help="Place a cutlabel on the plot. Options are: %s"
		#							 % ", ".join(plotbase.cutlabeldict.keys()))
		default=None, help="Place a cutlabel on the plot.")

	# AXIS
	axis = parser.add_argument_group('Axis options')
	axis.add_argument('--log', action='store_true', default=None,
		 help="log plot")
	axis.add_argument('--xlog', action='store_true', default=None,
		 help="xlog plot")
	axis.add_argument('-y', type=float, nargs='+', default=None,
		help="upper and lower limit for y-axis")
	axis.add_argument('-x', type=float, nargs='+', default=None,
		help="upper and lower limit for x-axis")
	axis.add_argument('-z', type=float, nargs='+', default=None,
		help="upper and lower limit for z-axis")
	axis.add_argument('--xynames', type=str, nargs='+', default=None,
		help='x-y-axis label names,')

	axis.add_argument('--xticks', type=float, nargs='+', default=None,
		help="add custom xticks")

	# Other options
	group = parser.add_argument_group('Other options')
	group.add_argument('-v', '--verbose', action='store_true',
		help="verbosity")
	group.add_argument('--list', action='store_true',
		help="Show a list of the available predefined functions with docstrings")
	group.add_argument('--quantities', action='store_true',
		help="Show a list of the available quantities in the NTuple in each file")
#	general.add_argument('-L', '--live', action='store_true',
#		help="Live plotting: directly display the plot on your local EKP machine.")
	general.add_argument('-N', '--nologo', action='store_true',
		help="Don't show the harry logo at startup")
#	general.add_argument('-w', '--www', action='store_true',
#		help="Push output plots directly to your public EKP webspace")

	opt = parser.parse_args()

	opt.fit_offset = 0
	parser.set_defaults(fit_offset=0)
	opt.subplot = False
	parser.set_defaults(subplot=False)


	# get a separate dictionary with only the user-set values
	user_options = {}
	default_options = {}
	for key in vars(opt):
		default_options[key] = parser.get_default(key)
		if vars(opt)[key] is not parser.get_default(key):
			user_options[key] = vars(opt)[key]
	opt.user_options = user_options
	opt.default_options = default_options

	opt.brackets = False

	matplotlib.rcParams.update(plotrc.getstyle(opt.layout))

	return opt


def getPath(variable='ARTUS_BASE', nofail=False):
	try:
		return os.environ[variable]
	except:
		print variable, "is not in shell variables:", os.environ.keys()
		print "Please source scripts ini_artus and CMSSW!"
		if nofail:
			return None
		exit(1)


if __name__ == "__main__":
	print "Harry Plotter - the plot wizard"

	op = options()

	if not op.nologo:
		print """\n
              *    Hocus pocus ploticus!
             / \ 
            /___\                        ______________
           ( o o )            * *       |         |data|
           )  L  (           /   * *    |       s |MC  |
   ________()(-)()________  /     * *  *|       d '----|
 E\| _____ )()()() ______ |/3     * * * |       d:     |
   |/      ()()()(       \|        * * *|      yNh     |
           | )() |                    * |      yMh     |
           /     \                     *|     :mMm/    |
          / *  *  \                     |__.-omMMMm+-__|
         /   *  *  \ 
        / *_  *  _  \ 
"""

	harrycore.plot(op)

