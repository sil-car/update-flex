import argparse
import datetime
import importlib.metadata
import re

from lxml import etree
from pathlib import Path


def get_version_string():
    version_string = 'unknown'
    try:
        version_string = importlib.metadata.version('update-flex')
    except importlib.metadata.PackageNotFoundError:
        # Running as script rather than installed package.
        toml_file = Path(__file__).parents[1] / 'pyproject.toml'
        with toml_file.open() as f:
            lines = f.readlines()
        for line in lines:
            if line[:7] == 'version':
                version_string = line.split('=')[1].strip().strip('"')
            if version_string != 'unknown':
                break
    return version_string

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
    glosses = normalize_list(glosses)
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

def xml_tree_to_string(xml_tree):
    xml_string = etree.tostring(
        xml_tree, encoding='UTF-8', pretty_print=True, xml_declaration=True
    ).decode().rstrip()
    return xml_string

def get_lx_lang(xml_entry):
    lang = None
    lexical_unit = xml_entry.find('lexical-unit')
    if len(lexical_unit) > 0:
        form = lexical_unit.find('form')
        if len(form) > 0:
            lang = form.get('lang')
    return lang

def get_glosses_from_sense(lang, sense):
    glosses_raw = []
    if lang == 'sg': # get lexical-unit text if Source is in Sango
        gloss = get_lang_lexical_unit_from_sense(sense, lang)
        if gloss is not None:
            glosses_raw.append(gloss)
    gloss = get_lang_gloss_from_sense(sense, lang)
    if gloss is not None:
        glosses_raw.append(gloss)
    glosses_raw = normalize_list(glosses_raw)

    # Consolidate repeated terms in glosses.
    glosses = []
    for g_raw in glosses_raw:
        gs = g_raw.split(';')
        gs = list(set([g.strip() for g in gs]))
        glosses.extend(gs)
    glosses = normalize_list(glosses)

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
            text = g.find('text').text # returns first matching gloss
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

def get_semantic_domains_from_sense(sense):
    semantic_domains_raw = []
    traits = sense.findall("trait")
    for trait in traits:
        if trait.get('name') == "semantic-domain-ddp4":
            sd = trait.get('value')
            if sd is not None:
                semantic_domains_raw.append(sd)
    semantic_domains_raw = normalize_list(semantic_domains_raw)

    # Consolidate repeated terms.
    semantic_domains = []
    for sd_raw in semantic_domains_raw:
        sds = sd_raw.split(';')
        sds = list(set([sd.strip() for sd in sds]))
        semantic_domains.extend(sds)
    semantic_domains = normalize_list(semantic_domains)

    return semantic_domains

def update_gloss(lang, glosses, sense, allow_overwrite):
    """Update an existing gloss field or add a new gloss field in the self.target_xml tree."""
    gloss_exists = False
    updated = False
    glosses_text = ' ; '.join(glosses)
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
            g_lang.text = glosses_text
            if g_lang.text != old_g_lang_text:
                updated = True
    else:
        # Create new gloss.
        gloss = etree.SubElement(sense, 'gloss')
        gloss.attrib['lang'] = lang
        gloss_text = etree.SubElement(gloss, 'text')
        gloss_text.text = glosses_text
        updated = True
    if updated:
        update_timestamps(sense)

def update_semantic_domain(semantic_domains, sense, allow_overwrite):
    """Update an existing semantic domain field or add a new one in the given sense."""
    semantic_domain_trait = None
    updated = False
    sd_trait_text = ' ; '.join(semantic_domains)
    for t in sense.findall('trait'):
        if t.get('name') == 'semantic-domain-ddp4':
            old_semantic_domain = t.get('value')
            semantic_domain_trait = t
            break
    if semantic_domain_trait is not None:
        if allow_overwrite:
            # Update existing semantic domain.
            # TODO: Compare timestamps and only update if newer? Or maybe
            #   include an option "-u" to update instead of overwrite?
            semantic_domain_trait.attrib['value'] = sd_trait_text
            if semantic_domain_trait.attrib['value'] != old_semantic_domain:
                updated = True
    else:
        # Create new semantic domain trait.
        trait = etree.SubElement(sense, 'trait')
        trait.attrib['name'] = 'semantic-domain-ddp4'
        trait.attrib['value'] = sd_trait_text
        updated = True
    if updated:
        update_timestamps(sense)

