#!/usr/bin/env python3
# Copyright 2011 Tom Vincent <http://tlvince.com/contact/>

"""Generate HTTP 301 redirect rules from URL lists and filenames."""

import argparse
import pprint
import os
import logging
import difflib

def parseArguments():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])

    input = parser.add_argument_group("input",
        description="Supported URL list formats.")
    input.add_argument("--gcsv", nargs="?",
        help="path to Google craw error csv file(s)")
    input.add_argument("--plain", nargs="?",
        help="path to newline separated file(s)")

    output = parser.add_argument_group("output",
        description="Supported output formats.")
    formats = {"rack": "rack-rewrite 301 static redirect",
               "csv":  "comma separated"}
    output.add_argument("-o", "--output", choices=formats.keys(), default="csv",
        help="an output format; one of: " + pprint.saferepr(formats))

    parser.add_argument("--dirs", nargs="?", default=".",
        help="path to directory(s) of files")

    return parser.parse_args()

class InputFormat:
    """Base class for supported inputs."""
    def __init__(self, path):
        """Constructor for objects of class InputFormat."""
        self.path = path
    def read(self):
        """Return the contents of the given file."""
        path = os.path.expanduser(self.path)
        with open(path, encoding="utf-8") as f:
            return f.read().splitlines()
    def urls(self):
        return set(self.read())

class Plain(InputFormat):
    """Plain text format."""
    pass

class GoogleCSV(InputFormat):
    """Google CSV input format."""
    def urls(self):
        """Return a set of URLs from a Google crawl error CSV file."""
        header = "URL,Linked From,Discovery Date"
        gcsv = self.read()
        if gcsv[0] != header:
            raise Exception("Unexpected CSV format")
        urls = set()
        for line in gcsv[1:]:
            # Get everything before the first commar (just the URL)
            line = line[:line.find(",")]
            urls.add(line)
        return urls

def mergeURLS(inputs):
    """Create a unique set of URLs from the given input formats."""
    urls = set()
    for i in inputs:
        # Re-raise any exceptions
        try:
            urls = urls.union(i.urls())
        except:
            raise
    return urls

def fuzzySearch(urls, files, threshold=0.32):
    """Return a mapping of filenames that approximately match URLs."""
    mapping = {}
    for url in urls:
        matches = difflib.get_close_matches(url, files, 5, threshold)
        if matches:
            mapping[url] = matches
    return mapping

def main():
    """Start execution of gen301."""
    inputs = []
    files = set()

    args = parseArguments()

     # Configure the stdout logger
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s",
        level=logging.DEBUG)

    # Create a list of input format objects
    for gcsv in args.gcsv.split():
        inputs.append(GoogleCSV(gcsv))
    for plain in args.plain.split():
        inputs.append(Plain(plain))

    try:
        urls = mergeURLS(inputs)
        for dir in args.dirs.split():
            files = files.union(set(os.listdir(dir)))
    except Exception as e:
        logging.error(e)

    redirects = fuzzySearch(urls, files)

if __name__ == "__main__":
    main()
