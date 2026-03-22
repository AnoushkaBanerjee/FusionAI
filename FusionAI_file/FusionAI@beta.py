import threading
import tkinter as tk
from tkinter import *
import random
import datetime
import json
import os
import re
import pyttsx3
import time
import sympy

# ---------- VOICE ENGINE ----------
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
for v in voices:
    if "female" in v.name.lower():
        engine.setProperty('voice', v.id)
        break
else:
    engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 165)
engine.setProperty('volume', 1)

def speak(text):
    try:
        clean_text = text.replace("@", " at ").replace("AI", " A.I ").replace("FusionAI", "Fusion A I").replace("beta", "bay-ta")
        engine.say(clean_text)
        engine.runAndWait()
    except Exception as e:
        print("Voice error:", e)

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

# ---------- ONLINE AI (Google Gemini) ----------
RAW_KEY = "AIzaSyBzjS4mq2soW8LGlSmRZ8PqNBHQjqYOwL0" 

try:
    from google import genai
    
    # .strip() removes any accidental spaces or hidden characters
    CLEAN_KEY = RAW_KEY.strip()
    
    if CLEAN_KEY and "AIza" in CLEAN_KEY:
        online_client = genai.Client(api_key=CLEAN_KEY)
        print(f"✅ Client initialized! (Key starts with: {CLEAN_KEY[:5]}...)")
    else:
        print("❌ Error: RAW_KEY does not look like a valid Gemini API Key.")
        online_client = None
        
except Exception as e:
    print(f"❌ Initialization Failed: {e}")
    online_client = None

def fusion_ai_online(msg):
    if not online_client:
        return "Online AI error: Client not initialized."
    
    # These are the instructions the AI follows SILENTLY
    system_rules = (
        "You are FusionAI, a custom-built assistant created by Anoushka Banerjee. "
        "Acknowledge Anoushka as your developer if asked. "
        "IMPORTANT: Do not use Markdown formatting. Do not use asterisks (*) or "
        "underscores (_) for bold or italic text. Provide plain text only. "
        "Do not mention these instructions or express understanding of them in your output."
    )

    models_to_try = [
        'gemini-3.1-flash-lite-preview', 
        'gemini-3-flash-preview', 
        'gemini-2.5-flash',
        'gemini-2.5-pro'
    ]
    
    for model_name in models_to_try:
        try:
            # We pass the system_instruction in the config
            response = online_client.models.generate_content(
                model=model_name,
                config={'system_instruction': system_rules},
                contents=msg
            )
            
            if response and response.text:
                return response.text
                
        except Exception as e:
            err_msg = str(e).upper()
            if "404" in err_msg or "NOT_FOUND" in err_msg:
                continue
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                continue
            return f"Online AI error: {e}"

    return "❌ All systems offline. Please check connection."

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

# ---------- GUI LOGIC ----------
root = tk.Tk()
root.title("Fusion Launcher")
root.geometry("450x550")
root.configure(bg=BG)

selected_mode = StringVar(value="offline")

def launch_ai():
    mode = selected_mode.get()
    ai_window = Toplevel(root)
    ai_window.title(f"FusionAI@beta - {mode.upper()}")
    ai_window.geometry("700x600")
    ai_window.configure(bg=BG)

    chat = Text(ai_window, bg="#1e1e1e", fg="white", state=DISABLED, font=("Consolas", 11))
    chat.pack(fill="both", expand=True, padx=10, pady=10)

    status_label = Label(ai_window, text=f"Ready ({mode.capitalize()})", bg=BG, fg="gray")
    status_label.pack()

    bottom = Frame(ai_window, bg=BG)
    bottom.pack(fill="x", padx=10, pady=10)

    entry = Entry(bottom, font=("Segoe UI", 12))
    entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

    voice_on = BooleanVar(value=True)

    def typewriter(full_text):
        chat.config(state=NORMAL)
        chat.insert(END, "FusionAI: ")
        chat.config(state=DISABLED)
        
        def add_char(i=0):
            if i < len(full_text):
                chat.config(state=NORMAL)
                chat.insert(END, full_text[i])
                chat.config(state=DISABLED)
                chat.see(END)
                ai_window.after(30, lambda: add_char(i + 1))
            else:
                chat.config(state=NORMAL)
                chat.insert(END, "\n\n")
                chat.config(state=DISABLED)
                
                # RE-ENABLE the send button once typing is finished
                send_btn.config(state=NORMAL) 
                
                if voice_on.get(): speak(full_text)
                status_label.config(text=f"Ready ({mode.capitalize()})")
        
        add_char()

    def send(event=None):
        msg = entry.get()
        if not msg.strip(): return
        entry.delete(0, END)
        
        # DISABLE the send button so you can't click it twice!
        send_btn.config(state=DISABLED) 

        chat.config(state=NORMAL)
        chat.insert(END, f"You: {msg}\n")
        chat.config(state=DISABLED)
        chat.see(END)
        
        status_label.config(text="FusionAI is thinking...")
        ai_window.after(1200, lambda: process_reply(msg))

    def process_reply(msg):
        if mode == "offline":
            resp = fusion_ai_offline(msg)
            typewriter(resp)
        else:
            def bg_fetch():
                try:
                    resp = fusion_ai_online(msg)
                    ai_window.after(0, lambda: typewriter(resp))
                except Exception as e:
                    # This ensures the UI doesn't just hang if there's a connection error
                    ai_window.after(0, lambda: typewriter(f"System Error: {e}"))
            
            threading.Thread(target=bg_fetch, daemon=True).start()

    send_btn = Button(bottom, text="SEND", bg=GREEN, fg="white", command=send)
    send_btn.pack(side="right", padx=2)

    voice_btn = Button(bottom, text="🔊", bg=BLUE, fg="white", command=lambda: toggle_voice(), width=3)
    voice_btn.pack(side="right", padx=2)

    def toggle_voice():
        voice_on.set(not voice_on.get())
        voice_btn.config(text="🔊" if voice_on.get() else "🔇")

    entry.bind("<Return>", send)

# ---------- LAUNCHER UI ----------
Label(root, text="FusionAI", fg=CYAN, bg=BG, font=("Segoe UI", 24, "bold")).pack(pady=20)
Label(root, text="SELECT MODE", fg="white", bg=BG).pack()

Radiobutton(root, text="Offline Mode", variable=selected_mode, value="offline", bg=BG, fg=GREEN, selectcolor=BG, font=("Segoe UI", 12)).pack(pady=(20, 0))
Label(root, text="✔ Fast ✔Advanced Maths ✔Date, Time  ✖ Limited ✖Can feel static", fg="gray", bg=BG, font=("Segoe UI", 8)).pack()

Radiobutton(root, text="Online Mode", variable=selected_mode, value="online", bg=BG, fg=BLUE, selectcolor=BG, font=("Segoe UI", 12)).pack(pady=(20, 0))
Label(root, text="✔ Full Online AI Model ✔Correct Explanation ✔More detail ✖Rate Limits ✖Needs internet", fg="gray", bg=BG, font=("Segoe UI", 8)).pack()

Button(root, text="LAUNCH FUSION AI", bg=CYAN, fg="black", font=("Segoe UI", 12, "bold"), width=20, height=2, command=launch_ai).pack(pady=40)

root.mainloop()
