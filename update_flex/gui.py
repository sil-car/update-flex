from os import environ
from pathlib import Path
from threading import Thread
from tkinter import filedialog
from tkinter import IntVar
from tkinter import TclError
from tkinter.ttk import Button
from tkinter.ttk import Checkbutton
from tkinter.ttk import Entry
from tkinter.ttk import Frame
from tkinter.ttk import Label
from tkinter.ttk import Separator
from tkinter.ttk import Style

from . import util

class Gui(Frame):
    # Original window.
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)

        # Set theme.
        s = Style()
        s.theme_use('alt') # alt, clam, classic, default

        # Configure frame.
        self.config(padding="9 9 9 9")
        self.grid(column=0, row=0, sticky='NWES')
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.app = app
        self.source_label = "Choose source..."
        self.target_label = "Choose target..."

        pad = 4
        pady = 4

        ### Build window.
        # Row 0: Create ID Label.
        c_label = Label(self, text="ID type")
        c_label.grid(column=2, row=0, padx=pad, pady=pady, sticky='W')

        # Row 1: Create Source Label.
        s_label = Label(self, text="Source:")
        s_label.grid(column=0, row=1, padx=pad, pady=pady, sticky='W')
        # Row 1: Create Source Button.
        self.source_btn = Button(self, padding=pad, text=self.source_label)
        self.source_btn.grid(column=1, row=1, padx=pad, pady=pady, sticky='W')
        self.source_btn.bind("<ButtonRelease>", self.get_source_file)
        # Row 1: Create Source ID Entry.
        self.source_ent = Entry(self)
        self.source_ent.insert('end', self.app.source_cawl_type)
        self.source_ent.grid(column=2, row=1, padx=pad, pady=pady, sticky='W')
        self.source_ent.bind("<FocusOut>", self.on_source_ent_focusout)
        self.source_ent.bind("<Control-a>", self.ctrl_a)

        # Row 2: Create Target Label.
        t_label = Label(self, text="Target:")
        t_label.grid(column=0, row=2, padx=pad, pady=pady, sticky='W')
        # Row 2: Create Target Button.
        self.target_btn = Button(self, padding=pad, text=self.target_label)
        self.target_btn.grid(column=1, row=2, padx=pad, pady=pady, sticky='W')
        self.target_btn.bind("<ButtonRelease>", self.get_target_file)
        # Row 2: Create Target ID Entry.
        self.target_ent = Entry(self)
        self.target_ent.insert('end', self.app.target_cawl_type)
        self.target_ent.grid(column=2, row=2, padx=pad, pady=pady, sticky='w')
        self.target_ent.bind("<FocusOut>", self.on_target_ent_focusout)
        self.target_ent.bind("<Control-a>", self.ctrl_a)

        # Row 3: Add Separator.
        sep = Separator(self, orient='horizontal')
        sep.grid(row=3, columnspan=3, pady=pady*4, sticky='ew')

        # Row 4: Create Languages Label.
        l_label = Label(self, text="Language Code(s)")
        l_label.grid(column=1, row=4, padx=pad, pady=0, sticky='W')
        # Row 4: Create Fields Label.
        f_label = Label(self, text="Fields to update")
        f_label.grid(column=0, row=4, padx=pad, pady=pady, sticky='W')

        # Row 5: Create Glosses Checkbox.
        self.g_selected = IntVar()
        self.g_chbox = Checkbutton(self, text="Gloss(es)", variable=self.g_selected)
        self.g_chbox.grid(column=0, row=5, padx=pad, pady=pady, sticky='W')
        # Row 5: Create Source Language ISO Entry.
        self.lang_ent = Entry(self)
        self.lang_ent.grid(column=1, row=5, padx=pad, pady=pady, sticky='W')
        self.lang_ent.bind("<FocusOut>", self.on_lang_ent_focusout)
        self.lang_ent.bind("<Control-a>", self.ctrl_a)
        # Row 5: Create Overwrite Checkbox.
        self.o_selected = IntVar()
        self.o_chbox = Checkbutton(self, text="Allow overwriting?", variable=self.o_selected)
        self.o_chbox.grid(column=2, row=5, padx=pad, pady=pady, sticky='W')

        # Row 6: Create SematicDomain Checkbox.
        self.s_selected = IntVar()
        self.s_chbox = Checkbutton(self, text="Semantic Domain", variable=self.s_selected)
        self.s_chbox.grid(column=0, row=6, padx=pad, pady=pady, sticky='W')

        # Row 7: Create Update Button.
        self.update_btn = Button(
            self, padding=pad, text="Update LIFT File", state='disabled'
        )
        self.update_btn.grid(column=0, row=7, padx=pad, pady=pady, sticky='W')
        self.update_btn.bind("<ButtonRelease>", self.on_update_btn_release)
        # Row 7: Create Reset Button.
        self.reset_btn = Button(self, padding=pad, text="Reset")
        self.reset_btn.grid(column=1, row=7, padx=pad, pady=pady, sticky='W')
        self.reset_btn.bind("<ButtonRelease>", self.reset_widgets)
        # Row 7: Create Status Label.
        self.status_lab = Label(self, text="")
        self.status_lab.grid(column=3, row=7, columnspan=2, padx=pad, pady=pady, sticky='W')

        # Set initial state of widgets.
        self.reset_widgets('RESET')

    def select_all(self, widget):
        # Select text.
        widget.select_range(0, 'end')
        # Move cursor to the end.
        widget.icursor('end')

    def ctrl_a(self, event):
        # Pause 50ms, then select-all.
        self.after(50, self.select_all, event.widget)

    def on_source_ent_focusout(self, event):
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_lang_ent_focusout(self, event):
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_target_ent_focusout(self, event):
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_update_btn_release(self, event):
        # Verify source and target files.
        if self.app.source_file is None and len(self.app.target_files) != 1:
            # Ignore button press: should be disabled, but callback is still called.
            return

        # Get CAWL types.
        source_cawl = self.source_ent.get()
        if source_cawl is not None:
            self.app.source_cawl_type = source_cawl
        target_cawl = self.target_ent.get()
        if target_cawl is not None:
            self.app.target_cawl_type = target_cawl

        # Read checkbox states.
        if self.g_selected.get() == 1:
            self.app.updates['glosses'] = util.parse_glosses_string_to_list(self.lang_ent.get())
        if self.s_selected.get() == 1:
            self.app.updates['semantic-domain'] = True
        if self.o_selected.get() == 1:
            self.app.updates['allow-overwrite'] = True

        # Disable all Widgets.
        for f in self.winfo_children():
            try:
                f['state'] = 'disabled'
            except TclError:
                pass
            for w in f.winfo_children():
                w['state'] = 'disabled'
        self.update_btn.configure(text="Updating...")
        if self.app.debug:
            self.app.print_debug_variables()

        # Start update in own thread.
        t_update = Thread(target=self.update_file)
        t_update.start()

    def get_source_file(self, event):
        selected_file = filedialog.askopenfilename(
            title=self.source_label,
            initialdir=environ.get('SNAP_REAL_HOME', Path.home()),
            filetypes=[('LIFT', '.lift')],
        )
        if selected_file:
            event.widget['text'] = Path(selected_file).name
            self.app.source_file = Path(selected_file)
            self.app.source_xml = util.get_xml_tree(self.app.source_file)
        self.verify_update_btn_state()

    def get_target_file(self, event):
        selected_file = filedialog.askopenfilename(
            title=self.target_label,
            filetypes=[('LIFT', '.lift')],
        )
        if selected_file:
            event.widget['text'] = Path(selected_file).name
            self.app.target_files = [Path(selected_file)]
            self.app.target_xml = util.get_xml_tree(self.app.target_files[0])
        self.verify_update_btn_state()

    def update_file(self):
        result = self.app.update_file(self.app.target_files[0])
        if not result:
            self.status_lab['text'] = f"Update failed for {self.app.target_files[0]}"
        self.reset_widgets('RESET')

    def verify_update_btn_state(self):
        if len(self.app.target_files) > 0 and self.app.source_file is not None:
            self.update_btn['state'] = 'normal'
        else:
            self.update_btn['state'] = 'disabled'

    def reset_widgets(self, event):
        # Reset variables.
        self.reset_variables()

        # Re-enable all widgets.
        for f in self.winfo_children():
            try:
                f['state'] = 'normal'
            except TclError:
                pass
            for w in f.winfo_children():
                w['state'] = 'normal'

        # Reset widgets.
        self.source_btn['text'] = self.source_label
        self.source_ent.delete(0, len(self.source_ent.get()))
        self.source_ent.insert('end', self.app.source_cawl_type)

        self.target_btn['text'] = self.target_label
        self.target_ent.delete(0, len(self.target_ent.get()))
        self.target_ent.insert('end', self.app.target_cawl_type)

        if self.g_selected.get() == 1:
            self.g_chbox.invoke()
            self.g_selected.set(0)
        self.lang_ent.delete(0, len(self.lang_ent.get()))
        if self.s_selected.get() == 1:
            self.s_chbox.invoke()
            self.s_selected.set(0)
        if self.o_selected.get() == 1:
            self.o_chbox.invoke()
            self.o_selected.set(0)
        self.update_btn['text'] = "Update LIFT file"
        self.update_btn['state'] = 'disabled'
        self.status_lab['text'] = ''

    def reset_variables(self):
        self.app.reset_variables()
        self.app.set_user_options()
