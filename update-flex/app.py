import datetime

from lxml import etree
from pathlib import Path
from sys import exit

import util


class App():
    def __init__(self, cli_args):
        self.args = cli_args
        self.debug = True if self.args.debug else False

        self.source_file = None
        self.source_cawl_type_default = 'CAWL'
        self.source_xml = None

        self.target_file = None
        self.target_cawl_type_default = 'CAWL'
        self.target_xml = None

        self.lang_default = 'sg'
        self.lang = self.lang_default

        # Verify virtual environment.
        util.verify_venv(self.debug)

        # Set CAWL types according to passed args.
        self.set_user_options()

        # Run GUI if no target_db given.
        if self.debug:
            print(f"DEBUG: {self.args = }")
        if not self.args.source_db and self.args.target_db == []:
            import gui
            maingui = gui.Gui(self)
            exit()

        # Parse script arguments.
        if self.args.source_db and self.args.target_db == []:
            self.target_file = Path(self.args.source_db)
            self.target_xml = self.get_xml_tree(self.target_file)
            print(
                etree.tostring(
                    self.target_xml, encoding='UTF-8', pretty_print=True, xml_declaration=True
                ).decode().rstrip()
            )
            exit()
        elif self.args.source_db: # update target file(s)
            # Set 'type' attribute for CAWL entries.
            if self.debug:
                print(f"DEBUG: {self.source_cawl_type = }")
                print(f"DEBUG: {self.target_cawl_type = }")

            # Gather source file data.
            self.source_file = Path(self.args.source_db).resolve()
            self.source_xml = self.get_xml_tree(self.source_file)
            if self.args.lang:
                self.lang = self.args.lang
                if self.debug:
                    print(f"DEBUG: from args: {self.lang = }")
            else:
                self.lang = self.get_lx_lang(self.source_xml.findall('entry')[0])
                if self.debug:
                    print(f"DEBUG: from source file: {self.lang = }")
                if not self.lang:
                    print(f"ERROR: Source language not found in {self.args.source_db}")
                    exit(1)

            # Gather target files.
            target_files = [Path(f).resolve() for f in self.args.target_db]
            if self.debug:
                print(f"DEBUG: {target_files = }")

            # Process files.
            file_list = '\n'.join([str(f) for f in target_files])
            print(f"Taking \"{self.lang}\" text from lexical-units and/or glosses from \"{self.source_file}\" to update glosses in:\n{file_list}")
            for target_file in target_files:
                if self.debug:
                    print(f"DEBUG: {target_file = }")
                self.target_xml = self.get_xml_tree(target_file)
                result = self.update_file(target_file)
                if self.debug:
                    print(f"DEBUG: Update {result = }")

    def set_user_options(self):
        # Source CAWL type.
        if self.args.source_cawl_type:
            self.source_cawl_type = self.args.source_cawl_type
        else:
            self.source_cawl_type = self.source_cawl_type_default
        # Language.
        if self.args.lang:
            self.lang = self.args.lang
        else:
            self.lang = self.lang_default
        # Target CAWL type.
        if self.args.target_cawl_type:
            self.target_cawl_type = self.args.target_cawl_type
        else:
            self.target_cawl_type = self.target_cawl_type_default

    def get_xml_tree(self, file_object):
        # Remove existing line breaks to allow pretty_print to work properly later.
        if self.debug:
            print(f"DEBUG: {file_object = }")
        parser = etree.XMLParser(remove_blank_text=True)
        return etree.parse(str(file_object), parser)

    def get_text_for_lang_and_sense(self, sense, location):
        text = None
        if location == 'lexical-unit':
            entry = sense.getparent()
            lexical_unit = entry.find('lexical-unit')
            if lexical_unit is not None:
                form = lexical_unit.find('form')
                if form.get('lang') == self.lang:
                    text = form.find('text').text
        elif location == 'gloss':
            glosses = sense.findall('gloss')
            if glosses is None:
                glosses = []
            for g in glosses:
                if g.get('lang') == self.lang:
                    text = g.find('text').text
                    break
        return text

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

    def get_glosses(self, cawl_str):
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
                    gloss = self.get_text_for_lang_and_sense(field.getparent(), loc)
                    if gloss is not None:
                        glosses.append(gloss)
        glosses = list(set(glosses))
        glosses.sort()
        return glosses

    def update_gloss(self, cawl_str, glosses):
        """Update an existing gloss field or add a new gloss field in the self.target_xml tree."""
        fields = self.target_xml.findall('.//field[@type]')
        for field in fields:
            cawl = self.get_cawl_from_field(field, self.target_cawl_type)
            if cawl == cawl_str:
                sense = field.getparent()
                gloss_exists = False
                updated = False
                for g in sense.findall('gloss'):
                    if g.get('lang') == self.lang:
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
                    gloss.attrib['lang'] = self.lang
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
        outfile = util.get_outfile_object(infile_path, self.lang, self.debug)
        self.target_xml.write(
            str(outfile), encoding='UTF-8', pretty_print=True, xml_declaration=True
        )
        print(f"Updated file saved as \"{outfile}\"")

    def update_file(self, target_file):
        target_cawls = self.get_cawls()
        for cawl in target_cawls:
            if self.debug:
                pass
            #     print(f"DEBUG: {cawl = }")
            else:
                print('.', end='', flush=True)
            source_glosses = self.get_glosses(cawl)
            if source_glosses:
                # if self.debug:
                #     print(f"DEBUG: {source_glosses = }")
                self.update_gloss(cawl, source_glosses)
        if not self.debug:
            print()

        # Create updated target file, preserving original.
        try:
            self.save_xml_to_file(target_file)
            return True
        except Exception as e:
            print(f"ERROR: {e}")
            return False
