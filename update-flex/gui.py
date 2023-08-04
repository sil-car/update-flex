import tkinter as tk

from pathlib import Path
from threading import Thread
from tkinter import filedialog
from tkinter import ttk


class Gui():
    def __init__(self, app):
        self.app = app
        self.source_label = "Choose source LIFT file..."
        self.target_label = "Choose LIFT file to update..."
        self.window = self.create_window()
        self.window.mainloop()

        # Identify future widgets.
        self.source_btn = None
        self.source_ent = None
        self.lang_ent = None
        self.target_btn = None
        self.target_ent = None
        self.reset_btn = None
        self.update_btn = None
        self.status_lab = None

    def select_all(self, widget):
        # Select text.
        widget.select_range(0, 'end')
        # Move cursor to the end.
        widget.icursor('end')

    def ctrl_a(self, event):
        # Pause 50ms, then select-all.
        self.window.after(50, self.select_all, event.widget)

    def on_source_ent_focusout(self, event):
        source_cawl = event.widget.get()
        if source_cawl is not None:
            self.app.source_cawl_type = source_cawl
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_lang_ent_focusout(self, event):
        lang = event.widget.get()
        if lang is not None:
            self.app.lang = lang
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_target_ent_focusout(self, event):
        target_cawl = event.widget.get()
        if target_cawl is not None:
            self.app.target_cawl_type = target_cawl
        # Ensure no text is selected.
        event.widget.select_range(0, 0)

    def on_update_btn_release(self, event):
        # Disable all Widgets.
        for f in self.window.winfo_children():
            for w in f.winfo_children():
                w.configure(state=tk.DISABLED)
        self.update_btn.configure(text="Updating...")
        # Start update in own thread.
        t_update = Thread(target=self.update_file)
        t_update.start()

    def get_source_file(self, event):
        selected_file = filedialog.askopenfilename(
            title=self.source_label,
            initialdir=Path.home(),
            filetypes=[('LIFT', '.lift')],
        )
        if selected_file:
            event.widget.configure(text=selected_file)
            self.app.source_file = Path(selected_file)
        self.verify_update_btn_state()

    def get_target_file(self, event):
        selected_file = filedialog.askopenfilename(
            title=self.target_label,
            initialdir=Path.home(),
            filetypes=[('LIFT', '.lift')],
        )
        if selected_file:
            event.widget.configure(text=selected_file)
            self.app.target_file = Path(selected_file)
        self.verify_update_btn_state()

    def update_file(self):
        self.app.source_xml = self.app.get_xml_tree(self.app.source_file)
        self.app.target_xml = self.app.get_xml_tree(self.app.target_file)
        result = self.app.update_file(self.app.target_file)
        if not result:
            self.status_lab.configure(text=f"Update failed for {self.app.target_file}")
        self.reset_widgets('RESET')

    def verify_update_btn_state(self):
        if self.app.target_file is not None and self.app.source_file is not None:
            self.update_btn.configure(state=tk.NORMAL)
        else:
            self.update_btn.configure(state=tk.DISABLED)

    def reset_widgets(self, event):
        # Reset variables.
        self.reset_variables()

        # Re-enable all widgets.
        for f in self.window.winfo_children():
            for w in f.winfo_children():
                w.configure(state=tk.NORMAL)

        # Reset widget text.
        self.source_btn.configure(text=self.source_label)
        self.source_ent.delete(0, len(self.source_ent.get()))
        self.source_ent.insert(tk.END, self.app.source_cawl_type)
        self.lang_ent.delete(0, len(self.source_ent.get()))
        self.lang_ent.insert(tk.END, self.app.lang)

        self.target_btn.configure(text=self.target_label)
        self.target_ent.delete(0, len(self.target_ent.get()))
        self.target_ent.insert(tk.END, self.app.target_cawl_type)

        self.update_btn.configure(text="Update LIFT file")
        self.status_lab.configure(text='')

    def reset_variables(self):
        # Reset CAWL types.
        self.app.set_user_options()
        self.app.source_file = None
        self.app.source_xml = None
        self.app.target_file = None
        self.app.target_xml = None

    def create_window(self):
        pad = 4
        pady = 9
        root = tk.Tk()
        style = ttk.Style()
        style.theme_use('clam') # alt, clam, classic, default
        root.title("Update glosses in FLEx LIFT file")

        # Set icon.
        data_dir = Path(__file__).parent / 'data'
        icon_path = data_dir / 'icon.png'
        # root.wm_iconphoto(tk.PhotoImage(file=str(icon_path))) # doesn't work!?
        root.tk.call('wm', 'iconphoto', str(root), tk.PhotoImage(file=str(icon_path)))

        # Create window frame.
        frame = ttk.Frame(root, padding="9 9 9 9")
        frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        # Create headings.
        # f_label = ttk.Label(frame, text="Files")
        f_label = ttk.Label(frame, text="")
        f_label.grid(column=1, row=0, padx=pad, pady=0, sticky=tk.W)
        c_label = ttk.Label(frame, text="CAWL tag")
        c_label.grid(column=2, row=0, padx=pad, pady=0, sticky=tk.W)
        l_label = ttk.Label(frame, text="Language Code")
        l_label.grid(column=3, row=0, padx=pad, pady=0, sticky=tk.W)
        s_label = ttk.Label(frame, text="Source:")
        s_label.grid(column=0, row=1, padx=pad, pady=pady, sticky=tk.W)
        t_label = ttk.Label(frame, text="Target:")
        t_label.grid(column=0, row=2, padx=pad, pady=pady, sticky=tk.W)

        # Create Source Button.
        self.source_btn = ttk.Button(frame, padding=pad, text=self.source_label)
        self.source_btn.grid(column=1, row=1, padx=pad, pady=pady, sticky=tk.W)
        self.source_btn.bind("<ButtonRelease>", self.get_source_file)

        # Create Source CAWL Text Entry.
        self.source_ent = ttk.Entry(frame)
        self.source_ent.insert(tk.END, self.app.source_cawl_type)
        self.source_ent.grid(column=2, row=1, padx=pad, pady=pady, sticky=tk.W)
        self.source_ent.bind("<FocusOut>", self.on_source_ent_focusout)
        self.source_ent.bind("<Control-a>", self.ctrl_a)

        # Create Source Language ISO Entry.
        self.lang_ent = ttk.Entry(frame)
        self.lang_ent.insert(tk.END, self.app.lang)
        self.lang_ent.grid(column=3, row=1, padx=pad, pady=pady, sticky=tk.W)
        self.lang_ent.bind("<FocusOut>", self.on_lang_ent_focusout)
        self.lang_ent.bind("<Control-a>", self.ctrl_a)

        # Create Target Button.
        self.target_btn = ttk.Button(frame, padding=pad, text=self.target_label)
        self.target_btn.grid(column=1, row=2, padx=pad, pady=pady, sticky=tk.W)
        self.target_btn.bind("<ButtonRelease>", self.get_target_file)

        # Create Target CAWL Text Entry.
        self.target_ent = ttk.Entry(frame)
        self.target_ent.insert(tk.END, self.app.target_cawl_type)
        self.target_ent.grid(column=2, row=2, padx=pad, pady=pady, sticky=tk.W)
        self.target_ent.bind("<FocusOut>", self.on_target_ent_focusout)
        self.target_ent.bind("<Control-a>", self.ctrl_a)

        # Create Reset Button.
        self.reset_btn = ttk.Button(frame, padding=pad, text="Reset")
        self.reset_btn.grid(column=3, row=2, padx=pad, pady=pady, sticky=tk.W)
        self.reset_btn.bind("<ButtonRelease>", self.reset_widgets)

        # Create Update Button.
        self.update_btn = ttk.Button(
            frame, padding=pad, text="Update LIFT File", state=tk.DISABLED
        )
        self.update_btn.grid(column=1, row=3, padx=pad, pady=pady, sticky=tk.W)
        self.update_btn.bind("<ButtonRelease>", self.on_update_btn_release)

        # Create Status Label.
        self.status_lab = ttk.Label(frame, text="")
        self.status_lab.grid(column=2, row=3, columnspan=2, padx=pad, pady=pady, sticky=tk.W)

        return root
