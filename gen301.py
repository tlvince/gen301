#!/usr/bin/env python3
# Copyright 2011 Tom Vincent <http://tlvince.com/contact/>

"""Generate HTTP 301 redirect rules from URL lists and filenames."""

import argparse
import pprint

def parseArguments():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])

    input = parser.add_argument_group("input",
        description="Supported URL list formats.")
    input.add_argument("--gcsv", nargs="?",
        help="path to Google craw error csv file(s)")
    input.add_argument("--file", nargs="?",
        help="path to newline separated file(s)")

    output = parser.add_argument_group("output",
        description="Supported output formats.")
    formats = {"rack": "rack-rewrite 301 static redirect",
               "csv":  "comma separated"}
    output.add_argument("-o", "--output", choices=formats.keys(),
        help="an output format; one of: " + pprint.saferepr(formats))

    parser.add_argument("--dir", nargs="?",
        help="path to directory of files")

    return parser.parse_args()

def main():
    """Start execution of gen301."""
    args = parseArguments()

if __name__ == "__main__":
    main()
