import argparse
import re

from lxml import etree
from pathlib import Path


def get_outfile_object(old_file_obj, lang_names, debug):
    new_file_name = f"{old_file_obj.stem}_updated-{lang_names}.lift"
    new_file_obj = old_file_obj.with_name(new_file_name)
    if debug:
        print(f"DEBUG: {str(new_file_obj) = }")
    return new_file_obj

def get_unicode(text):
    unicode = "".join(map(lambda c: rf"\u{ord(c):04x}", text))
    return unicode

def get_xml_tree(file_object):
    # Remove existing line breaks to allow pretty_print to work properly later.
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.parse(str(file_object), parser)

def print_xml_tree(xml_tree):
    print(
        etree.tostring(
            xml_tree, encoding='UTF-8', pretty_print=True, xml_declaration=True
        ).decode().rstrip()
    )

def parse_glosses_string_to_list(glosses_string):
    d = ' '
    glosses = re.sub(r'[^a-z]', d, glosses_string.lower()).split(d)
    glosses = list(set(glosses))
    glosses.sort()
    return glosses

def get_text_for_lang_and_sense(lang, sense, location):
    text = None
    if location == 'lexical-unit':
        entry = sense.getparent()
        lexical_unit = entry.find('lexical-unit')
        if lexical_unit is not None:
            form = lexical_unit.find('form')
            if form.get('lang') == lang:
                text = form.find('text').text
    elif location == 'gloss':
        glosses = sense.findall('gloss')
        if glosses is None:
            glosses = []
        for g in glosses:
            if g.get('lang') == lang:
                text = g.find('text').text
                break
    return text

def parse_cli():
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
        '-d', '--debug',
        action='store_true',
    )
    parser.add_argument(
        '-g', '--glosses',
        help="Update glosses in target file(s) with given language(s) from source file. Defaults to the language of the source file's 'lexical-unit', but this can be used to specify a language from the entry's glosses instead.",
    )
    parser.add_argument(
        '-i', '--source-id-type',
        help="The value used in the source's 'type' attribute to designate a CAWL entry. [CAWL]",
    )
    parser.add_argument(
        '-I', '--target-id-type',
        help="The value used in the target's 'type' attribute to designate a CAWL entry. [CAWL]",
    )
    parser.add_argument(
        '-s', '--semantic-domain',
        help="Update semantic domain info from source file to target file(s)",
        action='store_true',
    )
    return parser.parse_args()
