# Yt-dlp-GUI-for-linux
This is Human written one. if my tutorial looks bad. scroall down to find AI written

simple yt-dlp GUI with python or you can use the compiled version. just select video and audio and it will merge it and download the video for you.
also you need to install ffmpeg and yt-dlp on your system before using that.
make sure by checkying
yt-dlp --version
ffmpeg -version
if answer comes then you are okay if not then install them. you can open issue tab if you want to know how to install them.
Also yes this is my first project and code is created by AI and verified by human. you can use the file with ./run.sh in the terminal. or you can use the compiled version (not sure if it works for everyone).
you can even compile it yourself it is really easy. first run ./run.sh. and let it run program for once.
step2. activate the venv first source venv/bin/activate.
step3. then install. pip install pyinstaller
step4. pyinstaller --onefile --windowed yt_dlp_gui.py
it will be located in dist/yt_dlp_gui. folder. just run it from there simple

This is AI written now.


# YT-DLP GUI for Linux

A simple **yt-dlp GUI built with Python**.
You can either run it from source or use the compiled version.

Just select the video and audio formats, and the app will merge and download the final video for you automatically.

---

## Requirements

Before using this app, make sure you have **yt-dlp** and **ffmpeg** installed on your system.

Check by running:

```bash
yt-dlp --version
ffmpeg -version
```

If both commands return a version number, you're good to go ✅
If not, please install them first. You can check the **Issues** tab for help on installation.

---

## Running from Source

You can run the app directly using:

```bash
./run.sh
```

---

## Compiled Version

There is also a compiled version available (not guaranteed to work on every system).

If it doesn’t work for you, you can easily build it yourself.

---

## How to Compile It Yourself

It’s very simple:

**Step 1:** Run the app once

```bash
./run.sh
```

**Step 2:** Activate the virtual environment

```bash
source venv/bin/activate
```

**Step 3:** Install PyInstaller

```bash
pip install pyinstaller
```

**Step 4:** Build the executable

```bash
pyinstaller --onefile --windowed yt_dlp_gui.py
```

After building, the executable will be located in:

```
dist/yt_dlp_gui
```

Just run it from there. That’s it 🎉

---

## Notes

* This is my first project.
* The code was initially generated with AI and then reviewed and verified by a human.
* Feedback and suggestions are welcome!

---
