import os
import openai
import speech_recognition as sr
from gtts import gTTS
import tempfile
import pygame
import tkinter as tk
from tkinter import messagebox, ttk
import difflib
from dotenv import load_dotenv  # Load environment variables from .env file

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("⚠ ERROR: OpenAI API Key is missing! Make sure it's in the .env file.")
else:
    print("✅ OpenAI API Key Loaded Successfully.")  # Debugging: Ensure API Key is loaded

# Initialize OpenAI client
client = openai.OpenAI(api_key=api_key)

# Initialize pygame mixer for audio playback
pygame.mixer.init()

def generate_sentences(scenario, count=4):
    """Generates diverse German sentences based on the given scenario."""
    prompt = (
        f"Generate {count} different simple German sentences related to '{scenario}' for beginners. "
        "Ensure variety in vocabulary and structure."
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Provide only German sentences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        print("OpenAI Response:", response)  # Debugging: Print full response
        return response.choices[0].message.content.strip().split("\n")[:count]
    except Exception as e:
        print(f"❌ Error: {e}")
        return ["Error generating sentence"] * count

def play_sentence(sentence):
    """Plays the given sentence using text-to-speech."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        tts = gTTS(text=sentence, lang='de')
        tts.save(temp_file.name)
    pygame.mixer.music.load(temp_file.name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def record_and_check(sentence, feedback_label):
    """Records the user's speech, compares it with the correct sentence, and provides feedback."""
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            feedback_label.config(text="🎙 Listening...", fg="blue")
            feedback_label.update()
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            feedback_label.config(text="⏳ Processing...", fg="orange")
            feedback_label.update()
            spoken_text = recognizer.recognize_google(audio, language='de-DE')
            similarity = difflib.SequenceMatcher(None, spoken_text.lower(), sentence.lower()).ratio()
            feedback_label.config(
                text=(f"✅ Good pronunciation!\nYou said: {spoken_text}" if similarity > 0.8 
                      else f"❌ Try again!\nExpected: {sentence}\nYou said: {spoken_text}"),
                fg="green" if similarity > 0.8 else "red"
            )
    except sr.UnknownValueError:
        feedback_label.config(text="❌ Could not understand speech. Try again.", fg="red")
    except sr.RequestError:
        feedback_label.config(text="🚨 Speech service error. Check your internet.", fg="red")
    except sr.WaitTimeoutError:
        feedback_label.config(text="⏳ Recording timed out. Speak within the limit.", fg="red")

def display_sentences():
    """Fetches and displays generated sentences in the UI."""
    scenario = scenario_var.get()
    if scenario == "Select a Scenario":
        messagebox.showwarning("Warning", "Please select a scenario!")
        return
    
    for widget in sentences_frame.winfo_children():
        widget.destroy()
    
    tk.Label(sentences_frame, text="Generated Sentences:", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(anchor="w", pady=5)
    
    sentences = generate_sentences(scenario)
    for sentence in sentences:
        if sentence:
            frame = tk.Frame(sentences_frame, bg="white", relief="solid", bd=2, highlightbackground="#ccc", highlightthickness=2)
            frame.pack(pady=5, padx=10, fill="x")

            tk.Label(frame, text=sentence, font=("Arial", 12), bg="white", anchor="w", justify="left").pack(side="top", padx=5, pady=3, fill="x")
            
            btns_frame = tk.Frame(frame, bg="white")
            btns_frame.pack(side="bottom", pady=3)
            
            feedback_label = tk.Label(frame, text="", font=("Arial", 10), fg="red", bg="white")
            feedback_label.pack(side="bottom", fill="x", pady=5)
            
            tk.Button(
                btns_frame, text="🔊 Play", command=lambda s=sentence: play_sentence(s),
                font=("Arial", 10, "bold"), padx=10, pady=5
            ).pack(side="left", padx=5)
            
            tk.Button(
                btns_frame, text="🎙 Pronounce", command=lambda s=sentence, fl=feedback_label: record_and_check(s, fl),
                font=("Arial", 10, "bold"), padx=10, pady=5
            ).pack(side="left", padx=5)

# Main UI Setup
window = tk.Tk()
window.title("German Language Practice")
window.geometry("700x700")
window.configure(bg='#f0f0f0')

tk.Label(window, text="German Language Practice", font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=10)

tk.Label(window, text="Choose a Scenario:", font=("Arial", 12), bg="#f0f0f0").pack()
scenario_var = tk.StringVar()
scenario_menu = ttk.Combobox(window, textvariable=scenario_var, values=["Hospital", "Restaurant", "Airport"], state="readonly", width=30, font=("Arial", 12))
scenario_menu.set("Select a Scenario")
scenario_menu.pack(pady=5)

tk.Button(
    window, text="Generate Sentences", font=("Arial", 12, "bold"), 
    command=display_sentences, bg="blue", fg="white", padx=10, pady=5
).pack(pady=10)

sentences_frame = tk.Frame(window, bg="#f0f0f0")
sentences_frame.pack(pady=20, fill="both", expand=True)

window.mainloop()