# Import libraries
import requests
from bs4 import BeautifulSoup
import glob
import shutil
import subprocess
import os
import tkinter as tk
from tkinter import messagebox

if os.path.exists('data.txt') == False:
    # Datei erstellen, wenn sie nicht existiert
    open('data.txt', 'w').close()

#auf Speicher zugreifen
content = open('data.txt', 'r+')

#Dictionary für die Kurse
courses = {}

#Funktion zum Hinzufügen eines Kurses
#Reihenfolge: Link des Kurses, Anzahl heruntergeladener Dateien, 
# letzter heruntergeladener Link (nicht jeder Link ist ein passendes PDF), flashcards,
# max. neue PDFs(-1 = unbegrenzt), directory
def edit_course(newCourse_name, new_course_url, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory):
    global courses
    if newCourse_name not in courses:
        courses[newCourse_name] = []
    courses[newCourse_name] = [new_course_url, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory]
    storeInput()

#Speicher auslesen
#Reihenfolge: Name des Kurses, Link des Kurses, Anzahl bereits heruntergeladener PDFs, 
# letzter heruntergeladener Link, flashcards, max. neue PDFs, directory
for row in content:
    parts = row.strip().split(',')
    if len(parts) == 7: 
        course_name = parts[0].strip()
        course_link = parts[1].strip()
        downloaded_count = int(parts[2].strip())
        last_downloaded_link = int(parts[3].strip())
        flashcards = parts[4].strip().lower() == 'true'
        max_new_pdfs = int(parts[5].strip())
        directory = parts[6].strip()
        courses[course_name] = [course_link, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory]

#Speicher in Datei schreiben
def storeInput():
    with open('data.txt', 'w') as f:
        for course_name, (course_link, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory) in courses.items():
            f.write(f"{course_name},{course_link},{downloaded_count},{last_downloaded_link},{flashcards},{max_new_pdfs},{directory}\n")

#Cookies initialisieren
cookies = {
    'MoodleSession': 'DEIN_SESSION_COOKIE_WERT'
}

# Funktion zum Setzen der Cookies
def set_cookies(new_cookies):
    global cookies
    cookies = new_cookies

# Fehlerklasse für spezifische Fehlermeldungen
class Fehler(Exception):
    def __init__(self, nachricht):
        self.nachricht = nachricht
        super().__init__(self.nachricht)

def getInput(downloaded_count = 0, last_downloaded_link = 0):
    try:
        new_course_url = entry2.get()
        newCourse_name = entry3.get().replace(" ", "-")
        flashcards = flashcards_var.get()
        if entry4.get() != "" and not entry4.get().isdigit(): raise Fehler("Invalid input for max new PDFs")
        if entry4.get() != "" and int(entry4.get()) < 0: raise Fehler("Negative number not allowed")
        max_new_pdfs = int(entry4.get()) if entry4.get()!= "" else -1
        directory = entry5.get()

        #Speichern der Änderungen
        if new_course_url and newCourse_name and directory:
            edit_course(newCourse_name, new_course_url, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory)
        else:
            raise Fehler("All fields are required.")
        messagebox.showinfo("Success", "Course added successfully!", parent=root)
    except Fehler as f:
        messagebox.showerror("Changes not saved!", f.nachricht, parent=root)

