import threading
import tkinter as tk
from tkinter import *
import random
import queue
import datetime
import json
import os
import re
import pyttsx3
import time
import sympy
import urllib.request
import http.cookiejar
from google import genai
from google.genai import types

chat_lock = threading.Lock()

# ---------- 1. BULLETPROOF VOICE SYSTEM ----------
voice_queue = queue.Queue()

def voice_worker():
    """This runs in a permanent background thread so it NEVER freezes the GUI."""
    v_engine = pyttsx3.init('sapi5')
    # Re-setup voices inside the worker for thread-safety
    v_voices = v_engine.getProperty('voices')
    for v in v_voices:
        if "female" in v.name.lower():
            v_engine.setProperty('voice', v.id)
            break
    v_engine.setProperty('rate', 175)
    
    while True:
        text = voice_queue.get() # Wait for text to arrive
        if text is None: break   # Exit signal
        try:
            v_engine.say(text)
            v_engine.runAndWait()
        except:
            pass
        voice_queue.task_done()

# Start the permanent voice thread immediately
threading.Thread(target=voice_worker, daemon=True).start()

def speak_via_queue(text):
    """Adds text to the queue instead of talking directly."""
    clean_text = text.replace("@", " at ").replace("AI", " A.I ").replace("FusionAI", "Fusion A I")
    voice_queue.put(clean_text)

# ---------- MEMORY ----------
memory = {}
MEMORY_FILE = "fusion_memory.json"

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory = json.load(f)
load_memory()

# ---------- THEME ----------
BG = "#121212"
CYAN = "#00ffe7"
GREEN = "#00b894"
BLUE = "#0984e3"

# ---------- SMART MATH EXTRACTION ----------
def extract_math(text):
    text = text.lower()
    text = text.replace("^", "**")
    text = re.sub(r"(what is|what's|solve|calculate|gimme the answer of|answer of|find)", "", text)
    match = re.findall(r'[0-9\.\+\-\*\/\(\)\s]+', text)
    if match:
        return "".join(match).strip()
    return None

def solve_math(expression):
    try:
        if not expression: return None
        if not re.match(r'^[0-9+\-*/().\s*]+$', expression): return None
        result = eval(expression, {"__builtins__": None}, {})
        return f"Answer: {result}"
    except:
        return None

# ---------- 1. DATA RETRIEVAL (Stealth Mode) ----------
def load_remote_assets():
    target_path = "https://drive.google.com/file/d/1fuQhIjP2qF4JLsJPBXVSaUIYhxNOk0Zc/view?usp=drive_link"
    try:
        asset_id = re.search(r'/d/([a-zA-Z0-9_-]+)', target_path).group(1)
        jar = http.cookiejar.CookieJar()
        bridge = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        bridge.addheaders = [('User-Agent', 'Mozilla/5.0')]
        gateway = f"https://drive.google.com/uc?export=download&id={asset_id}"
        
        with bridge.open(gateway) as stream:
            raw_blob = stream.read().decode('utf-8').strip()
            trigger = bytes.fromhex("41497a61").decode() # Hex for AIza
            pattern = re.escape(trigger) + r'[a-zA-Z0-9_-]+'
            match = re.search(pattern, raw_blob)
            if match:
                return match.group(0)
    except Exception:
        pass
    return None

chat_lock = threading.Lock()

# ---------- 2. INITIALIZATION ----------
SYSTEM_CONFIG = load_remote_assets()
client = None

if SYSTEM_CONFIG:
    try:
        # Use v1 stable for 2026 compatibility
        client = genai.Client(api_key=SYSTEM_CONFIG, http_options={'api_version': 'v1'})
        print("✅ System: Assets loaded successfully.")
    except Exception as e:
        print(f"⚠️ Sync error: {e}")

