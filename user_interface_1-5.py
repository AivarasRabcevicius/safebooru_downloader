import time
from tkinter import filedialog, Tk, Entry, Checkbutton, Button, Label, StringVar, Listbox, END, Frame, LEFT, \
    SINGLE, TclError, messagebox, IntVar

from sqlalchemy import select, desc, Column, create_engine, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
import pickle

import requests
import json
import os

default_suggestion_lenght = 20  # defines how wide will the suggestion list be when its empty at the beggining
max_returned_suggestions = 300  # maximum amount of suggestions offered once enter is pressed
posts_pulled_per_request = 1000  # how many posts will the API return per request (max allowed 1000)
directory_path = ""
tag_list_compose = []  # tags ready to be put into a request will be collected here
exitcheck = False  # used to exit download_window loops when exit button has been pressed

engine = create_engine("sqlite:///database.db")
Base = declarative_base()


class TagList(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer)
    count = Column(Integer)
    name = Column("tag_name", String)

    def __init__(self, tag_id, name, count):
        self.tag_id = tag_id
        self.name = name
        self.count = count


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()
window = Tk()
window.title("safebooru downloader")


def requester(tag_list, folder_location, general, sensitive, safe):
    if tag_list:
        if folder_location:
            if general or sensitive or safe:

                def image_downloader():
                    downloaded_images = 0
                    for pic in picture_list:
                        if exitcheck:
                            exit(0)
                        actual_picture = requests.get(pic[0])
                        format = pic[0].split(".")[-1]
                        with open(f"{pic[1]}.{format}", "wb") as f:
                            f.write(actual_picture.content)
                        downloaded_images += 1
                        download_progress["text"] = f"{downloaded_images}/{image_count} downloaded"
                        download_window.update()
                        if downloaded_images == image_count:
                            download_progress["text"] = "DONE! The application will close now"
                            download_window.update()
                            time.sleep(3)
                            exit(0)

                window.destroy()
                download_window = Tk()
                download_window.title("safebooru downloader")
                download_window.geometry("300x100")
                download_window.update()

                def exitcommand():
                    global exitcheck
                    exitcheck = True
                    download_window.destroy()

                download_window.protocol('WM_DELETE_WINDOW', exitcommand)
                download_progress = Label(download_window)
                download_progress.pack()
                pid = 0
                tag_str = "+".join(tag_list)
                try:
                    os.chdir(folder_location)
                except FileNotFoundError:
                    messagebox.showerror("", "entered folder path does not exist, closing application")
                    exit(0)
                picture_list = []
                image_count = 0
                download_progress["text"] = "scanning safebooru for tagged images..."
                while True:
                    booru = requests.get(
                        f"https://safebooru.org/index.php?page=dapi&s=post&q=index&tags={tag_str}&json=1&limit={posts_pulled_per_request}&pid={pid}&json=1")
                    i = 0
                    try:
                        dict = json.loads(booru.text)
                    except json.decoder.JSONDecodeError:
                        print("INFO (decoder error)")
                        if image_count != 0:
                            if messagebox.askokcancel("", f"{image_count} images will be downloaded, continue?"):
                                image_downloader()
                            else:
                                exit(0)
                        else:
                            messagebox.showerror("", "no images found with given tags, closing application")
                            exit(0)
                    while True:
                        if exitcheck:
                            exit(0)
                        try:
                            picture_url = dict[i]["file_url"]
                            print(f"INFO picture url:{picture_url}")
                            picture_id = dict[i]["id"]
                            print(f"INFO picture id:{picture_id}")
                            print(f"INFO scanned images:{i + 1 + pid * posts_pulled_per_request}\n")
                            rating = dict[i]["rating"]
                            if ((general) & (rating == "general")) or ((sensitive) & (rating == "sensitive")) or (
                                    (safe) & (rating == "safe")):
                                picture = [picture_url, picture_id]
                                picture_list.append(picture)
                                image_count += 1
                            i += 1
                        except IndexError:
                            print("INFO index error(break)")
                            break
                        download_window.update()
                    pid += 1

            else:
                messagebox.showerror("", "tick at least one of the rating boxes")
                return None
        else:
            messagebox.showerror("", "select a folder to download images to")
            return None
    else:
        messagebox.showerror("", "select at least one tag")
        return None


