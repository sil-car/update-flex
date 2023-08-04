#!/bin/env python3

"""
Update target LIFT file(s) with entries in source LIFT file.

Use 2 FLEx database LIFT exports:
- source.lift (LWC)
- target.lift (minority language)
- [target.lift...]
"""

import argparse

import app


def main():
    # Define arguments and options.
    parser = argparse.ArgumentParser(
        description="Show or update FLEx database files in LIFT format.",
    )
    parser.add_argument(
        "source_db",
        nargs='?',
        help="The source file to get updates from.",
    )
    parser.add_argument(
        "target_db",
        nargs='*', # require 0 or more targets
        help="The target file(s) to be shown or updated.",
    )
    parser.add_argument(
        '-l', '--lang',
        help="The language whose text will be copied from the source file(s). Defaults to the language of the 'lexical-unit', but this can be used to specify a language from the entry's glosses instead.",
    )
    parser.add_argument(
        '-s', '--source-cawl-type',
        help="The value used in the source's 'type' attribute to designate a CAWL entry. [CAWL]",
    )
    parser.add_argument(
        '-t', '--target-cawl-type',
        help="The value used in the target's 'type' attribute to designate a CAWL entry. [CAWL]",
    )
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
    )
    args = parser.parse_args()
    mainapp = app.App(args)

if __name__ == '__main__':
    main()
