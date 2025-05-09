from tkinter import filedialog, Tk, Entry, Checkbutton, Button, Label, StringVar, Listbox, END, Frame, LEFT, \
    SINGLE, TclError, messagebox, IntVar

from sqlalchemy import select, desc
from sqlalchemy.orm import sessionmaker
import pickle

from sqlalchemy import Column , create_engine , Integer , String
from sqlalchemy.orm import declarative_base

engine = create_engine("sqlite:///database.db")
Base = declarative_base()

class TagList (Base):
    __tablename__ = "tags"
    id = Column(Integer , primary_key=True )
    tag_id = Column (Integer)
    count = Column(Integer)
    name = Column("tag_name" , String)

    def __init__(self , tag_id , name , count):
        self.tag_id = tag_id
        self.name = name
        self.count = count


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

window = Tk()
default_suggestion_lenght = 20
max_returned_suggestions = 100

directory_path = ""
tag_list_compose = []

import requests
import json
import os

posts_pulled_per_request = 1000




def requester(tag_list, folder_location, general, sensitive, safe):
    if tag_list:
        if folder_location:
            if general or sensitive or safe:
                window.destroy()
                download_window = Tk()
                # download_window.protocol('WM_DELETE_WINDOW', lambda : [ exit(0) , download_window.destroy()])
                download_window.geometry("300x100")
                download_window.update()
                # download_progress_var = StringVar()
                # download_progress_var.set("test")
                download_progress = Label(download_window)
                download_progress.pack()
                pid = 0
                tag_str = "+".join(tag_list)
                folder_name = " ".join(tag_list)
                os.chdir(folder_location)
                # try:
                #     os.makedirs(folder_name)
                #     os.chdir(f"{folder_location}{folder_name}")
                # except FileExistsError:
                #     os.chdir(f"{folder_location}{folder_name}")
                while True:
                    booru = requests.get(
                        f"https://safebooru.org/index.php?page=dapi&s=post&q=index&tags={tag_str}&json=1&limit={posts_pulled_per_request}&pid={pid}&json=1")
                    i = 0
                    try:
                        dict = json.loads(booru.text)
                    except json.decoder.JSONDecodeError:
                        print("DONE! (decoder error)")
                        download_progress["text"] = "DONE!"
                        # exit_button = Button(download_window , text="Exit" , command=lambda : exit(0) )
                        # exit_button.pack()
                        return 0
                    # print(dict)
                    # json_object = json.dumps(dict, indent=4)
                    # with open("sample.json" , "w") as f:
                    #     f.write(json_object)
                    while True:
                        try:
                            print(dict[i]["file_url"])
                            print(dict[i]["id"])
                            print(i + 1 + pid * posts_pulled_per_request)
                            download_progress["text"] = "pictures downloaded:" + str(
                                i + 1 + pid * posts_pulled_per_request)
                            nuotrauka_url = dict[i]["file_url"]
                            nuotrauka_id = dict[i]["id"]
                            rating = dict[i]["rating"]
                            if ((general) & (rating == "general")) or ((sensitive) & (rating == "sensitive")) or (
                                    (safe) & (rating == "safe")):
                                nuotrauka = requests.get(nuotrauka_url)
                                format = nuotrauka_url.split(".")[-1]
                                with open(f"{nuotrauka_id}.{format}", "wb") as f:
                                    f.write(nuotrauka.content)
                            i += 1
                        except IndexError:
                            print("index error(break)")
                            break
                        download_window.update()
                        # global ExitFlag
                        # if ExitFlag:
                        #     print("exit 0")
                        #     exit(0)
                        # except KeyError:
                        #     print("DONE!( key error")
                        #     exit(0)
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


# def new_window():
#     download_window = Tk()
#     download_window.mainloop()

def tag_finder(search):
    stmt = select(TagList).order_by(desc(TagList.count)).where(TagList.name.icontains(search)).limit(
        max_returned_suggestions)
    result = session.execute(stmt)
    search_results = {}
    for user_obj in result.scalars():
        search_results[user_obj.name] = user_obj.count
    print(search_results)
    try:
        longest_suggestion = len(max(search_results, key=len))
    except ValueError:
        messagebox.showerror("",
                             "this tag does not exist in the current program database. You can still try downloading pictures with this tag")
    else:
        suggestion_list.config(width=longest_suggestion)
        print(f"longest {longest_suggestion}")
        # search_results = sorted(search_results.items(), key= lambda item: item[1] , reverse=True)
        print(search_results)
        # suggestion_list.update()
        suggestion_list.delete(0, END)
        for suggestion in search_results:
            suggestion_list.insert(END, suggestion)


def choose_directory():
    global directory_path, folder_location, se
    directory_path = filedialog.askdirectory(title="Choose a Directory")
    folder_location["text"] = directory_path
    dump_pickle()


def select_suggestion():
    try:
        selected_suggestion = suggestion_list.get(suggestion_list.curselection())
        entry.set(selected_suggestion)
    except TclError:
        print(
            "Bad listbox index: this is an expected error that happens when you deselect an item from suggestion list")


def add_button():
    new_tag = entry.get()
    if new_tag in tag_list_compose:
        messagebox.showerror('', 'tag already added')
        print("tag already added")
    else:
        if new_tag:
            tag_list_compose.append(new_tag)
            new_button = Button(frame_mid, text=new_tag)
            new_button["command"] = lambda b=new_button: [b.pack_forget(), tag_list_compose.remove(b["text"])]
            new_button.pack(side=LEFT)
            print(tag_list_compose)
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
    print("no pkl")
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
# folder_location = Label(langas, text="Folder location")

directory_button = Button(frame_lower, text="Choose Directory", command=choose_directory)
folder_location_var = StringVar()
get_pickle()
folder_location = Label(frame_lower, text=folder_location_var)
general_var = IntVar()
sensitive_var = IntVar()
safe_var = IntVar()
general = Checkbutton(frame_lower, text="general", variable=general_var)
sensitive = Checkbutton(frame_lower, text="sensitive", variable=sensitive_var)
safe = Checkbutton(frame_lower, text="safe", variable=safe_var)
download = Button(frame_lowerest, text="DOWNLOAD",
                  command=lambda: [requester(tag_list_compose, folder_location.cget("text"), general_var.get(),
                                             sensitive_var.get(), safe_var.get())])

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

directory_button.grid(row=2, column=0)
folder_location.grid(row=2, column=1)
general.grid(row=3, column=0)
sensitive.grid(row=3, column=1)
safe.grid(row=3, column=3)

download.pack()

window.mainloop()
