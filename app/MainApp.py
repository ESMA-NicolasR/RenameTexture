import re
import shutil
import tkinter
import tkinter as tk
from pathlib import Path
from tkinter.filedialog import askdirectory
from enum import StrEnum


class ScreenName(StrEnum):
    HOME = "HOME"
    RENAME = "RENAME"


class HeaderLabel(StrEnum):
    HOME = "F-Rename ready to serve !"
    RENAME = "Rename texture files"


class Header:
    def __init__(self, main_app: "MainApp"):
        self.main_app = main_app
        self.root_frame = tk.Frame(self.main_app.root)
        self.label = tk.Label(self.root_frame, text=HeaderLabel.HOME)
        self.button = tk.Button(self.root_frame, text="Home", command=self.main_app.display_home_screen)

        self.display_label_and_button()
        self.root_frame.pack(side=tk.TOP)

    def change_label(self, new_label: str):
        self.label['text'] = new_label

    def display_only_label(self):
        self.label.grid_forget()
        self.button.grid_forget()

        self.label.grid(row=0, column=0, columnspan=2)

    def display_label_and_button(self):
        self.label.grid_forget()
        self.button.grid_forget()

        self.button.grid(row=0, column=0)
        self.label.grid(row=0, column=1)


class Body:
    def __init__(self, main_app: "MainApp"):
        self.main_app = main_app
        self.root_frame = tk.Frame(self.main_app.root, bg="#777")
        self.root_frame.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.current_screen = None

    def swap_to_screen(self, new_screen):
        if self.current_screen is not None:
            self.current_screen.hide()

        self.current_screen = new_screen
        self.current_screen.show()


class Footer:
    def __init__(self, main_app: "MainApp"):
        self.main_app = main_app
        self.root_frame = tk.Frame(self.main_app.root)
        self.label = tk.Label(self.root_frame)
        self.label.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        self.root_frame.pack(side=tk.BOTTOM)

    def display_message(self, message: str, color: str = "black"):
        self.label.config(text=message, fg=color)

    def clear(self):
        self.label.config(text="", fg='black')


class Screen:
    def __init__(self, main_app: "MainApp"):
        self.main_app = main_app
        self.root_frame = tk.Frame(self.main_app.body.root_frame)

    def show(self):
        self.root_frame.pack(expand=tk.YES, fill=tk.BOTH)

    def hide(self):
        self.root_frame.pack_forget()


class HomeScreen(Screen):
    def __init__(self, main_app: "MainApp"):
        super().__init__(main_app)

        (tk.Button(self.root_frame, text=ScreenName.HOME, command=self.change_screen(ScreenName.HOME))
         .pack(side=tk.LEFT, expand=True, fill=tk.BOTH))
        (tk.Button(self.root_frame, text=ScreenName.RENAME, command=self.change_screen(ScreenName.RENAME))
         .pack(side=tk.LEFT, expand=True, fill=tk.BOTH))

    def change_screen(self, screen: ScreenName):
        def inner_change():
            self.main_app.change_screen(screen)

        return inner_change


