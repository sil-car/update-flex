import datetime
import sys

from lxml import etree
from pathlib import Path
from sys import exit
from tkinter import Tk
from tkinter.ttk import Style

from . import gui
from . import util


class App(Tk):
    def __init__(self, cli_args, **kwargs):
        super().__init__(**kwargs)
        self.classname = kwargs.get('className')
        self.title("Update fields in FLEx LIFT file")

        self.args = cli_args

        # Define default values.
        self.source_cawl_type_default = 'CAWL'
        self.source_file_default = None
        self.source_xml_default = None
        self.target_cawl_type_default = 'CAWL'
        self.target_files_default = []
        self.target_xml_default = None
        self.updates_default = dict()

        # Set variables to defaults.
        self.reset_variables()

        # Set CAWL types according to passed args.
        self.set_user_options()

        # Run GUI if no target_db given.
        if not self.args.source_db and self.args.target_db == []:
            gui.Gui(self, class_=self.classname)
            self.mainloop()

        # Parse script arguments.
        if self.args.source_db and self.args.target_db == []:
            # Print source file XML and exit.
            self.target_file = Path(self.args.source_db)
            util.print_xml_tree(util.get_xml_tree(self.target_file))
            exit()
        elif self.args.source_db: # update target file(s)
            # Gather source file data.
            self.source_file = Path(self.args.source_db).resolve()
            self.source_xml = util.get_xml_tree(self.source_file)
            if self.updates.get('glosses') is None:
                lx_lang = self.get_lx_lang(self.source_xml.findall('entry')[0])
                if not lx_lang:
                    print(f"ERROR: Source language not found in {self.args.source_db}")
                    exit(1)
                self.updates['glosses'] = lx_lang

            # Gather target files.
            self.target_files = [Path(f).resolve() for f in self.args.target_db]

            # Print debug info.
            if self.debug:
                self.print_debug_variables()

            # Process files.
            file_list = '\n'.join([str(f) for f in self.target_files])
            print(f"Taking \"{','.join(self.updates.get('glosses'))}\" text from lexical-units and/or glosses from \"{self.source_file}\" to update glosses in:\n{file_list}")
            for target_file in self.target_files:
                if self.debug:
                    print(f"DEBUG: {target_file = }")
                self.target_xml = util.get_xml_tree(target_file)
                result = self.update_file(target_file)
                if self.debug:
                    print(f"DEBUG: Update {result = }")

    def print_debug_variables(self):
        print(f"DEBUG: {self.args = }")
        print(f"DEBUG: {self.source_file = }")
        print(f"DEBUG: {self.source_cawl_type = }")
        print(f"DEBUG: {self.target_cawl_type = }")
        # print(f"DEBUG: {self.lang = }")
        print(f"DEBUG: {self.updates = }")
        print(f"DEBUG: {self.target_files = }")

    def reset_variables(self):
        self.source_cawl_type = self.source_cawl_type_default
        self.source_file = self.source_file_default
        self.source_xml = self.source_xml_default
        self.target_cawl_type = self.target_cawl_type_default
        self.target_files = self.target_files_default
        self.target_xml = self.target_xml_default
        self.updates = self.updates_default

    def set_user_options(self):
        self.debug = True if self.args.debug else False

        # Source CAWL type.
        if self.args.source_id_type:
            self.source_cawl_type = self.args.source_id_type
        else:
            self.source_cawl_type = self.source_cawl_type_default
        # Language(s).
        # self.lang = None
        if self.args.glosses:
            glosses = util.parse_glosses_string_to_list(self.args.glosses)
            self.updates['glosses'] = glosses
            # self.lang = self.args.glosses
        # Semantic domain.
        if self.args.semantic_domain:
            self.updates['semantic-domain'] = self.args.semantic_domain

        # Target CAWL type.
        if self.args.target_id_type:
            self.target_cawl_type = self.args.target_id_type
        else:
            self.target_cawl_type = self.target_cawl_type_default

    def get_cawl_from_field(self, field, cawl_type):
        cawl = None
        if field.get('type') == cawl_type:
            cawl = field.find('form').find('text').text.strip()
        return cawl

    def get_cawls(self):
        cawls = []
        fields = self.target_xml.findall('.//field[@type]')
        for field in fields:
            cawl = self.get_cawl_from_field(field, self.target_cawl_type)
            if cawl:
                cawls.append(cawl)
        cawls = list(set(cawls))
        return cawls

    def get_glosses(self, cawl_str, lang):
        source_locations = [
            'lexical-unit',
            'gloss',
        ]
        glosses = []
        fields = self.source_xml.findall('.//field[@type]')
        for field in fields:
            cawl = self.get_cawl_from_field(field, self.source_cawl_type)
            if cawl == cawl_str:
                for loc in source_locations:
                    gloss = util.get_text_for_lang_and_sense(lang, field.getparent(), loc)
                    if gloss is not None:
                        glosses.append(gloss)
        glosses = list(set(glosses))
        glosses.sort()
        return glosses

    def update_gloss(self, cawl_str, lang, glosses):
        """Update an existing gloss field or add a new gloss field in the self.target_xml tree."""
        fields = self.target_xml.findall('.//field[@type]')
        for field in fields:
            cawl = self.get_cawl_from_field(field, self.target_cawl_type)
            if cawl == cawl_str:
                sense = field.getparent()
                gloss_exists = False
                updated = False
                for g in sense.findall('gloss'):
                    if g.get('lang') == lang:
                        g_lang = g.find('text')
                        old_g_lang_text = g_lang.text
                        gloss_exists = True
                        break
                if gloss_exists:
                    # Update existing gloss.
                    # TODO: Compare timestamps and only update if newer? Or maybe
                    #   include an option "-u" to update instead of overwrite?
                    g_lang.text = ' ; '.join(glosses)
                    if g_lang.text != old_g_lang_text:
                        if self.debug:
                            print(f"DEBUG: Updated gloss for {cawl = }")
                        updated = True
                else:
                    # Create new gloss.
                    gloss = etree.SubElement(sense, 'gloss')
                    gloss.attrib['lang'] = lang
                    gloss_text = etree.SubElement(gloss, 'text')
                    gloss_text.text = ' ; '.join(glosses)
                    if self.debug:
                        print(f"DEBUG: Created gloss for {cawl = }")
                    updated = True
                if updated:
                    self.update_timestamps(sense)

    def update_timestamps(self, sense):
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        sense.attrib['dateModified'] = timestamp
        entry = sense.getparent()
        entry.attrib['dateModified'] = timestamp

    def get_lx_lang(self, xml_entry):
        lang = None
        # lexical_unit = xml_entry.find('lexical_unit')
        lexical_unit = xml_entry.find('lexical-unit')
        if len(lexical_unit) > 0:
            form = lexical_unit.find('form')
            if len(form) > 0:
                lang = form.get('lang')
        return lang

    def save_xml_to_file(self, infile_path):
        lang_names = '-'.join(self.updates.get('glosses'))
        outfile = util.get_outfile_object(infile_path, lang_names, self.debug)
        self.target_xml.write(
            str(outfile), encoding='UTF-8', pretty_print=True, xml_declaration=True
        )
        print(f"Updated file saved as \"{outfile}\"")

    def update_file(self, target_file):
        # TODO: Right now this assumes the only update action is "glosses".
        target_cawls = self.get_cawls()
        for cawl in target_cawls:
            if not self.debug:
                print('.', end='', flush=True)
            langs = self.updates.get('glosses')
            if langs is not None:
                for lang in langs:
                    self.update_glosses(cawl, lang)

            self.update_semantic_domain(cawl)
        if not self.debug:
            print()

        # Create updated target file, preserving original.
        try:
            self.save_xml_to_file(target_file)
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False

    def update_glosses(self, cawl, lang):
        source_glosses = self.get_glosses(cawl, lang)
        if source_glosses:
            self.update_gloss(cawl, lang, source_glosses)

    def update_semantic_domain(self, cawl):
        pass

def main():
    App(util.parse_cli(), className="Updateflex")
