#!/usr/bin/env python3
import os
import subprocess
import argparse
import re
import logging

USAGE = "python3 toc_generator.py"
DESCRIPTION = """\
Generates tables of contents for markdown files in the current folder. \
Add regex patterns for files the script should ignore to the .tocignore file in the current folder.
"""
NO_GH_MD_TOC_SCRIPT_ERROR = """\
Cannot find the Github Markdown TOC bash script (./gh-md-toc). \
Download it to the current folder using the following command:
wget https://raw.githubusercontent.com/ekalinin/github-markdown-toc/master/gh-md-toc && chmod +x ./gh-md-toc
"""

IGNORE_FILE_NAME = ".tocignore"
GH_MD_TOC_FILE_NAME = "./gh-md-toc"
LVL2_HEADING_PATTERN = re.compile("(?m)^#{2}(?!#)(.*)")


def run():
    if not os.path.exists(GH_MD_TOC_FILE_NAME):
        logging.fatal(NO_GH_MD_TOC_SCRIPT_ERROR)
        return

    logging.info("Generating tables of contents...")
    filenames = get_filenames()

    if not filenames:
        logging.warning("No markdown files found!")
        return
    logging.debug("Working with files: " + str(filenames))

    for filename in filenames:
        generate_toc(filename)

    logging.info("Done!")


def generate_toc(filename):
    with open(filename, mode="r+") as file:
        content = file.read().splitlines(True)
        process = subprocess.Popen([GH_MD_TOC_FILE_NAME, '-'],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        # Pass the content of the file without the first line (root heading)
        stdout, stderr = process.communicate(input=''.join(content[1:]).encode())

        if stderr:
            logging.error("Error preparing a table of contents for the file %s: %s", filename, stderr)
            return

        toc_str = stdout.decode('unicode_escape')  # Fixes all new lines and tabs
        logging.debug("Prepared the table of contents for the file %s:\n%s", filename, toc_str)

        lvl2_heading_index = next(i for i, line in enumerate(content) if LVL2_HEADING_PATTERN.match(line))
        content_with_toc = content[0] + toc_str + os.linesep + ''.join(content[lvl2_heading_index:])

        file.seek(0)
        file.write(content_with_toc)
        file.truncate()
        logging.debug("%s file is successfully updated!", filename)


def get_filenames():
    ignore_patterns = set()
    if os.path.exists(IGNORE_FILE_NAME):
        with open(IGNORE_FILE_NAME, mode="r") as file:
            for pattern in file.readlines():
                ignore_patterns.add(re.compile(''.join(c for c in pattern if c.isprintable())))  # Printable chars only

    current_dir = os.getcwd()
    filenames = set()

    for root, directories, files in os.walk(current_dir):
        for filename in files:
            rel_filename = os.path.join(os.path.relpath(root, current_dir), filename).removeprefix("./")
            if not is_file_ignored(rel_filename, ignore_patterns):
                filenames.add(rel_filename)
    return filenames


def is_file_ignored(filename, patterns):
    if not filename.lower().endswith(".md"):
        return True

    for pattern in patterns:
        if pattern.match(filename):
            return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=USAGE,
                                     description=DESCRIPTION)
    parser.add_argument("-d", "--debug", action="store_true", help="set log level to DEBUG")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    run()