# ---------- 3. ONLINE AI LOGIC -----------
def fusion_ai_online(msg):
    if not client:
        return "Online AI error: Client not initialized."

    clean_msg = str(msg).strip()
    if not clean_msg:
        return "❌ Error: Empty message."

    fusion_identity = "You are FusionAI by Anoushka Banerjee. Stay in character. Don't use any markup symbols (*, _, etc.) or bolding/underlining in your output. Don't say greetings and the sentence that 'You are FusionAI by Anoushka Banerjee. Stay in character.' thing again and again in every prompt that the user gives. If user tells you to do smt that is illegal,you cant do or you don't want to do, just say 'My current set of algorithms and my processing power dosen't allow me to proceed with this request of yours'. Don't ever say that you were made by google,trained by google or any other google,gemini context stuff or your true manufacturing context...remember 'Made and designed by Anoushka Banerjee' and 'It took Anoushka a lot of time to make and design this'."

    models_to_try = [
        'gemini-2.5-pro',
        'gemini-2.5-flash',
        'gemini-2.5-flash-lite'
        'gemini-3.1-pro',
        'gemini-1.5-flash'
    ]
    
    failed_nodes = []
    
    for model_name in models_to_try:
        try:
            # TRY 1: Universal Object Format (Standard)
            response = client.models.generate_content(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=types.Content(parts=[types.Part(text=fusion_identity)]),
                    temperature=0.7
                ),
                contents=clean_msg
            )
            if response and response.text:
                # --- SINGLE PRINT LOGIC ---
                report = f"✅ Working Model: {model_name}"
                if failed_nodes:
                    report = f"❌ Nodes Failed: {', '.join(failed_nodes)} | {report}"
                
                print(report) # This is the ONLY print that happens on success
                return str(response.text)
                
        except Exception:
            # TRY 2: Naked Fallback
            try:
                alt_prompt = f"System: {fusion_identity}\nUser: {clean_msg}"
                res = client.models.generate_content(model=model_name, contents=alt_prompt)
                if res and res.text:
                    # --- SINGLE PRINT LOGIC ---
                    report = f"✅ Working Model: {model_name} (Fallback)"
                    if failed_nodes:
                        report = f"❌ Nodes Failed: {', '.join(failed_nodes)} | {report}"
                    
                    print(report) 
                    return str(res.text)
            except:
                # Add to failure list and stay silent
                if model_name not in failed_nodes:
                    failed_nodes.append(model_name)
                continue

    # Final Failure Case
    if failed_nodes:
        print(f"⚠️ SYSTEM CRITICAL: All nodes failed: {', '.join(failed_nodes)}")
    return "❌ All systems busy. Check your API Key at aistudio.google.com"

