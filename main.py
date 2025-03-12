sound_files_in_order = []

from pydub import AudioSegment
from gtts import gTTS
import os
import zipfile
import json
import sqlite3
from deep_translator import GoogleTranslator
import re

extracted_files = "extracted_files"

def sanitize_filename2(filename, replacement = ""):
    return filename.replace("&nbsp;",replacement)

def sanitize_filename(filename, replacement=" "):
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename (str): Original filename.
        replacement (str): Character to replace invalid characters with. Defaults to "_".
    
    Returns:
        str: Sanitized filename.
    """
    # Define characters that are not allowed in file names
    # Invalid characters for Windows: \ / : * ? " < > |
    invalid_chars = r'[\\/:*?"<>|]'
    
    # Replace invalid characters with the replacement character
    sanitized_name = re.sub(invalid_chars, replacement, filename)
    
    # Optionally, trim leading/trailing whitespace or replace multiple replacements with one
    sanitized_name = sanitized_name.strip()
    sanitized_name = re.sub(f"{re.escape(replacement)}+", replacement, sanitized_name)
    
    return sanitized_name

def create_folder_if_missing(folder_path):
    # Check if the folder exists and create it if it doesn't
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder created at: {folder_path}")

def extract_akpg(file_path):
    # Rename .akpg to .zip
    zip_file_path = file_path.replace('.akpg', '.zip')
    (os.rename(file_path, zip_file_path))

    # Extract the .zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall('extracted_files')
    print("Extracted files to 'extracted_files'.")

def create_apkg(extract_dir, output_apkg):
    """Repackage extracted files into an Anki .apkg file."""
    zip_file_path = output_apkg.replace('.apkg', '.zip')

    # Create a ZIP archive
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
        for root, _, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, extract_dir)  # Maintain relative paths
                zip_ref.write(file_path, arcname)

    # Rename .zip back to .apkg
    os.rename(zip_file_path, output_apkg)
    print(f"Created '{output_apkg}' successfully.")

def translate_text(text, target_language='en'):
    translator = GoogleTranslator(source='auto', target=target_language)
    return translator.translate(text)

def create_text_to_speach(text,lang ):
    text = sanitize_filename(text)
    text = sanitize_filename2(text)

    tts = gTTS(text=text, lang=lang)
    create_folder_if_missing("tmp")
    file_path = 'tmp/' +text + ""
    tts.save(file_path)
    return file_path

def get_file_name_for_reference(reference):
    print("reference: ", reference)
    # Path to your media JSON file
    media_file_path = extracted_files + '/media'  # or 'media' if it has no extension

    # Open and load the JSON file
    with open(media_file_path, 'r', encoding='utf-8') as f:
        media_map = json.load(f)

    # Now media_map is a Python dictionary, and you can access its contents
    #print(media_map)

    file_reference = None
    for key, value in media_map.items():
        if value == reference:
            file_reference = key
            break

    # Print the result
    if file_reference:
        return file_reference
    else:
        return None


def load_notes_from_collection(root):
    db_path = root + '/collection.anki21'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get the note fields
    cursor.execute("SELECT * FROM notes")

    # Fetch all notes
    notes = cursor.fetchall()

    return notes

def load_cols_from_collection(root):
    db_path = root + '/collection.anki21'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to get the note fields
    cursor.execute("SELECT * FROM col")

    # Fetch all notes
    notes = cursor.fetchall()

    return notes



def get_json_keys(parsed_data):
    ret = []
    for key, value in parsed_data.items():
        #print(key)
        ret.append(key)
    return ret

class NoteInfo(object):
    """docstring for NoteInfo"""
    def __init__(self, root = "/Users/andersmb15/Desktop/JapaneseListeningApp_POC/jp-basic/Jlab_Beginner_course_audio_export.apkg"):
        
        extract_akpg(root)
        self.notes = load_notes_from_collection(extracted_files)
        self.col = load_cols_from_collection(extracted_files)
    
    def get_notes_for_id(self,note_id):
        # Path to the extracted SQLite database (collection.anki2)
        db_path = extracted_files

        # Connect to the SQLite database
        conn = sqlite3.connect(extracted_files +'/collection.anki21')
        cursor = conn.cursor()

        # Query to get the note fields
        cursor.execute("SELECT * FROM notes")

        # Fetch all notes
        notes = cursor.fetchall()

        # Print the note fields for inspection

        ret = []

        for note in notes:
            this_note_id = (note[2])
            if(this_note_id == note_id):
                ret.append(note)
        return ret
            

    def get_notes_for_note_name(self, note_name):
        note_id = self.get_note_id_for_note_name(note_name)
        notes = self.get_notes_for_id(note_id)
        return notes

    def get_note_id_for_note_name(self,target_note_name):
        for c in self.col:
           
            parsed_data = json.loads(c[9])
            
            keys = get_json_keys(parsed_data)
            for key in keys: 
                if(parsed_data[key]["name"] == target_note_name):
                    #print("Found Target: ", parsed_data[key]["name"] )
                    return (parsed_data[key]["id"])
               
def get_filed_from_note(note, filed_inx):
        tup = note
        tup2 = (tup[6].split(''))
        return tup2[filed_inx]

class StepType(object):
    MP3_TYPE = 1
    TTS = 2
    TTTS = 3 
    """docstring for step_type"""
    def __init__(self, type,lang = None):
        self.type = type
        self.lang = lang
        

class Step(object):
    """docstring for Step"""
    def __init__(self,field_inx, repetition_cnt, step_type, backup_step = None):
        super(Step, self).__init__()
        self.field_inx = field_inx
        self.repetition_cnt = repetition_cnt
        self.step_type = step_type
        self.backup_step = backup_step 

    def get_audio_for_step(self, note):
        pause_duration = 2000
        pause = AudioSegment.silent(duration=pause_duration)
        combined_audio = AudioSegment.empty()


        
        if(self.step_type.type == StepType.MP3_TYPE):
            text0 = get_filed_from_note(note, self.field_inx)
            if(text0[text0.find("[sound:")]):
                mp3_0 = (text0[7:len(text0)-1])
            else:
                mp3_0 = text0
            
            mp3_file_name = get_file_name_for_reference(mp3_0)
            tts_file_path = 'extracted_files/' + mp3_file_name + ""
            tts_audio = AudioSegment.from_mp3(tts_file_path)
            for i in range(0,self.repetition_cnt):
                combined_audio += tts_audio
                combined_audio += pause
        
        elif self.step_type.type == None:
            assert(0)
        
        elif self.step_type.type == StepType.TTS:
            text0 = get_filed_from_note(note, self.field_inx)
            if len(text0) == 0:
                if(self.backup_step != None):
                    return self.backup_step.get_audio_for_step(note)
                return combined_audio
            tts_file_path = create_text_to_speach(text0, self.step_type.lang)
            # Load the TTS audio
            tts_audio = AudioSegment.from_mp3(tts_file_path)
            for i in range(0,self.repetition_cnt):
                combined_audio += tts_audio
                combined_audio += pause

        elif self.step_type.type == StepType.TTTS: 
            text0 = get_filed_from_note(note, self.field_inx)
            text0 = translate_text(text0, target_language = self.step_type.lang)
        
            tts_file_path = create_text_to_speach(text0, self.step_type.lang)
        
            # Load the TTS audio
            tts_audio = AudioSegment.from_mp3(tts_file_path)
            for i in range(0,self.repetition_cnt):
                combined_audio += tts_audio
                combined_audio += pause
        else:
            #print(self.step_type.type)
            assert(0)
        
        return combined_audio
                    


class sequence(object):
    """docstring for sequence"""
    def __init__(self, notes):
        self.steps = []
        self.notes = notes

    def add_step(self,field_inx, repetition_cnt, step_type, backup_step = None):
        self.steps.append(Step(field_inx,repetition_cnt, step_type, backup_step = backup_step))

    def genrate_cards(self, card_prefix, track_name_inx = None):
        create_folder_if_missing("output")
        for cnt, note in enumerate(self.notes):
            combined_audio = AudioSegment.empty()
            for step_cnt, step in enumerate(self.steps):
                combined_audio += step.get_audio_for_step(note)
            track_name = ""
            if track_name_inx != None:
                track_name = get_filed_from_note(note, track_name_inx)
                track_name = sanitize_filename(track_name)
                track_name = sanitize_filename2(track_name)
            output_file_path = f'output/{cnt}_{card_prefix}_{track_name}.mp3'
            combined_audio.export(output_file_path, format='mp3')

def get_fields_from_note_type(root, model_id):
    db_path = root + '/collection.anki21'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query the `col` table to get the models (JSON format)
    cursor.execute("SELECT models FROM col")
    result = cursor.fetchone()

    if not result:
        print("No models found in the database.")
        return None

    models_json = result[0]  # Extract the JSON string
    models = json.loads(models_json)  # Convert it to a dictionary

    # Find the model by ID
    model = models.get(str(model_id))

    if not model:
        print(f"No model found with ID {model_id}")
        return None

    # Extract the list of field names
    field_names = [field["name"] for field in model["flds"]]

    return field_names

import sqlite3
import json

def get_model_id_by_name(root, note_type_name):
    db_path = root + '/collection.anki21'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT models FROM col")
    result = cursor.fetchone()

    if not result:
        print("No models found.")
        return None

    models_json = result[0]
    models = json.loads(models_json)

    # Search for the model ID by note type name
    for model_id, model_data in models.items():
        if model_data["name"].lower() == note_type_name.lower():
            return int(model_id)  # Convert model_id to integer

    print(f"Note type '{note_type_name}' not found.")
    return None

def get_notes_by_model_id(root, model_id):
    db_path = root + '/collection.anki21'

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id, flds FROM notes WHERE mid = ?", (model_id,))
    notes = cursor.fetchall()

    return notes

import os
import json
import sqlite3
from gtts import gTTS
import time

def add_tts_to_notes(root, target_note_type,filename_prefix, target_text=11, target_audio_field=19):
    # Paths for the deck and media files
    media_mapping_path = os.path.join(root, "media")  # Use "media" file, not media.json

    # Ensure root folder exists
    if not os.path.exists(root):
        os.makedirs(root)

    # Load existing media mapping if it exists
    media_mapping = {}
    if os.path.exists(media_mapping_path):
        with open(media_mapping_path, "r", encoding="utf-8") as f:
            media_mapping = json.load(f)

    db_path = os.path.join(root, "collection.anki21")

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Step 1: Find the note type ID for "Basic" (or the specified type)
    cursor.execute("SELECT models FROM col")
    col_data = cursor.fetchone()

    if not col_data:
        print("⚠️ No data found in 'col' table!")
        return

    models_json = json.loads(col_data[0])  # Load JSON from the `models` field
    note_type_ids = {int(k): v["name"] for k, v in models_json.items()}  # Map ID to name

    # Find the note type ID for the given name
    target_note_type_id = None
    for model_id, model_name in note_type_ids.items():
        if model_name.lower() == target_note_type.lower():
            target_note_type_id = model_id
            break

    if target_note_type_id is None:
        print(f"⚠️ Note type '{target_note_type}' not found!")
        return

    print(f"✅ Filtering notes with Note Type ID: {target_note_type_id}")

    # Step 2: Get all notes of the specified type
    cursor.execute("SELECT id, flds FROM notes WHERE mid = ?", (target_note_type_id,))
    notes = cursor.fetchall()

    # Find the next available numeric media ID
    existing_ids = {int(k) for k in media_mapping.keys()}  # Convert keys to integers
    next_media_id = max(existing_ids) + 1 if existing_ids else 0  # Start at 0 if empty

    for note_id, fields in notes:
        field_list = fields.split("\x1f")  # Split fields using Anki's separator

        if len(field_list) <= target_text:
            print(f"Skipping note {note_id}: Not enough fields")
            continue

        english_text = field_list[target_text]  # The field containing English translation
        if not english_text.strip():
            print(f"Skipping note {note_id}: Empty English translation")
            continue

        # Generate a unique numeric filename (e.g., "10", "11", "12")
        filename = str(next_media_id)
        filepath = os.path.join(root, filename)  # No file extension

        print(f"🎙️ Generating audio for Note {note_id}: {english_text}")
        time.sleep(0.5)
        tts = gTTS(english_text, lang="en")
        tts.save(filepath)

        # Update media mapping
        file_name_with_extension = f"audio_{filename_prefix}_{note_id}.mp3"
        media_mapping[str(next_media_id)] = file_name_with_extension
        next_media_id += 1  # Increment for next file

        # Step 6: Store the audio reference in the specified field
        if target_audio_field is not None and target_audio_field < len(field_list):
            field_list[target_audio_field] = f"[sound:{file_name_with_extension}]"
        else:
            # Find the first empty field if target_audio_field isn't given
            for i in range(len(field_list)):
                if field_list[i].strip() == "":
                    field_list[i] = f"[sound:{file_name_with_extension}]"
                    break
            else:
                print(f"⚠️ No empty field for Note {note_id}, skipping audio embedding.")
                continue

        # Step 7: Update the database with the new field data
        updated_fields = "\x1f".join(field_list)
        cursor.execute("UPDATE notes SET flds = ? WHERE id = ?", (updated_fields, note_id))

    # Step 8: Save changes to database and media mapping
    conn.commit()
    conn.close()

    # Save the updated media mapping back to "media" file
    with open(media_mapping_path, "w", encoding="utf-8") as f:
        json.dump(media_mapping, f, ensure_ascii=False, indent=4)

    print("✅ Successfully added TTS audio to all notes!")







def create_apkg(output_folder, output_filename):
    """
    Zips the extracted Anki deck files and renames them as a .apkg package.
    
    :param output_folder: The folder containing extracted Anki deck files (e.g., 'extracted_files')
    :param output_filename: The desired output filename (e.g., 'new-deck.apkg')
    """
    zip_filename = output_filename.replace(".apkg", ".zip")  # Create a temp .zip file
    output_apkg = output_filename  # Final .apkg file name

    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_folder)  # Preserve structure
                zipf.write(file_path, arcname)

    # Rename to .apkg
    os.rename(zip_filename, output_apkg)
    print(f"✅ Created '{output_apkg}' successfully!")

def add_audio_to_deck(input_deck_name, output_deck_name,output_folder):
    extract_akpg(input_deck_name)  # Extract an Anki deck
    create_apkg(output_folder, output_deck_name)  # Recreate the Anki deck
    root = extracted_files
    #note_type_name = "Japanese Morphman Audio Ankiweb+++++"  # Example note type name

    #model_id = get_model_id_by_name(root, note_type_name)
    #if model_id:
    #    notes = get_notes_by_model_id(root, model_id)
    #    for n in notes:
    #        print("---")
    #        print(n)
    add_tts_to_notes(root=extracted_files, target_note_type = "Core 2000+", filename_prefix = sentence)
    create_apkg(output_folder="extracted_files", output_filename="Core 2000 - Audio Extra 2.apkg")

    
    
        
