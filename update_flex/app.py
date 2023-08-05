from lxml import etree
from pathlib import Path
from sys import exit
from tkinter import Tk

from . import gui
from . import util

# from multiprocessing import Pool
# import copyreg
# from io import BytesIO

# def element_unpickler(data):
#     return etree.fromstring(data)

# def element_pickler(element):
#     return element_unpickler, (etree.tostring(element),)

# copyreg.pickle(etree._Element, element_pickler, element_unpickler)

# def elementtree_unpickler(data):
#     return etree.parse(BytesIO(data))

# def elementtree_pickler(tree):
#     return elementtree_unpickler, (etree.tostring(tree),)

# copyreg.pickle(etree._ElementTree, elementtree_pickler, elementtree_unpickler)


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

    def update_gloss(self, lang, glosses, sense):
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
            # Update existing gloss.
            # TODO: Compare timestamps and only update if newer? Or maybe
            #   include an option "-u" to update instead of overwrite?
            g_lang.text = ' ; '.join(glosses)
            if g_lang.text != old_g_lang_text:
                if self.debug:
                    cawl = util.get_cawl_from_sense(sense, self.target_cawl_type)
                    print(f"Debug: Updated gloss for {cawl = }")
                updated = True
        else:
            # Create new gloss.
            gloss = etree.SubElement(sense, 'gloss')
            gloss.attrib['lang'] = lang
            gloss_text = etree.SubElement(gloss, 'text')
            gloss_text.text = ' ; '.join(glosses)
            if self.debug:
                cawl = util.get_cawl_from_sense(sense, self.target_cawl_type)
                print(f"Debug: Created gloss for {cawl = }")
            updated = True
        if updated:
            util.update_timestamps(sense)

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
        target_cawls = util.get_cawls_from_xml(self.target_cawl_type, self.target_xml)
        for cawl in target_cawls:
            # NOTE: Multiprocessing at "sense" level breaks the ability to find the sense's
            #   parent, i.e. the corresponding "entry".
            # with Pool(2) as p:
            #     source_sense, target_sense = p.starmap(
            #         util.get_sense_from_cawl, [
            #             (cawl, self.source_cawl_type, self.source_xml),
            #             (cawl, self.target_cawl_type, self.target_xml),
            #             ]
            #         )
            source_sense = util.get_sense_from_cawl(cawl, self.source_cawl_type, self.source_xml)
            if source_sense is None:
                # This sense/CAWL # doesn't exist in the source file.
                if self.debug:
                    print(f"Debug: No source sense found for {self.source_cawl_type} = {cawl}")
                continue
            target_sense = util.get_sense_from_cawl(cawl, self.target_cawl_type, self.target_xml)
            if not self.debug:
                print('.', end='', flush=True)

            # Update glosses.
            for lang in self.updates.get('glosses', []):
                source_glosses = util.get_glosses_from_sense(lang, source_sense)
                if source_glosses:
                    self.update_gloss(lang, source_glosses, target_sense)

            # Update semantic domain.
            if self.updates.get('semantic-domain', False):
                source_semantic_domain = util.get_semantic_domain_from_sense(source_sense)
                if source_semantic_domain:
                    util.update_semantic_domain(source_semantic_domain, target_sense)

        if not self.debug:
            print()

        # Create updated target file, preserving original.
        try:
            self.save_xml_to_file(target_file)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

def main():
    App(util.parse_cli(), className="Updateflex")