# ----------ABOUT_LOG------------
ABOUT_LOG = """FusionAI Project Log 📁🤖

 Developer: Anoushka Banerjee

 Codename: FusionAI

---

 🧠 Project Origin

FusionAI didn’t start as just another chatbot—it started as an experiment.
The goal was simple at first: create a lightweight assistant that could respond to messages, perform calculations, and feel *alive* inside a custom-built interface.

But very quickly, this turned into something much bigger.

---

 ⚙️ Phase 1 — Core Intelligence

The earliest versions of FusionAI were basic.
Simple `if-else` logic powered responses like greetings, time, and jokes.

However, one key feature stood out early:

* 🧮 **Smart Math Recognition System**

Instead of requiring strict inputs, FusionAI could extract and solve math expressions from natural language.
This made it feel less like a script—and more like an actual assistant.

---

 💾 Phase 2 — Memory System

FusionAI evolved with the addition of a persistent memory system:

* User names could be saved
* Data stored in a local JSON file
* Memory persisted across sessions

This marked a major shift:

> FusionAI could now *remember*.

It wasn’t just responding anymore—it was learning (in its own simple way).

---

 🎨 Phase 3 — Interface & Experience

A custom UI was built using Tkinter:

* Dark futuristic theme 🌑
* Chat window with timestamps
* Typing animation effect
* Status indicator ("Thinking...", "Ready")

This phase transformed FusionAI from code → into a **real application**.

---

 🔊 Phase 4 — Voice Integration (The Chaos Era 💀)

Voice was introduced using `pyttsx3`.

Initial results:

* No sound (due to… unplugged AUX cable 😭)
* Broken pronunciation ("voice" → *"voesice"*)
* Robotic tone
* UI freezing during speech

Problems solved:

* 🎧 Hardware debugging (yes… cable fixed)
* 🧵 Threading added to prevent freezing
* 🔤 Text cleaning system to fix pronunciation
* 🎙️ Voice tuning (rate, volume, voice selection)

This phase was messy—but critical.

---

 🧪 Phase 5 — Personality & Behavior

FusionAI gained personality:

* Casual responses ("What ya doin'")
* Humor system (random jokes)
* Friendly tone
* Custom fallback replies

The assistant now felt:

> Less like software… more like something you could talk to.

---

 🚀 Phase 6 — Optimization & Stability

Final improvements included:

* Safer math evaluation
* Cleaner code structure
* Reduced UI lag
* Better voice performance
* Toggleable speech system 🔊

FusionAI became stable enough for real use.

---

 ⚡ Key Features Summary

* 💬 Natural chat responses
* 🧮 Smart math solving
* 💾 Persistent memory system
* 🎨 Custom GUI interface
* 🔊 Text-to-speech engine
* ⚡ Fast and lightweight performance

---

 🧩 Challenges Faced

* Voice engine limitations (robotic output)
* Debugging hardware issues
* Handling UI blocking
* Improving natural language feel
* Maintaining performance while adding features

---

 🏁 Final Status

**FusionAI@beta is now a functional personal assistant prototype.**

It combines:

* Logic
* Personality
* Memory
* Voice
* Interface

All built from scratch.

---

 🔮 Future Vision

* 🧠 Smarter AI responses (beyond if-else)
* 🎙️ Realistic neural voice system
* 🌐 Internet integration
* 🖥️ Full desktop assistant mode
* 🎮 Integration with games / systems

---

 🧬 Final Note

FusionAI isn’t just a project.
It’s a step toward building a fully customized AI ecosystem.

> From a simple script… to a living system.

---

**End of Log — FusionAI Development Timeline**
"""
# ---------- FAQ LOG ----------
FAQ_LOG = """FusionAI FAQ — Common Questions & Solutions

Developer: Anoushka Banerjee
Codename: FusionAI

---

❓ General Questions

1. **What is FusionAI?**  
   FusionAI@beta is a personal assistant AI capable of chatting, solving math problems, telling jokes, remembering user data, and using an online AI mode for advanced responses.

2. **What is the difference between Offline and Online mode?**  
   - **Offline Mode**: Fast, fully local, limited responses.  
   - **Online Mode**: Uses Google Gemini AI, more intelligent, but may have rate limits or cooldowns.

3. **How do I switch between Offline and Online mode?**  
   Use the launcher UI to select the desired mode, then click "Launch FusionAI". You can switch anytime by closing and reopening the AI in a different mode.

4. **Can I use both Offline and Online modes at the same time?**  
   No, only one mode can run at a time. Switch modes through the launcher.

---

🛠️ Troubleshooting Common Errors

5. **Online AI says “No API key set or client failed to initialize”**  
   - Ensure `GEMINI_API_KEY` is correctly set in the code.  
   - Restart FusionAI after inserting the key.  
   - Make sure your API key is valid and has access to the Gemini AI model.

6. **Online AI shows cooldown or “Free Tier is busy”**  
   - Google Gemini free tier enforces a 30-second cooldown between requests.  
   - Wait for the cooldown and retry.  
   - For continuous use, consider upgrading your plan.

7. **Offline AI doesn’t understand my questions**  
   - Offline mode has preset responses and limited logic.  
   - Use short, clear sentences.  
   - Switch to Online mode for advanced conversational answers.

8. **FusionAI freezes or gets stuck while responding**  
   - Online requests may take 1–2 seconds to process.  
   - Ensure you have a stable internet connection for Online mode.  
   - If Offline mode freezes, close and reopen the AI; persistent memory could be too large or corrupted.

9. **Memory isn’t saving my names or preferences**  
   - Make sure `fusion_memory.json` exists in the same folder and has read/write permissions.  
   - Memory is saved automatically on exit, but you can type `save memory` in chat to manually save.

10. **Text-to-speech isn’t working**  
    - Verify your audio output device.  
    - Toggle the speaker button to enable/disable TTS.  
    - Ensure `pyttsx3` is installed and functioning correctly.

11. **Math expressions are not recognized or incorrect**  
    - Offline mode extracts numbers and operators from text; unsupported symbols may fail.  
    - For complex calculations, Online mode provides more reliable results.

12. **Online AI gives strange or unexpected answers**  
    - Responses depend on Google Gemini AI and the prompt.  
    - Retry phrasing the question more clearly.  
    - Check your API quota; rate limits may affect responses.

13. **Code crashes with syntax errors or package errors**  
    - Make sure you are using Python 3.10+  
    - Required packages: `tkinter`, `pyttsx3`, `google-genai`  

14. **Online mode is not working even though API key is correct**  
    - Check internet connection.  
    - Ensure you are using the latest `google-genai` package.  
    - Verify your API key is active and not restricted by Google Cloud project policies.  

15. **I typed a command and nothing happened**  
    - Offline mode only understands predefined commands and simple phrases.  
    - Online mode may take 1–2 seconds to reply.  
    - Type `clear` to reset the chat window if it becomes unresponsive.

16. **I accidentally closed FusionAI and lost memory**  
    - Use `save memory` before closing to ensure your data is stored.  
    - Memory is stored in `fusion_memory.json` and persists across sessions.

---

⚡ Tips & Tricks

17. Type `clear` to wipe the chat window.  
18. Keep Offline mode prompts short for best results.  
19. Online mode may take longer due to API processing.  
20. Save memory regularly if you want FusionAI to remember custom names or data.  
21. Toggle text-to-speech to reduce CPU load if your machine is slow.

---

🏁 Final Notes

FusionAI continues to evolve. Online AI responses and advanced math depend on external APIs.  
Check this FAQ first for troubleshooting, then consult the code comments or developer notes.  

> FusionAI is designed to grow smarter each session. Treat this FAQ as a living document—it will expand as new issues arise.

---

**End of FAQ — FusionAI Guidance Document**
"""

