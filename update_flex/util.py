import argparse
import datetime
import re

from lxml import etree


def get_outfile_object(old_file_obj, tag, debug):
    new_file_name = f"{old_file_obj.stem}{tag}.lift"
    new_file_obj = old_file_obj.with_name(new_file_name)
    if debug:
        print(f"Debug: {str(new_file_obj) = }")
    return new_file_obj

def get_cawl_dict(xml_tree, cawl_type):
    cawls = dict()
    senses = xml_tree.findall('.//sense')
    for sense in senses:
        cawl = get_cawl_from_sense(sense, cawl_type)
        if cawls.get(cawl) is None:
            cawls[cawl] = [sense]
        else:
            cawls[cawl].append(sense)
    return cawls


def parse_glosses_string_to_list(glosses_string):
    d = ' '
    glosses = re.sub(r'[^a-z]+', d, glosses_string.lower()).split(d)
    glosses = list(set(glosses))
    glosses.sort()
    return glosses

def update_timestamps(sense):
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    sense.attrib['dateModified'] = timestamp
    entry = sense.getparent()
    entry.attrib['dateModified'] = timestamp

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

def get_lx_lang(xml_entry):
    lang = None
    lexical_unit = xml_entry.find('lexical-unit')
    if len(lexical_unit) > 0:
        form = lexical_unit.find('form')
        if len(form) > 0:
            lang = form.get('lang')
    return lang

def get_glosses_from_sense(lang, sense):
    glosses = []
    gloss = get_lang_lexical_unit_from_sense(sense, lang)
    if gloss is not None:
        glosses.append(gloss)
    gloss = get_lang_gloss_from_sense(sense, lang)
    if gloss is not None:
        glosses.append(gloss)
    glosses = list(set(glosses))
    glosses.sort()
    return glosses

def get_lang_lexical_unit_from_sense(sense, lang):
    text = None
    entry = sense.getparent()
    lexical_unit = entry.find('lexical-unit')
    if lexical_unit is not None:
        form = lexical_unit.find('form')
        if form.get('lang') == lang:
            text = form.find('text').text
    return text

def get_lang_gloss_from_sense(sense, lang):
    text = None
    glosses = sense.findall('gloss')
    if glosses is None:
        glosses = []
    for g in glosses:
        if g.get('lang') == lang:
            text = g.find('text').text
            break
    return text

def get_cawl_from_field(field, cawl_type):
    cawl = None
    if field.get('type') == cawl_type:
        cawl = field.find('form').find('text').text.strip()
    return cawl

def get_cawl_from_sense(sense, cawl_type):
    cawl = None
    fields = sense.findall('.//field[@type]')
    for field in fields:
        cawl = get_cawl_from_field(field, cawl_type)
        if cawl:
            break
    return cawl

def get_semantic_domain_from_sense(sense):
    value = None
    traits = sense.findall("trait")
    for trait in traits:
        if trait.get('name') == "semantic-domain-ddp4":
            value = trait.get('value')
            break
    return value

def update_gloss(lang, glosses, sense, allow_overwrite):
    """Update an existing gloss field or add a new gloss field in the self.target_xml tree."""
    gloss_exists = False
    updated = False
    for g in sense.findall('gloss'):
        if g.get('lang') == lang:
            g_lang = g.find('text')
            old_g_lang_text = g_lang.text
            gloss_exists = True
            break
    if gloss_exists:
        if allow_overwrite:
            # Update existing gloss.
            # TODO: Compare timestamps and only update if newer? Or maybe
            #   include an option "-u" to update instead of overwrite?
            g_lang.text = ' ; '.join(glosses)
            if g_lang.text != old_g_lang_text:
                updated = True
    else:
        # Create new gloss.
        gloss = etree.SubElement(sense, 'gloss')
        gloss.attrib['lang'] = lang
        gloss_text = etree.SubElement(gloss, 'text')
        gloss_text.text = ' ; '.join(glosses)
        updated = True
    if updated:
        update_timestamps(sense)

def update_semantic_domain(updated_semantic_domain, sense, allow_overwrite):
    """Update an existing semantic domain field or add a new one in the given sense."""
    semantic_domain_trait = None
    updated = False
    for t in sense.findall('trait'):
        if t.get('name') == 'semantic-domain-ddp4':
            old_semantic_domain = t.get('value')
            semantic_domain_trait = t
            break
    if semantic_domain_trait is not None and allow_overwrite:
        # Update existing semantic domain.
        # TODO: Compare timestamps and only update if newer? Or maybe
        #   include an option "-u" to update instead of overwrite?
        semantic_domain_trait.attrib['value'] = updated_semantic_domain
        if updated_semantic_domain != old_semantic_domain:
            updated = True
    else:
        # Create new semantic domain trait.
        trait = etree.SubElement(sense, 'trait')
        trait.attrib['name'] = 'semantic-domain-ddp4'
        trait.attrib['value'] = updated_semantic_domain
        updated = True
    if updated:
        update_timestamps(sense)

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
        help=argparse.SUPPRESS,
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
        '-o', '--allow-overwrite',
        help="Allow glosses in target file(s) to be overwritten. [False]",
        action='store_true',
    )
    parser.add_argument(
        '-s', '--semantic-domain',
        help="Update semantic domain info from source file to target file(s).",
        action='store_true',
    )
    return parser.parse_args()
