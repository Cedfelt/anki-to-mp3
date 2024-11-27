sound_files_in_order = []

root = "jp-basic"
from pydub import AudioSegment
from gtts import gTTS
import os
import zipfile
import json
import sqlite3
from deep_translator import GoogleTranslator

extracted_files = "extracted_files"

def extract_akpg(file_path):
    # Rename .akpg to .zip
    zip_file_path = file_path.replace('.akpg', '.zip')
    (os.rename(file_path, zip_file_path))

    # Extract the .zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall('extracted_files')
    print("Extracted files to 'extracted_files'.")

def translate_text(text, target_language='en'):
    translator = GoogleTranslator(source='auto', target=target_language)
    return translator.translate(text)

def create_text_to_speach(text,lang ):
    tts = gTTS(text=text, lang=lang)
    file_path = 'tmp/' +text + ""
    tts.save(file_path)
    return file_path

def sanitize_filename(filename):
    # Remove or replace any characters that are not allowed in file names.
    # You can adjust the regex pattern to allow certain characters.
    return re.sub(r'[<>:"/\\|?*()]', '', filename)

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

    def genrate_cards(self, card_prefix):
        
        
        for cnt, note in enumerate(self.notes):
            combined_audio = AudioSegment.empty()
            for step_cnt, step in enumerate(self.steps):
                combined_audio += step.get_audio_for_step(note)
            output_file_path = f'output/{cnt}_{card_prefix}.mp3'
            combined_audio.export(output_file_path, format='mp3')


def jp_basic_deck():
    target_notes = "JlabNote-JlabConverted-1"
    tmp = NoteInfo()
    notes = tmp.get_notes_for_note_name(target_notes)
    seq = sequence(notes)
    
    # Sentence Japaense 
    seq.add_step(field_inx = 3,repetition_cnt = 3, step_type = StepType(type = StepType.MP3_TYPE, lang = "ja",))

    # Sentence English 
    backup_step = Step(field_inx = 11 , repetition_cnt = 1, step_type = StepType(type = StepType.TTTS, lang = "en"))
    seq.add_step(field_inx = 17,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "en",), backup_step = backup_step)

    seq.genrate_cards(card_prefix = "jp_basic")


def peppa_deck():
    
    target_notes = "PeppaPig"
    tmp = NoteInfo()
    notes = tmp.get_notes_for_note_name(target_notes)
    seq = sequence(notes)
    
    # Vocab Japaense 
    seq.add_step(field_inx = 2,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "ja",))

    # Vocab English 
    seq.add_step(field_inx = 3,repetition_cnt = 1, step_type = StepType(type = StepType.TTTS, lang = "en",))

    # Japanese Setence 
    seq.add_step(field_inx = 0,repetition_cnt = 3, step_type = StepType(type = StepType.TTS, lang = "ja",))
    
    # English Sentence
    backup_step = Step(field_inx = 0 , repetition_cnt = 1, step_type = StepType(type = StepType.TTTS, lang = "en"))
    seq.add_step(field_inx = 1,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "en",), backup_step = backup_step)
    
    seq.genrate_cards(card_prefix = "podcast2")


def shirokuma_deck():
    target_notes = "Japanese Morphman Audio Ankiweb+++++"
    tmp = NoteInfo()
    notes = tmp.get_notes_for_note_name(target_notes)
    seq = sequence(notes)
    
    # Sentence Japaense 
    seq.add_step(field_inx = 5,repetition_cnt = 2, step_type = StepType(type = StepType.MP3_TYPE, lang = "ja",))

    # Sentence English 
    seq.add_step(field_inx = 1,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "en",))

    seq.genrate_cards(card_prefix = "shirokuma")

def ebba_engelska_swe():
    target_notes = "PeppaPig"
    tmp = NoteInfo(root = "/Users/andersmb15/Desktop/JapaneseListeningApp_POC/jp-basic/Ebba-Engelska.apkg")
    notes = tmp.get_notes_for_note_name(target_notes)
    seq = sequence(notes)
    
    # Sentence English 
    seq.add_step(field_inx = 0,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "sv",))

    seq.genrate_cards(card_prefix = "ebba_engelska_sv")

def ebba_engelska_eng():
    target_notes = "PeppaPig"
    tmp = NoteInfo(root = "/Users/andersmb15/Desktop/JapaneseListeningApp_POC/jp-basic/Ebba-Engelska.apkg")
    notes = tmp.get_notes_for_note_name(target_notes)
    seq = sequence(notes)
    
    # Sentence English 
    seq.add_step(field_inx = 1,repetition_cnt = 1, step_type = StepType(type = StepType.TTS, lang = "en",))

    seq.genrate_cards(card_prefix = "ebba_engelska_eng")

if __name__ == '__main__':
    jp_basic_deck()
    #ebba_engelska_eng()
    #ebba_engelska_swe()

    

    

    
        
        
