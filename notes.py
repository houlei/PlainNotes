import sublime, sublime_plugin
import os, fnmatch, re

from gzip import GzipFile
from pickle import load, dump

ST3 = int(sublime.version()) >= 3000

def settings():
    return sublime.load_settings('Notes.sublime-settings')

class NotesListCommand(sublime_plugin.ApplicationCommand):

    def run(self):
        root = settings().get("root")
        window = sublime.active_window()
        self.notes_dir = os.path.expanduser(root)
        self.file_list = self.find_notes()
        window.show_quick_panel([f[0] for f in self.file_list], self.open_note)

    def find_notes(self):
        note_files = []
        for path, subdirs, files in os.walk(self.notes_dir):
            for name in files:
                for ext in settings().get("note_file_extensions"):
                    if fnmatch.fnmatch(name, "*." + ext):
                        note_files.append((re.sub('\.' + ext + '$', '', name),
                                           os.path.join(path, name),
                                           os.path.getmtime(os.path.join(path, name))
                                          ))
        note_files.sort(key=lambda item: item[2], reverse=True)
        return note_files

    def open_note(self, index):
        if index == -1:
            return
        file_path = self.file_list[index][1]
        # self.window.run_command("new_pane",{"move": True})
        view = sublime.active_window().open_file(file_path)
        f_id = file_id(file_path)
        if db.get(f_id) and db[f_id]["color_scheme"]:
            view.settings().set("color_scheme", db[f_id]["color_scheme"])


class NotesNewCommand(sublime_plugin.ApplicationCommand):

    def run(self, title=None):
        root = settings().get("root")
        self.notes_dir = os.path.expanduser(root)

        self.window = sublime.active_window()
        if title is None:
            self.window.show_input_panel("Title", "", self.create_note, None, None)
        else:
            self.create_note(title)

    def create_note(self, title):
        file = os.path.join(self.notes_dir, title + ".note")
        if not os.path.exists(file):
            open(file, 'w+').close()
        view = sublime.active_window().open_file(file)
        self.insert_title_scheduled = False
        self.insert_title(title, view)

    def insert_title(self, title, view):
        if view.is_loading():
            if not self.insert_title_scheduled:
                self.insert_title_scheduled = True
                sublime.set_timeout(lambda: self.insert_title(title, view), 100)
            return
        else:
            view.run_command("note_insert_title", {"title": title})


class NoteInsertTitleCommand(sublime_plugin.TextCommand):
    def run(self, edit, **kwargs):
        header = "# " + kwargs["title"].capitalize() + "\n"
        self.view.insert(edit, 0, header)


class NoteChangeColorCommand(sublime_plugin.WindowCommand):

    def __init__(self, view):
        self.colors = ["Orange", "Yellow", "Green", "GreenLight", "Blue", "BlueLight", "Purple", "Pink", "Gray", "White"]

    def on_select(self, index):
        global db
        if index == -1:
            self.window.active_view().settings().set("color_scheme", self.original_cs)
        else:
            path = os.path.join("Packages" , "SublimeNotes", "Color Schemes", "Sticky-" + self.colors[index] + ".tmTheme")
            view = self.window.active_view()
            view.settings().set("color_scheme", path)
            f_id = file_id(view.file_name())
            if not db.get(f_id):
                db[f_id] = {}
            db[f_id]["color_scheme"] = path
            save_to_brain()

    def on_highlight(self, index):
        path = os.path.join("Packages" , "SublimeNotes", "Color Schemes", "Sticky-" + self.colors[index] + ".tmTheme")
        self.window.active_view().settings().set("color_scheme", path)

    def run(self):
        self.window = sublime.active_window()
        self.original_cs = self.window.active_view().settings().get("color_scheme")
        current_color = os.path.basename(self.original_cs).replace("Sticky-","").replace(".tmTheme", "")
        # show_quick_panel(items, on_done, <flags>, <selected_index>, <on_highlighted>)
        self.window.show_quick_panel(self.colors, self.on_select, 0, self.colors.index(current_color), self.on_highlight)

    # TODO activated

def file_id(path):
    return os.path.relpath(path, root)

def save_to_brain():
    print("SAVING TO DISK-----------------")
    print(db)
    gz = GzipFile(db_file, 'wb')
    dump(db, gz, -1)
    gz.close()


def plugin_loaded():
    global db, root, db_file
    # creating root if it does not exist
    root = os.path.expanduser(settings().get("root"))
    if not os.path.exists(root):
        os.makedirs(root)
    # open db
    db = {}
    db_file = os.path.join(root, '.brain', 'brain.bin.gz')
    try:
        os.makedirs(os.path.dirname(db_file))
    except:
        pass
    try:
        gz = GzipFile(db_file, 'rb')
        db = load(gz)
        gz.close()
    except:
        db = {}

if not ST3:
    plugin_loaded()
