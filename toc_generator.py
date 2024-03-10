#!/usr/bin/env python3
import argparse
import logging
import os
import re

USAGE = "python3 toc_generator.py"
DESCRIPTION = """\
Generates tables of contents for markdown files in the current folder. \
Add regex patterns for files the script should ignore to the .tocignore file in the current folder.
"""

IGNORE_FILE_NAME = ".tocignore"
LVL2_HEADING_PATTERN = re.compile("(?m)^#{2}(?!#)(.*)")


def run():
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
        content_lines = file.read().splitlines(True)

        if not content_lines[0].startswith("#"):
            logging.warning("File " + filename + " doesn't start with a header. Skipping...")
            return

        first_header_index = -1
        for i in range(1, len(content_lines)):
            if LVL2_HEADING_PATTERN.match(content_lines[i]):
                first_header_index = i
                break
            elif content_lines[i].startswith('#'):
                logging.warning(
                    "File " + filename + " has another header between lvl1 and the first lvl2 headers. Skipping...")
                return

        if first_header_index == -1:
            logging.warning("File " + filename + " doesn't have lvl2 headers. Skipping...")
            return

        toc_str = ''
        code_block = False
        for line in content_lines[1:]:

            # Marks the start and end of a code block
            if line.startswith("```"):
                if code_block:
                    code_block = False
                else:
                    code_block = True

            # Handles the header line
            elif line.startswith('#'):

                # No lvl7 headers exist
                if line.startswith('#######'):
                    continue

                # No headers can exist inside code blocks
                if code_block:
                    continue

                # Adds tabulation according to the level of the header
                for i in range(2, len(line)):
                    if line[i] == '#':
                        toc_str += '    '
                    else:
                        break

                # Adds the header's label
                line = line.lstrip('#').strip(' \n')
                toc_str += '* [' + line + ']'

                # Generates an anchor for the header
                anchor_list = list()
                last_underscore_i = -1
                to_remove = list()
                inline_code = False
                for i in range(0, len(line)):

                    # Replaces all spaces with hyphens
                    if line[i] == ' ' or line[i] == '-':
                        anchor_list.append('-')

                    # Marks a start of an inline code piece
                    elif line[i] == '`':
                        if inline_code:
                            inline_code = False
                        else:
                            inline_code = True

                    # Marks for removal an even number of underscores if outside the inline code piece
                    elif line[i] == '_':
                        if not inline_code:
                            if last_underscore_i == -1:
                                last_underscore_i = i
                                anchor_list.append('_')
                            else:
                                to_remove.append(last_underscore_i)
                                last_underscore_i = -1
                        else:
                            anchor_list.append('_')

                    # Simply adds other alphanumeric chars lowercased
                    elif line[i].isalnum():
                        anchor_list.append(line[i].lower())

                # Removes marked characters
                for i in to_remove:
                    del anchor_list[i]

                # Adds generated anchor to the table
                toc_str += '(#' + ''.join(anchor_list) + ')\n'

        logging.debug("Prepared the table of contents for the file %s:\n%s", filename, toc_str)

        # Replaces everything between lvl1 and first lvl2 headers with the table of contents
        content_with_toc = content_lines[0] + toc_str + os.linesep + ''.join(content_lines[first_header_index:])

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
