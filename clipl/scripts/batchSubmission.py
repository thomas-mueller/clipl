#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import clipl.utility.logger as logger
log = logging.getLogger(__name__)

import argparse

import clipl.utility.batchsubmission as batchsubmission


def main():
	
	parser = argparse.ArgumentParser(description="Batch submission of multiple commands.", parents=[logger.loggingParser])

	parser.add_argument("commands", help="Commands to be executed on a batch system. They can also be piped into this program.", nargs="*", default=[])
	parser.add_argument("-b", "--batch", default="rwthcondor",
	                    help="Run with grid-control and select backend. [Default: %(default)s]")

	args = parser.parse_args()
	logger.initLogger(args)
	
	batchsubmission.batch_submission(commands=args.commands, batch=args.batch)


if __name__ == "__main__":
	main()

