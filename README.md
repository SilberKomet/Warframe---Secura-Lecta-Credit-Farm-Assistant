# Warframe Lecta Tracker (CPM/KPM/OCR)

A Python-based overlay and tracker for Warframe that monitors Credits Per Minute (CPM), Kills Per Minute (KPM), and other stats using OCR (Optical Character Recognition) and log reading.

## Features
- **Live Overlay:** Draggable stats (CPM, KPM, FPS) over the game.
- **Real-time Graphs:** Visualizes your farming efficiency.
- **OCR Tracking:** Reads credits/kills from the Mission Progress screen (Tab).
- **Log Tracking:** Reads `EE.log` for 100% accurate kill counts and spawn rates.
- **FPS Tracker:** Uses PresentMon for accurate frametime analysis.

---

## How to Download & Run

### Option 1: The Easy Way (Recommended)
**No installation required.**
1. Go to the Releases page.
2. Download the latest `.zip` file.
3. Extract it anywhere.
4. Run `Start_Tracker.bat`.

### Option 2: For Developers (Source Code)
If you have Python installed and want to run the raw scripts:

1. Clone this repository or download the Source Code zip.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the launcher:
   ```bash
   Start_Tracker.bat
   ```
   *(Or run `python CPM_OOP.py` directly)*

---

## Controls
| Key | Action |
| :--- | :--- |
| **F8** | Start Run Timer |
| **TAB** | Scan Credits (Open Mission Progress) |
| **F9** | Toggle Bounding Box Overlay |
| **F10** | Save Data & End Run |

## First Time Setup
1. When you first launch the tracker, it will ask you to select a folder to save your run data.
2. It will then launch the **Bounding Box Setup**.
3. Follow the on-screen instructions to draw boxes around the "Credits" text and the 5 possible credit values in the Mission Progress screen.

## Requirements
- Warframe must be running on the **Primary Monitor**.
- Interface Scale in Warframe should be consistent (default 100 recommended).
- **PresentMon.exe** must be in the folder for FPS tracking (included in releases).