class RenameScreen(Screen):
    OBJECT_BEFORE_MAP = 1
    MAP_BEFORE_OBJECT = 2
    NUMBER_AFTER_MAP = 1
    NUMBER_AFTER_OBJECT = 2

    def __init__(self, main_app: "MainApp"):
        super().__init__(main_app)

        self.word_position = tkinter.IntVar(value=self.OBJECT_BEFORE_MAP)
        self.number_position = tkinter.IntVar(value=self.NUMBER_AFTER_MAP)
        self.renamed_prefix = "T_"

        self.files_success = 0
        self.files_error = 0
        self.files_ignored = 0

        self.root_frame.grid_columnconfigure(0, weight=1)
        self.root_frame.grid_columnconfigure(1, weight=1)
        self.root_frame.grid_columnconfigure(2, weight=1)
        self.root_frame.grid_rowconfigure(2, weight=1)

        tk.Label(self.root_frame, text="Source directory").grid(row=0, column=0, sticky="ew")
        self.ent_file = tk.Entry(self.root_frame)
        self.ent_file.grid(row=0, column=1, sticky="ew", padx=5)
        btn_file = tk.Button(self.root_frame, text="...", command=lambda: self.ask_directory_and_insert_into_entry(self.ent_file))
        btn_file.grid(row=0, column=2)

        tk.Label(self.root_frame, text="File prefix").grid(row=1, column=0, sticky="ew")
        self.ent_prefix = tk.Entry(self.root_frame)
        self.ent_prefix.grid(row=1, column=1, sticky="ew", padx=5)
        self.ent_prefix.delete(0, tk.END)
        self.ent_prefix.insert(0, "SM_")

        tk.Label(self.root_frame, text="Word position").grid(row=2, column=0, sticky="ew")
        self.rb_1 = tk.Radiobutton(self.root_frame, text="Object before map", value=self.OBJECT_BEFORE_MAP, variable=self.word_position, command=self.refresh_preview)
        self.rb_1.grid(row=2, column=1, sticky="ew")
        self.rb_2 = tk.Radiobutton(self.root_frame, text="Map before object", value=self.MAP_BEFORE_OBJECT, variable=self.word_position, command=self.refresh_preview)
        self.rb_2.grid(row=2, column=2, sticky="ew")

        tk.Label(self.root_frame, text="Number position").grid(row=3, column=0, sticky="ew")
        self.rb_3 = tk.Radiobutton(self.root_frame, text="After map", value=self.NUMBER_AFTER_MAP, variable=self.number_position, command=self.refresh_preview)
        self.rb_3.grid(row=3, column=1, sticky="ew")
        self.rb_4 = tk.Radiobutton(self.root_frame, text="After object", value=self.NUMBER_AFTER_OBJECT, variable=self.number_position, command=self.refresh_preview)
        self.rb_4.grid(row=3, column=2, sticky="ew")

        tk.Label(self.root_frame, text="Preview : ").grid(row=4, column=0, sticky="ew")
        self.preview_label = tk.Label(self.root_frame, text="...")
        self.preview_label.grid(row=4, column=1, sticky="ew")
        self.refresh_preview()

        tk.Button(self.root_frame, text="Rename", command=self.rename).grid(row=5, column=0, columnspan=3, sticky="ew")

    def rename(self):
        # Init metrics
        self.files_error = 0
        self.files_success = 0
        self.files_ignored = 0

        # Find files in directory
        directory = self.ent_file.get()
        file_list = self.list_files(directory)

        # Create ouput directory
        output_dir = Path(directory) / "output"
        output_dir.mkdir(exist_ok=True)

        # Rename each file
        prefix = self.ent_prefix.get()
        for file in file_list:
            if not file.name.startswith(prefix):
                self.main_app.log_warning(f"Skipping {file.name}")
                self.files_ignored += 1
                continue
            try:
                base_name = file.name.split("_M_")[0].split(prefix)[1]
                map_name = file.name.split(".png")[0].split("_")[-1]
                search = re.search(r"_\d+", file.name)
                number = search.group()
                base_name = base_name.replace(number, "")
                map_name = map_name.replace(number, "")
                new_name = self.get_name_from_words(self.renamed_prefix, base_name, map_name, number) + ".png"
                self.rename_file(directory, file.name, output_dir, new_name)
                self.files_success += 1
            except:
                self.main_app.log_error(f"Could not rename {file.name}")
                self.files_error += 1

        # Print result
        self.main_app.log_info(f"Renamed {self.files_success} files, skipped {self.files_ignored} files, error on {self.files_error} files")

    def list_files(self, directory):
        dir_path = Path(directory)
        return list(dir_path.glob("./*.png"))

    def rename_file(self, og_folder, og_name, new_folder, new_name):
        og_path = Path(og_folder) / og_name
        new_path = Path(new_folder) / new_name
        shutil.copy(og_path, new_path)
        self.main_app.log_success(f"{og_path} => {new_path} OK")

    def ask_directory_and_insert_into_entry(self, entry):
        filepath = askdirectory()
        if filepath:
            entry.delete(0, tk.END)
            entry.insert(0, filepath)

    def get_name_from_words(self, prefix, object, map, number):
        s_result = f"{prefix}"
        s_object = f"{object}"
        s_map = f"{map}"
        if(self.number_position.get()==self.NUMBER_AFTER_OBJECT):
            s_object += f"{number}"
        elif(self.number_position.get()==self.NUMBER_AFTER_MAP):
            s_map += f"{number}"
        if(self.word_position.get()==self.OBJECT_BEFORE_MAP):
            s_result += f"{s_object}_{s_map}"
        elif(self.word_position.get()==self.MAP_BEFORE_OBJECT):
            s_result += f"{s_map}_{s_object}"

        return s_result

    def refresh_preview(self):
        self.preview_label.config(text=self.get_name_from_words(self.renamed_prefix, "Cube", "Normal", "_001"))


class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("F-Rename")
        self.root.geometry("400x300")

        self.header = Header(self)
        self.body = Body(self)
        self.footer = Footer(self)
        self.screens = {
            ScreenName.HOME: HomeScreen(self),
            ScreenName.RENAME: RenameScreen(self),
        }

        self.display_home_screen()

        self.root.mainloop()

    def display_home_screen(self):
        self.header.change_label(HeaderLabel.HOME)
        self.header.display_only_label()

        self.body.swap_to_screen(self.screens[ScreenName.HOME])

        self.log_info("Messages will appear here")

    def display_rename_screen(self):
        self.header.change_label(HeaderLabel.RENAME)
        self.header.display_label_and_button()

        self.body.swap_to_screen(self.screens[ScreenName.RENAME])

        self.log_info("Select a directory that contains texture files")

    def change_screen(self, screen: ScreenName):
        return {
            ScreenName.HOME: self.display_home_screen,
            ScreenName.RENAME: self.display_rename_screen,
        }.get(screen, self.fail_change_screen(screen))()

    def fail_change_screen(self, screen: str):
        def inner_fail():
            self.log_error(f"Screen not found: {screen}")

        return inner_fail

    def log_info(self, message: str):
        self.footer.display_message(message, "teal")

    def log_error(self, message: str):
        self.footer.display_message(message, "red")

    def log_warning(self, message: str):
        self.footer.display_message(message, "orange")

    def log_success(self, message: str):
        self.footer.display_message(message, "green")


if __name__ == "__main__":
    MainApp()