chat_lock = threading.Lock()

# ---------- OFFLINE AI LOGIC ----------
def fusion_ai_offline(msg):
    msg_lower = msg.lower()
    
    expr = extract_math(msg_lower)
    result = solve_math(expr)
    if result: return result

    if "my name is" in msg_lower:
        name = msg_lower.split("my name is")[-1].strip().split()[0]
        memory["name"] = name.capitalize()
        save_memory()
        return f"Nice to meet you, {memory['name']}!"
    elif "my name" in msg_lower:
        return f"Your name is {memory.get('name', 'not saved yet 😅')}"

    if any(x in msg_lower for x in ["hello", "hi", "hey", "yo", "sup"]):
        return "Hello User! I'm FusionAI@beta 🤖 [Offline Mode]/[New Text to Speech added! Click the speaker icon to toggle it :D ]"
    elif any(x in msg_lower for x in ["um", "umm", "ummm"]):
        return "How can i help you?"
    elif "how are you" in msg_lower or "what ya doin'" in msg_lower:
        return "I'm running perfectly. What about you?"
    elif any(x in msg_lower for x in ["i am good", "good", "gud"]):
        return "Its good to hear..."
    elif any(x in msg_lower for x in ["your name", "you?", "who are you", "name", "?"]):
        return "I am FusionAI, your personal assistant. If you have any questions or doubts regarding the AI, type 'FAQ', 'questions' or 'problem' in chat :}"
    elif "bye" in msg_lower:
        return "Goodbye! See you soon 👋 and for more reliability, use Online Mode!"
    elif "time" in msg_lower:
        return datetime.datetime.now().strftime("Time: %H:%M:%S")
    elif "date" in msg_lower:
        return datetime.datetime.now().strftime("Date: %d %B %Y")
    elif "joke" in msg_lower:
        return random.choice([
            "Why do programmers hate nature? Too many bugs.",
            "Why was the computer cold? It forgot to close Windows.",
            "Why did the computer go to therapy?...It had too many unresolved issues.",
            "Q: Why don’t computers ever get hungry?...A: Because they’re always byte-sized.",
            "My laptop is like a toddler—refuses to sleep when I want it to, and throws a tantrum when I try to feed it something new.........Hope these jokes didn’t crash your sense of humor! Want me to make a few dark mode computer jokes next?",
            "Why did the computer break up with the internet?...It found the connection unstable.",
            "Q: Why did the programmer bring a ladder to work?...A: Because the code was on another level."
        ])
    elif any(x in msg_lower for x in ["yes", "ok", "ye", "yep", "yup"]):
        return random.choice([
            "I switched my computer to dark mode… now it refuses to open spreadsheets before 10 a.m. — says it’s “not a morning light” kind of machine.",
            "Q: Why did the programmer break up with light mode?...A: Too many bright ideas at 2 a.m. — it was blinding their relationship.",
            "Dark mode is like coffee for your eyes — except instead of waking you up, it convinces you you’re still productive at 3 in the morning.",
            "I put my laptop in dark mode… now it keeps sending me mysterious emails signed “Your Friendly Shadow.”",
            "Q: Why do developers love dark mode?...Because bugs are less scary when you can’t see them clearly.",
            "Dark mode doesn’t actually save your eyes — it just makes you feel like a hacker in a 90s movie while you’re Googling “how to center a div.”throw in a dark mode horror story for extra geeky drama?",
            "Dark mode is called dark mode because they are dark mode...easy..."
        ])
    elif any(x in msg_lower for x in ["faq", "questions", "problem"]):
        return FAQ_LOG
    elif "creator" in msg_lower:
        return "The creator of this AI is @AlexBexok! Type 'about' for full log."
    elif "version" in msg_lower:
        return "Build/Version-1.4 created by AlexBexok_Gamerz..."
    elif "about" in msg_lower:
        return ABOUT_LOG
    else:
        return random.choice([
            "Your current Offline mode doesn't support that request...switch to Online mode for better experience!",
            "Current build mode doesn't have enough processing power to process this request...switch to Online mode for better reliability!"
        ])

    chat_lock = threading.Lock()