def tag_finder(search):
    stmt = select(TagList).order_by(desc(TagList.count)).where(TagList.name.icontains(search)).limit(
        max_returned_suggestions)
    result = session.execute(stmt)
    search_results = {}
    for tag in result.scalars():  # scalars() executes and returns a scalar result set, which yields scalar values from the first column of each row.
        search_results[tag.name] = tag.count
    print(f"INFO search results: {search_results}")
    try:
        longest_suggestion = len(max(search_results, key=len))
    except ValueError:
        messagebox.showerror("",
                             "this tag does not exist in the current program database. You can still try downloading pictures with this tag")
    else:
        suggestion_list.config(width=longest_suggestion + 10)
        print(f"INFO longest suggestion:{longest_suggestion}")
        suggestion_list.delete(0, END)  # END = "end" , used to get the last item on suggestion list
        for suggestion in search_results.items():
            suggestion_list.insert(END, [suggestion[0], f"{suggestion[1]} entries"])  # END is used as an index


def choose_directory():
    global directory_path, folder_location
    directory_path = filedialog.askdirectory(title="Choose a Directory")
    folder_location["text"] = directory_path
    dump_pickle()


def select_suggestion():
    try:
        selected_suggestion = suggestion_list.get(suggestion_list.curselection())
        entry.set(selected_suggestion[0])
    except TclError:
        print(
            "INFO Bad listbox index: this is an expected error that happens when you deselect an item from suggestion list")


def add_button():
    new_tag = entry.get()
    if new_tag in tag_list_compose:
        messagebox.showerror('', 'tag already added')
        print("INFO tag already added")
    else:
        if new_tag:
            tag_list_compose.append(new_tag)
            new_button = Button(frame_mid, text=new_tag)
            new_button["command"] = lambda b=new_button: [b.pack_forget(), tag_list_compose.remove(b["text"]),
                                                          print(f"INFO tag list updated: {tag_list_compose}")]
            new_button.pack(side=LEFT)
            print(f"INFO tag list updated: {tag_list_compose}:")
        else:
            messagebox.showerror('', "put something into the entry box")


def get_pickle():
    global directory_path, folder_location_var
    with open("path.pkl", "rb") as pickle_in:
        directory_path = pickle.load(pickle_in)
        folder_location_var = directory_path


def dump_pickle():
    global folder_location_var
    with open("path.pkl", "wb") as pickle_out:
        pickle.dump(directory_path, pickle_out)
    folder_location_var = directory_path


if not os.path.isfile('./path.pkl'):
    print("INFO no pkl file, creating pkl file")
    dump_pickle()

frame_upper = Frame(window)
frame_upper_lower = Frame(window)
frame_mid = Frame(window)
frame_lower = Frame(window)
frame_lowerest = Frame(window)

tag_list = Label(frame_upper,
                 text="Search for tags, characters, authors,\n then press enter to see suggestions\n leave blank for most popular tags")
entry = StringVar()
tag_list_enter = Entry(frame_upper, textvariable=entry, font=("Arial", 12))
add_tag = Button(frame_upper, text="Add tag", command=add_button)
suggestion_list = Listbox(frame_upper_lower, font=("Arial", 12), width=default_suggestion_lenght, selectmode=SINGLE)

directory_button = Button(frame_lower, text="Choose Directory", command=choose_directory)
folder_location_var = StringVar()
get_pickle()
tags_label = Label(frame_mid, text="added tags (click to remove)")
folder_location = Label(frame_lower, text=folder_location_var)
general_var = IntVar()
sensitive_var = IntVar()
safe_var = IntVar()
general = Checkbutton(frame_lower, text="general", variable=general_var)
sensitive = Checkbutton(frame_lower, text="sensitive", variable=sensitive_var)
safe = Checkbutton(frame_lower, text="safe", variable=safe_var)
download = Button(frame_lowerest, text="DOWNLOAD",
                  command=lambda: requester(tag_list_compose, folder_location.cget("text"), general_var.get(),
                                            sensitive_var.get(), safe_var.get()))

tag_list_enter.bind('<Return>', lambda event: tag_finder(tag_list_enter.get()))
suggestion_list.bind("<<ListboxSelect>>", lambda event: select_suggestion())

frame_upper.pack()
frame_upper_lower.pack()
frame_mid.pack()
frame_lower.pack()
frame_lowerest.pack()

tag_list.pack(side=LEFT)
tag_list_enter.pack(side=LEFT)
add_tag.pack()
suggestion_list.pack()
tags_label.pack()

directory_button.grid(row=2, column=0)
folder_location.grid(row=2, column=1)
general.grid(row=3, column=0)
sensitive.grid(row=3, column=1)
safe.grid(row=3, column=3)

download.pack()

window.mainloop()
