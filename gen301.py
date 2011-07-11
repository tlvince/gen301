#!/usr/bin/env python3
# Copyright 2011 Tom Vincent <http://tlvince.com/contact/>

"""Generate HTTP 301 redirect rules from URL lists and filenames."""

import argparse
import pprint
import os
import logging
import difflib

from urllib.parse import urlparse

def parseArguments():
    """Parse the command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])

    input = parser.add_argument_group("input",
        description="Supported URL list formats.")
    input.add_argument("-g", "--gcsv", nargs="?",
        help="path to Google crawl error csv file(s)")
    input.add_argument("-p", "--plain", nargs="?",
        help="path to newline separated file(s)")

    output = parser.add_argument_group("output",
        description="Supported output formats.")
    formats = {"rack": "rack-rewrite 301 static redirect",
               "csv":  "comma separated"}
    output.add_argument("-o", "--output", choices=formats.keys(), default="csv",
        help="an output format; one of: " + pprint.saferepr(formats))
    output.add_argument("-e", "--ext", action="store_true",
        help="remove file extension in redirects")
    output.add_argument("-s", "--subdomain", action="store_true",
        help="remove subdomains in redirects")

    files = parser.add_argument_group("files",
        description="Heuristics regarding filename format.")
    files.add_argument("-u", "--utc", action="store_true",
        help="filenames start with a date in UTC format")

    search = parser.add_argument_group("search",
        description="Fuzzy search parameters.")
    search.add_argument("-c", "--cutoff", default=0.32, type=float,
        help="fuzzy search threshold (float, defaults to: 0.32)")
    search.add_argument("-m", "--matches", default=1, type=int,
        help="number of fuzzy search matches (int, defaults to: 1)")

    parser.add_argument("-d", "--dirs", nargs="?", default=".",
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

def fuzzySearch(urls, files, n, cutoff):
    """Return a mapping of filenames that approximately match URLs."""
    mapping = {}
    for url in urls:
        matches = difflib.get_close_matches(url, files, n, cutoff)
        if matches:
            mapping[url] = matches
    return mapping

class OutputFormat:
    """Base class for supported outputs."""
    def __init__(self, redirects, subdomain):
        """Constructor."""
        self.redirects = redirects
        self.subdomain = subdomain
    def __repr__(self):
        """Return a machine-readable output of the redirects."""
        return pprint.saferepr(self.redirects)
    def __str__(self):
        """Pretty print redirects."""
        return pprint.pformat(self.redirects)

class CSV(OutputFormat):
    def __str__(self):
        """Print redirects in a commar separated format."""
        lines = []
        for url in self.redirects.keys():
            for match in self.redirects[url]:
                parsed = urlparse(url)
                netloc = parsed.netloc
                if self.subdomain:
                    netloc = netloc[(netloc.find(".")+1):]
                prefix = "{0}://{1}".format(parsed.scheme, netloc)
                lines.append("{0}, {1}/{2}".format(url, prefix, match))
        return "\n".join([line for line in lines])

def formatFiles(path, utc, ext):
    """Return a list of files in the given path, with optional formatting."""
    files = os.listdir(path)
    if utc:
        # Subsitute dashes for slashes a leading UTC date:
        #   YYYY-MM-DD- => YYYY/MM/DD/
        for index, value in enumerate(files):
            files[index] = value[:11].replace("-", "/") + value[11:]
    if ext:
        # Substitute the file extension with a slash
        #   file.mkd    => file/
        for index, value in enumerate(files):
            name, ext = os.path.splitext(value)
            files[index] = name + "/"
    return files

def main():
    """Start execution of gen301."""
    inputs = []
    files = set()

    args = parseArguments()

     # Configure the stdout logger
    logging.basicConfig(format="%(filename)s: %(levelname)s: %(message)s",
        level=logging.DEBUG)

    try:
        # Create a list of input format objects
        for gcsv in args.gcsv.split():
            inputs.append(GoogleCSV(gcsv))
        for plain in args.plain.split():
            inputs.append(Plain(plain))

        # Get the URLs
        urls = mergeURLS(inputs)

        # Get the files
        for dir in args.dirs.split():
            files = files.union(formatFiles(dir, args.utc, args.ext))

        # Search for matches
        redirects = fuzzySearch(urls, files, args.matches, args.cutoff)

    except Exception as e:
        logging.error(e)

    if args.output is "csv":
        out = CSV(redirects, args.subdomain)
    elif args.output is "rack":
        out = Rack(redirect, args.subdomain)
    else:
        out = OutputFormat(redirects, args.subdomain)

    print(out)

if __name__ == "__main__":
    main()