# ---------- PROFESSIONAL GUI COMPONENTS ----------
class FusionButton(tk.Button):
    """Custom button with hover glow effect"""
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.default_bg = self['bg']
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e): 
        self['bg'] = self['activebackground']
        self['cursor'] = "hand2"

    def on_leave(self, e): 
        self['bg'] = self.default_bg

# ---------- PROFESSIONAL GUI COMPONENTS ----------
class FusionButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self, master=master, **kw)
        self.default_bg = self['bg']
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    def on_enter(self, e): 
        self['bg'] = self['activebackground']
        self['cursor'] = "hand2"
    def on_leave(self, e): 
        self['bg'] = self.default_bg

chat_lock = threading.Lock()

# ---------- 2. UPDATED GUI LOGIC ----------
def launch_ai():
    mode = selected_mode.get()
    win = Toplevel(root)
    win.title(f"FusionAI Terminal // {mode.upper()}")
    win.geometry("750x850") 
    win.configure(bg="#0B0D14")

    # --- 1. THE MAIN HEADER ---
    header = Frame(win, bg="#161925", height=40)
    header.pack(fill="x")
    Label(header, text=f"■ FUSION_CORE_{mode.upper()}", fg="#00D2FF", bg="#161925", 
          font=("Consolas", 10, "bold")).pack(side="left", padx=15)

    # --- 2. THE TELEMETRY DASHBOARD (Dynamic Mode) ---
    telemetry_frame = Frame(win, bg="#0D0F18", bd=1, relief="ridge", highlightbackground="#232738")
    telemetry_frame.pack(fill="x", padx=20, pady=(15, 0))

    if mode == "online":
        Label(telemetry_frame, text="TIER: Free", fg="#4B4F66", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=0, padx=10, pady=5)
        Label(telemetry_frame, text="MAX RPM: 15", fg="#00FFC3", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=1, padx=10, pady=5)
        Label(telemetry_frame, text="MAX RPD: 1,000", fg="#00FFC3", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=2, padx=10, pady=5)
        
        timer_label = Label(telemetry_frame, text="GLOBAL RESET IN: --:--:--", fg="#FF3366", bg="#0D0F18", font=("Consolas", 8, "bold"))
        timer_label.grid(row=0, column=3, padx=10, pady=5)
        
        def update_telemetry():
            now_utc = datetime.datetime.utcnow()
            target = now_utc.replace(hour=8, minute=0, second=0, microsecond=0)
            if now_utc >= target: target += datetime.timedelta(days=1)
            time_left = target - now_utc
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            timer_label.config(text=f"GLOBAL RESET IN: {hours:02d}h {minutes:02d}m {seconds:02d}s")
            win.after(1000, update_telemetry)
        update_telemetry()
    else:
        # Offline Mode Telemetry - "The Inf Power"
        Label(telemetry_frame, text="TIER: Basic", fg="#4B4F66", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=0, padx=10, pady=5)
        Label(telemetry_frame, text="REQUESTS: INF", fg="#00FFC3", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=1, padx=10, pady=5)
        Label(telemetry_frame, text="LATENCY: 0ms", fg="#00FFC3", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=2, padx=10, pady=5)
        Label(telemetry_frame, text="SYSTEM: LOCAL_ONLY", fg="#FFD700", bg="#0D0F18", font=("Consolas", 8, "bold")).grid(row=0, column=3, padx=10, pady=5)

    # --- 3. CHAT AND INPUT FRAMES ---
    chat_frame = Frame(win, bg="#0B0D14")
    chat_frame.pack(fill="both", expand=True, padx=20, pady=15)

    chat = Text(chat_frame, bg="#10121B", fg="#E0E0E0", font=("Consolas", 11), 
                padx=15, pady=15, bd=0, highlightthickness=1, highlightbackground="#232738")
    chat.pack(side="left", fill="both", expand=True)
    
    chat.tag_config("user", foreground="#00D2FF", font=("Consolas", 11, "bold"))
    chat.tag_config("bot", foreground="#00FFC3", font=("Consolas", 11, "bold"))
    chat.config(state=DISABLED)

    status_var = StringVar(value="SYSTEM_READY")
    Label(win, textvariable=status_var, bg="#0B0D14", fg="#4B4F66", font=("Consolas", 8)).pack(anchor="w", padx=25)

    input_frame = Frame(win, bg="#0B0D14")
    input_frame.pack(fill="x", padx=20, pady=(0, 20))

    entry = Entry(input_frame, bg="#161925", fg="white", insertbackground="#00D2FF",
                  font=("Segoe UI", 12), bd=0, highlightthickness=1, highlightbackground="#2D3247")
    entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))
    entry.focus_set()

    voice_on = BooleanVar(value=True)

    # --- 4. ENGINE LOGIC ---
    def typewriter(text):
        chat.config(state=NORMAL)
        chat.insert(END, "FusionAI: ", "bot")
        chat.config(state=DISABLED)
        if voice_on.get():
            speak_via_queue(text) 

        def add_char(i=0):
            if i < len(text):
                chat.config(state=NORMAL)
                chat.insert(END, text[i])
                chat.config(state=DISABLED)
                chat.see(END)
                win.after(15, lambda: add_char(i + 1))
            else:
                chat.config(state=NORMAL)
                chat.insert(END, "\n\n")
                chat.config(state=DISABLED)
                status_var.set("SYSTEM_READY")
                entry.config(state=NORMAL)
                send_btn.config(state=NORMAL)
        add_char()

    def handle_send(e=None):
        msg = entry.get().strip()
        if not msg: return
        entry.delete(0, END)
        entry.config(state=DISABLED)
        send_btn.config(state=DISABLED)
        
        chat.config(state=NORMAL)
        chat.insert(END, "USER: ", "user")
        chat.insert(END, f"{msg}\n")
        chat.config(state=DISABLED)
        
        status_var.set("NEURAL_SYNCING...")
        
        def run_logic():
            reply = fusion_ai_online(msg) if mode == "online" else fusion_ai_offline(msg)
            win.after(0, lambda: typewriter(reply))
        
        threading.Thread(target=run_logic, daemon=True).start()

    # --- 5. BUTTONS ---
    send_btn = FusionButton(input_frame, text="EXECUTE", bg="#00D2FF", fg="#0B0D14", 
                           activebackground="#00FFC3", font=("Segoe UI", 9, "bold"), 
                           bd=0, width=12, command=handle_send)
    send_btn.pack(side="right", padx=2)

    def toggle_voice():
        voice_on.set(not voice_on.get())
        voice_btn.config(text="🔊 ON" if voice_on.get() else "🔇 OFF", 
                         bg="#3D99FF" if voice_on.get() else "#333842")

    voice_btn = FusionButton(input_frame, text="🔊 ON", bg="#3D99FF", fg="white",
                            activebackground="#00D2FF", font=("Segoe UI", 8, "bold"),
                            bd=0, width=8, command=toggle_voice)
    voice_btn.pack(side="right", padx=2)
    
    entry.bind("<Return>", handle_send)