def UpdateAllCourses():
    try:
        if entry1.get() == "":
            raise Fehler("Cookies field is empty. It may not be possible to download files.")
    except Fehler as f:
        messagebox.showerror("Error", f.nachricht, parent=root)
    c = entry1.get()
    set_cookies({'MoodleSession': c})

    for course_name, (course_link, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory) in courses.items():

        # URL from which pdfs to be downloaded
        url = course_link

        # Requests URL, hand over Cookies and get response object
        response = requests.get(url, cookies=cookies, allow_redirects=True)

        # Parse text obtained
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all hyperlinks present on webpage
        links = soup.find_all('a')

        i = 1 #Nummer eines Links, last_downloaded_link mit 0 initialisiert
        j = downloaded_count #Anzahl pro Modul heruntergeladaner PDFs, downloaded_count mit 0 initialisiert
        y = downloaded_count  

        # From all links check for pdf link and
        # if present download file
        for link in links:
            href = link.get('href')
            if href and ('resource' in href or '.pdf' in href):
                if i > last_downloaded_link: #nur unbekannte PDFs runterladen
                    if j < downloaded_count + max_new_pdfs or max_new_pdfs == -1: #max. neue PDFs beachten, -1 = unbegrenzt

                        # Get response object for link
                        response = requests.get(href,cookies=cookies,allow_redirects=True)

                        # Write content in pdf file
                        if response.headers.get('Content-Type', '').startswith('application/pdf'):
                            j += 1
                            base_filename = f"{course_name}{j}.pdf"
                            filename = base_filename
                            while os.path.exists(filename):
                                j += 1
                                filename = f"{course_name}{j}.pdf"
                            print("Downloading file:", j)
                            with open(filename, 'wb') as pdf:
                                pdf.write(response.content)
                            print("File ", j, " downloaded")
                        else:
                            response_download = requests.get(href, cookies=cookies, allow_redirects=True)
                            soup_download = BeautifulSoup(response_download.text, 'html.parser') 
                            download_links = soup_download.find_all('a')
                            for download_link in download_links:
                                download_href = download_link.get('href')
                                if download_href and download_href.endswith('.pdf'):
                                    j += 1
                                    base_filename = f"{course_name}{j}.pdf"
                                    filename = base_filename
                                    while os.path.exists(filename):
                                        j += 1
                                        filename = f"{course_name}{j}.pdf"
                                    print("Downloading file:", j)
                                    pdf_response = requests.get(download_href, cookies=cookies, allow_redirects=True)
                                    with open(filename, 'wb') as pdf:
                                        pdf.write(pdf_response.content)
                                    print("File ", j, " downloaded")
                    else:
                        break
                i += 1
        z = j        
        courses[course_name][1] = j # Update downloaded_count
        courses[course_name][2] = i-1 # Update last_downloaded_link
        storeInput()

        print("All PDF files from " + course_name + " downloaded")
        
        directory_of_python_script = os.path.dirname(os.path.abspath(__file__))

        if flashcards:
            # Convert PDF files to PNG
            for x in range(y+1,z+1): # sonst werden alle PDFs eines Moduls zu Karteikarten gemacht!
                pattern = f"{str(course_name)}{x}.pdf"
                for pdf_file in glob.glob(os.path.join(directory_of_python_script, pattern)):
                    output_prefix = os.path.splitext(pdf_file)[0] 
                    try:
                        subprocess.run([
                            "pdftoppm",
                            "-png",
                            "-r", "300",
                            pdf_file,
                            output_prefix
                        ]) 
                    except Exception as e:
                        messagebox.showerror("Error converting PDF to PNG:", e, parent=root)

        # Move all pdf and png files to another folder
        if directory_of_python_script != directory:
            for x in range(y+1,z+1): 
                pattern = f"{str(course_name)}{x}"
                for pdf_file in glob.glob(os.path.join(f"{pattern}.pdf")):
                    try:
                        shutil.move(pdf_file, directory)
                    except Exception as e:
                        messagebox.showerror("Error moving file:", e, parent=root)
                for png_file in glob.glob(os.path.join(f"{pattern}*.png")):
                    try:
                        shutil.move(png_file, directory)
                    except Exception as e:
                        messagebox.showerror("Error moving file:", e, parent=root)

# Hauptfenster erstellen
root = tk.Tk()
root.title("PDF Downloader")
root.geometry("600x600")

# Eingabefelder und Labels
label1 = tk.Label(root, text="Cookies:")
label1.pack(pady=5)
entry1 = tk.Entry(root)
entry1.pack(pady=5)

def add_course_window():
    global entry2, entry3, entry4, entry5, flashcards_var

    # Erstelle ein neues Toplevel-Fenster
    add_course_window = tk.Toplevel(root)
    add_course_window.title("Course")
    add_course_window.geometry("500x500")  

    # Eingabefelder
    label2 = tk.Label(add_course_window, text="Add URL from new course:")
    label2.pack(pady=5)
    entry2 = tk.Entry(add_course_window)
    entry2.pack(pady=5)

    label3 = tk.Label(add_course_window, text="Name of new course:")
    label3.pack(pady=5)
    entry3 = tk.Entry(add_course_window)
    entry3.pack(pady=5)

    label4 = tk.Label(add_course_window, text="max. new PDFs per course or leave empty:")
    label4.pack(pady=5)
    entry4 = tk.Entry(add_course_window)
    entry4.pack(pady=5)

    label5 = tk.Label(add_course_window, text="Directory(where to save):")
    label5.pack(pady=5)
    entry5 = tk.Entry(add_course_window)
    entry5.pack(pady=5)

    #Checkbox für Karteikarten
    flashcards_var = tk.BooleanVar(value=False)
    checkbox = tk.Checkbutton(add_course_window, text="Create flashcards", variable=flashcards_var)
    checkbox.pack(pady=10)

    # Button zum Abspeichern
    calc_button = tk.Button(add_course_window, text="Save Changes", command=getInput)
    calc_button.pack(pady=10)

