from lxml import etree
from pathlib import Path
from sys import exit
from tkinter import Tk

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
            if self.updates.get('glosses') is None and not self.updates.get('semantic-domain'):
                lx_lang = util.get_lx_lang(self.source_xml.findall('entry')[0])
                if not lx_lang:
                    print(f"ERROR: Source language not found in {self.args.source_db}")
                    exit(1)
                self.updates['glosses'] = [lx_lang]

            # Gather target files.
            self.target_files = [Path(f).resolve() for f in self.args.target_db]

            # Print debug info.
            if self.debug:
                self.print_debug_variables()

            # Process files.
            # file_list = '\n'.join([str(f) for f in self.target_files])
            # print(f"Taking \"{','.join(self.updates.get('glosses'))}\" text from lexical-units and/or glosses from \"{self.source_file}\" to update glosses in:\n{file_list}")
            for target_file in self.target_files:
                if self.debug:
                    print(f"Debug: {target_file = }")
                self.target_xml = util.get_xml_tree(target_file)
                result = self.update_file(target_file)
                if self.debug:
                    print(f"Debug: Update {result = }")

    def print_debug_variables(self):
        print(f"Debug: {self.args = }")
        print(f"Debug: {self.source_file = }")
        print(f"Debug: {self.source_cawl_type = }")
        print(f"Debug: {self.target_cawl_type = }")
        print(f"Debug: {self.updates = }")
        print(f"Debug: {self.target_files = }")

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
        if self.args.glosses:
            glosses = util.parse_glosses_string_to_list(self.args.glosses)
            self.updates['glosses'] = glosses
        # Semantic domain.
        if self.args.semantic_domain:
            self.updates['semantic-domain'] = self.args.semantic_domain

        # Target CAWL type.
        if self.args.target_id_type:
            self.target_cawl_type = self.args.target_id_type
        else:
            self.target_cawl_type = self.target_cawl_type_default

    def save_xml_to_file(self, infile_path):
        tag = '_updated'
        if self.updates.get('semantic-domain'):
            tag += '-s'
        langs = self.updates.get('glosses')
        if langs is not None:
            tag += '-' + '-'.join(langs)
        outfile = util.get_outfile_object(infile_path, tag, self.debug)
        self.target_xml.write(
            str(outfile), encoding='UTF-8', pretty_print=True, xml_declaration=True
        )
        print(f"Updated file saved as \"{outfile}\"")

    def update_file(self, target_file):
        # Gather data from source and target files.
        target_cawls_dict = util.get_cawl_dict(self.target_xml, self.target_cawl_type)
        source_cawls_dict = util.get_cawl_dict(self.source_xml, self.source_cawl_type)
        # Loop through dict for CAWL #s in target file (10x faster than looping through XML).
        for cawl, target_senses in target_cawls_dict.items():
            if cawl is None:
                continue
            source_senses = source_cawls_dict.get(cawl, [])
            if len(source_senses) == 0:
                continue
            
            # Update glosses.
            for lang in self.updates.get('glosses', []):
                source_glosses = []
                for sense in source_senses:
                    # Combine source file's lexical-unit of same lang and lang's gloss.
                    source_glosses.extend(util.get_glosses_from_sense(lang, sense))
                if len(source_glosses) > 0:
                    for sense in target_senses:
                        util.update_gloss(lang, source_glosses, sense)

            # Update semantic domain.
            if self.updates.get('semantic-domain', False):
                source_semantic_domains = []
                for sense in source_senses:
                    sd = util.get_semantic_domain_from_sense(sense)
                    if sd is not None:
                        source_semantic_domains.append(sd)
                source_semantic_domains = list(set(source_semantic_domains))
                if len(source_semantic_domains) > 0:
                    source_semantic_domains.sort()
                    for sense in target_senses:
                        sd_string = ' ; '.join(source_semantic_domains)
                        # Replace semantic domain value in target.
                        #   NOTE: Is it worth comparing with existing value before replacing?
                        #   E.g. Many files have the same SD #, but use either FR or EN text with it.
                        util.update_semantic_domain(sd_string, sense)

        # Create updated target file, preserving original.
        try:
            self.save_xml_to_file(target_file)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

def main():
    App(util.parse_cli(), className="Updateflex")