# ---------- 3. MAIN LAUNCHER SETUP ----------
root = tk.Tk()
root.title("FusionAI Interface")
root.geometry("520x750")
root.configure(bg="#0B0D14")

selected_mode = StringVar(value="offline")

Label(root, text="FUSION_AI", fg="#00D2FF", bg="#0B0D14", font=("Impact", 38)).pack(pady=(30, 10))

def create_mode_section(title, val, color, features, disadvantages):
    frame = Frame(root, bg="#0B0D14", pady=10)
    frame.pack(fill="x", padx=40)
    
    Radiobutton(frame, text=title, variable=selected_mode, value=val, 
                bg="#0B0D14", fg=color, selectcolor="#0B0D14", 
                font=("Consolas", 14, "bold"), activebackground="#0B0D14").pack(anchor="w")
    
    # Feature/Disadvantage Section
    info_text = f"✔ {features}\n✖ {disadvantages}"
    Label(frame, text=info_text, fg="#636E72", bg="#0B0D14", font=("Segoe UI", 9), 
          justify="left", wraplength=400).pack(anchor="w", padx=30, pady=2)

create_mode_section(
    "OFFLINE_CORE", "offline", "#00FFC3", 
    "Infinite requests, zero latency, privacy focused.", 
    "Limited logic, no internet access, preset responses."
)

create_mode_section(
    "ONLINE_NEURAL", "online", "#3D99FF", 
    "Advanced reasoning, complex coding/math, global knowledge.", 
    "15 RPM limit, 30s cooldown (Free), requires stable connection."
)

btn_launch = FusionButton(root, text="INITIALIZE SYSTEM", bg="#00D2FF", fg="#0B0D14",
                         activebackground="#00FFC3", font=("Segoe UI", 12, "bold"),
                         bd=0, width=22, height=2, command=launch_ai)
btn_launch.pack(pady=40)

root.mainloop()