def dedupe_glosses(lang, sense):
    # Gather all existing glosses.
    glosses_texts = []
    all_glosses = sense.findall('gloss')
    for gloss in all_glosses:
        if gloss.get('lang') == lang:
            gloss_elem = gloss.find('text')
            glosses_texts.append(gloss_elem.text)
    glosses_texts = normalize_list(glosses_texts)

    # Consolidate into a single updated string.
    glosses = []
    for glosses_text in glosses_texts:
        gs = glosses_text.split(';')
        gs = normalize_list(gs)
        glosses.extend(gs)
    glosses = normalize_list(glosses)
    updated_glosses_text = ' ; '.join(glosses)

    # Update 1st instance & remove all others.
    updated = False
    for gloss in all_glosses:
        if gloss.get('lang') == lang:
            if not updated:
                g_elem = gloss.find('text')
                if g_elem.text != updated_glosses_text:
                    g_elem.text = updated_glosses_text
                updated = True
            else:
                print(f"removed gloss {gloss}")
                sense.remove(gloss)

def dedupe_semantic_domains(sense):
    # Gather all existing semantic domain info.
    sd_texts = []
    traits = sense.findall('trait')
    for trait in traits:
        if trait.get('name') == 'semantic-domain-ddp4':
            sd_texts.append(trait.get('value'))
    sd_texts = normalize_list(sd_texts)

    # Consolidate into a single updated string.
    semantic_domains = []
    for sd_text in sd_texts:
        sds = sd_text.split(';')
        sds = normalize_list(sds)
        semantic_domains.extend(sds)
    semantic_domains = normalize_list(semantic_domains)
    updated_sd_text = ' ; '.join(semantic_domains)

    # Update 1st instance & remove all others.
    updated = False
    for trait in traits:
        if trait.get('name') == 'semantic-domain-ddp4':
            if not updated:
                if trait.get('value') != updated_sd_text:
                    trait.attrib['value'] = updated_sd_text
                updated = True
            else:
                print(f"removed trait {trait}")
                sense.remove(trait)


def normalize_list(mylist):
    # Strip whitespace.
    mylist = [t.strip() for t in mylist]
    # Deduplicate items.
    mylist = list(set(mylist))
    # Sort alphabetically.
    mylist.sort()
    return mylist

def parse_cli():
    # Define arguments and options.
    parser = argparse.ArgumentParser(
        description="show or update FLEx database files in LIFT format",
    )
    parser.add_argument(
        "source_db",
        nargs='?',
        help="the source file to get updates from",
    )
    parser.add_argument(
        "target_db",
        nargs='*', # require 0 or more targets
        help="the target file(s) to be shown or updated",
    )
    parser.add_argument(
        '-d', '--debug',
        help=argparse.SUPPRESS,
        action='store_true',
    )
    parser.add_argument(
        '-g', '--glosses',
        help="update glosses in target file(s) with given language(s) from source file; defaults to the language of the source file's 'lexical-unit', but this can be used to specify a language from the entry's glosses instead",
    )
    parser.add_argument(
        '-i', '--source-id-type',
        help="the value used in the source's 'type' attribute to designate a CAWL entry [CAWL]",
    )
    parser.add_argument(
        '-I', '--target-id-type',
        help="the value used in the target's 'type' attribute to designate a CAWL entry [CAWL]",
    )
    parser.add_argument(
        '-o', '--allow-overwrite',
        help="allow glosses in target file(s) to be overwritten [False]",
        action='store_true',
    )
    parser.add_argument(
        '-s', '--semantic-domain',
        help="update semantic domain info from source file to target file(s)",
        action='store_true',
    )
    parser.add_argument(
        '-V', '--version',
        help="show app version",
        action='store_true',
    )
    return parser.parse_args()