def editing_one_course_window(course_name, course_link, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory):
    global entry2, entry3, entry4, entry5, flashcards_var

    #Erstelle ein neues TopLevel-Fenster
    editing_one_course_window = tk.Toplevel(root)
    editing_one_course_window.title("Editing " + course_name)
    editing_one_course_window.geometry("500x500")

    #Eingabefelder
    label2 = tk.Label(editing_one_course_window, text="Edit URL:")
    label2.pack(pady=5)
    course_link_var = tk.StringVar(value=course_link)
    entry2 = tk.Entry(editing_one_course_window, textvariable=course_link_var)
    entry2.pack(pady=5)

    label3 = tk.Label(editing_one_course_window, text="Edit name:")
    label3.pack(pady=5)
    course_name_var = tk.StringVar(value=course_name)
    entry3 = tk.Entry(editing_one_course_window, textvariable=course_name_var)
    entry3.pack(pady=5)

    label4 = tk.Label(editing_one_course_window, text="max. new PDFs per course or leave empty:")
    label4.pack(pady=5)
    max_new_pdfs_var = tk.StringVar(value=max_new_pdfs)
    entry4 = tk.Entry(editing_one_course_window, textvariable=max_new_pdfs_var)
    entry4.pack(pady=5)

    label5 = tk.Label(editing_one_course_window, text="Directory(where to save):")
    label5.pack(pady=5)
    directory_var = tk.StringVar(value=directory)
    entry5 = tk.Entry(editing_one_course_window, textvariable=directory_var)
    entry5.pack(pady=5)

    #Checkbox für Karteikarten
    flashcards_var = tk.BooleanVar(value=flashcards)
    checkbox = tk.Checkbutton(editing_one_course_window, text="Create flashcards", variable=flashcards_var)
    checkbox.pack(pady=10)

    # Button zum Abspeichern
    calc_button = tk.Button(editing_one_course_window, text="Save Changes", command=lambda: getInput(downloaded_count, last_downloaded_link))
    #command mit lambda, da ich an die Funktion getInput() Parameter übergebe und sie sonst direkt aufgerufen werden würde
    calc_button.pack(pady=10)


def edit_course_window():
    global courses, editing_one_course_window

    edit_course_window = tk.Toplevel(root)
    edit_course_window.title("Edit Courses")
    edit_course_window.geometry("500x500")

    # Canvas und Scrollbar
    canvas = tk.Canvas(edit_course_window)
    scrollbar = tk.Scrollbar(edit_course_window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Frame für Inhalt
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")

    label1 = tk.Label(frame, text="Choose Course by Clicking:")
    label1.pack(pady=5)

    for course_name, (course_link, downloaded_count, last_downloaded_link, flashcards, max_new_pdfs, directory) in courses.items():
        course_button = tk.Button(frame, text=course_name, command=lambda 
                                  c=course_name, cl=course_link, do=downloaded_count, 
                                  la=last_downloaded_link, f=flashcards, m=max_new_pdfs, d=directory: editing_one_course_window(c, cl, do, la, f, m, d))
        course_button.pack(pady=5, anchor="center", fill="x", side="top")

    # Canvas-Größe aktualisieren
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# Button im Hauptfenster, der Fenster zum Kurs hinzufügen öffnet
button = tk.Button(root, text="Add Course", command=add_course_window)
button.pack(pady=10)

# Button zum Kurs editieren
edit_button = tk.Button(root, text="Edit Course", command=edit_course_window)
edit_button.pack(pady=10)

# Button zum Downloaden
download_button = tk.Button(root, text="Download PDFs", command=UpdateAllCourses)
download_button.pack(pady=10)

# Hauptschleife starten (Fenster bzw. GUI offenhalten)
root.mainloop()

