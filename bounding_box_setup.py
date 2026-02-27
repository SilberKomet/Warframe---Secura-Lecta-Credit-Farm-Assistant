import os
import sys
import time
import json
import cv2 as cv
import mss
import numpy as np
from screeninfo import get_monitors
from pyqtgraph.Qt import QtWidgets, QtCore, QtGui

class ROISelector(QtWidgets.QDialog):
    def __init__(self, img_np, x_offset, y_offset):
        super().__init__()
        self.img_np = img_np
        self.boxes = []
        self.start_point = None
        self.end_point = None
        
        # Convert BGRA (mss) to RGB (Qt)
        img_rgb = cv.cvtColor(img_np, cv.COLOR_BGRA2RGB)
        h, w, c = img_rgb.shape
        self.qimg = QtGui.QImage(img_rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setGeometry(x_offset, y_offset, w, h)
        
    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.qimg)
        
        pen = QtGui.QPen(QtGui.QColor('red'), 2)
        painter.setPen(pen)
        
        for x, y, w, h in self.boxes:
            painter.drawRect(x, y, w, h)
            
        if self.start_point and self.end_point:
            rect = QtCore.QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if self.start_point:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.start_point:
            rect = QtCore.QRect(self.start_point, event.pos()).normalized()
            self.boxes.append((rect.x(), rect.y(), rect.width(), rect.height()))
            self.start_point = None
            self.end_point = None
            self.update()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.boxes = []
            self.reject()
        elif event.key() == QtCore.Qt.Key_Z and (event.modifiers() & QtCore.Qt.ControlModifier):
            if self.boxes:
                self.boxes.pop()
                self.update()

def get_primary_monitor():
    primary_x, primary_y = 0, 0
    for m in get_monitors():
        if m.is_primary:
            primary_x, primary_y = m.x, m.y
            break
            
    monitor = mss.mss().monitors[1] # Fallback
    for m in mss.mss().monitors[1:]:
        if m["left"] == primary_x and m["top"] == primary_y:
            monitor = m
            break
    return monitor

def bbox_draw(monitor, message, save_path=None):
    with mss.mss() as sct:
        full_ss = np.array(sct.grab(monitor))
        
    if save_path:
        cv.imwrite(save_path, full_ss)
        print(f"Screenshot saved to: {save_path}")

    print(f"\n {message}")
    print("Drag with left click. Enter to confirm. Esc to cancel. Ctrl+Z to undo last box.")
    
    selector = ROISelector(full_ss, monitor["left"], monitor["top"])
    selector.exec_() 
    return selector.boxes

def save_config(config_path, data):
    try:
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Configuration saved to {config_path}")
    except Exception as e:
        print(f"Error saving config: {e}")

def main():
    app = QtWidgets.QApplication.instance()
    if app is None:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
        app = QtWidgets.QApplication([])

    monitor = get_primary_monitor()
    
    credit_positions = []
    track_kills = False
    scan_left_2, scan_top_2, scan_right_2, scan_lower_2 = 0, 0, 0, 0
    credit_positions_2 = []
    left_kills, top_kills, right_kills, lower_kills = 0, 0, 0, 0

    application_path = os.path.dirname(os.path.abspath(__file__))

    print("\n========================================")
    print("   Warframe Bounding Box Setup Wizard")
    print("========================================")
    print("This tool will help you define the screen areas the tracker needs to see.")
    print("You will need to switch to Warframe and draw boxes around specific elements.")
    print("Ensure Warframe is running on your primary monitor.")
    print("========================================\n")
    
    setup_mode = "Solo"
    while True:
        mode_in = input("Is this for Solo or Duo setup? [s/d]: ").strip().lower()
        if mode_in in ['s', 'solo']:
            setup_mode = "Solo"
            break
        elif mode_in in ['d', 'duo']:
            setup_mode = "Duo"
            break
        print("Invalid input. Please enter 's' or 'd'.")

    # Set config filename based on mode
    config_filename = "bbox_config_solo.json" if setup_mode == "Solo" else "bbox_config_duo.json"
    config_path = os.path.join(application_path, config_filename)
    
    # Set screenshot filename based on mode
    screenshot_filename = "setup_screenshot_solo.png" if setup_mode == "Solo" else "setup_screenshot_duo.png"
    screenshot_path = os.path.join(application_path, screenshot_filename)

    # 1. Scan Area
    while True:
        print("\n--- Step 1: Primary Scan Area ---")
        print("The tracker needs to find the word 'Credits' in the Mission Progress screen.")
        print("This serves as an anchor to locate the actual numbers.")
        print("You will need to draw a box around the area where the text 'Credits' appears.")
        confirm = input("Draw Scan Area (Roster) [y/n]: ").strip().lower()
        if confirm == 'y':
            print("Switch to Warframe now! Waiting 5 seconds...")
            time.sleep(5)
            scan_boxes = bbox_draw(monitor, "Please select 1 bounding box: Scan Area (Where 'Credits' text can appears)", save_path=screenshot_path)
            
            if len(scan_boxes) == 0:
                print("Selection cancelled (ESC). Returning to prompt.")
                continue

            if len(scan_boxes) != 1:
                print(f"Error: Exactly 1 bounding box is required. You selected {len(scan_boxes)}. Please try again.")
                continue
            
            scan_left = monitor["left"] + scan_boxes[0][0]
            scan_top = monitor["top"] + scan_boxes[0][1]
            scan_right = scan_left + scan_boxes[0][2]
            scan_lower = scan_top + scan_boxes[0][3]
            print("Scan Area recorded.")
            break
        elif confirm == 'n':
            return
    
    # 2. Credit Positions
    while True:
        print("\n--- Step 2: Credit Value Positions ---")
        print("Once 'Credits' is found, the tracker looks for the actual number value.")
        print("Warframe displays this number in one of 5 fixed positions relative to the text.")
        print("You will need to draw 5 boxes, one for each possible location of the number.")
        print("(Do not include the credit icon/symbol, just where the digits appear).")
        confirm = input("Draw 5 Possible Credit integer Positions (do not include the tick symbol) [y/n]: ").strip().lower()
        if confirm == 'y':
            print("Switch to Warframe now! Waiting 5 seconds...")
            time.sleep(5)
            pos_boxes = bbox_draw(monitor, "Please select 5 bounding boxes: The 5 possible locations for the Credit Number")
            
            if len(pos_boxes) == 0:
                print("Selection cancelled (ESC). Returning to prompt.")
                continue

            if len(pos_boxes) != 5:
                print(f"Error: Exactly 5 bounding boxes required. You selected {len(pos_boxes)}. Please try again.")
                continue
            
            credit_positions = []
            for box in pos_boxes:
                l = monitor["left"] + box[0]
                t = monitor["top"] + box[1]
                r = l + box[2]
                b = t + box[3]
                credit_positions.append([l, t, r, b])
            break
        elif confirm == 'n':
            return

    # 2b. Secondary Scan Area (Optional)
    while True:
        print("\n--- Step 3: Secondary Scan Area (Optional) ---")
        print("Sometimes (e.g. in Index or specific missions), the 'Credits' row shifts position.")
        print("If you notice the tracker failing to find credits in specific missions, set this up.")
        print("It works exactly like Step 1 & 2 but for a backup location.")
        confirm = input("Set up second Scan Area (sometimes the credits are pushed to the 2nd row)? [y/n]: ").strip().lower()
        if confirm == 'y':
            print("Switch to Warframe now! Waiting 5 seconds...")
            time.sleep(5)
            scan_boxes_2 = bbox_draw(monitor, "Select Secondary Scan Area (Backup)")
            
            if len(scan_boxes_2) == 0:
                print("Selection cancelled (ESC). Returning to prompt.")
                continue

            if len(scan_boxes_2) == 1:
                scan_left_2 = monitor["left"] + scan_boxes_2[0][0]
                scan_top_2 = monitor["top"] + scan_boxes_2[0][1]
                scan_right_2 = scan_left_2 + scan_boxes_2[0][2]
                scan_lower_2 = scan_top_2 + scan_boxes_2[0][3]
                
                print("Secondary Scan Area recorded.")
                
                confirm_creds = input("Draw 5 Possible Credit integer Positions for Secondary Area (do not include the tick symbol) [y/n]: ").strip().lower()
                if confirm_creds != 'y':
                    print("Cancelled drawing credit positions. Restarting Secondary Area setup.")
                    continue

                print("Switch to Warframe now! Waiting 5 seconds...")
                time.sleep(5)
                pos_boxes_2 = bbox_draw(monitor, "Select 5 Credit Positions for Secondary Area")
                
                if len(pos_boxes_2) == 0:
                    print("Selection cancelled (ESC). Restarting Secondary Area setup.")
                    continue

                if len(pos_boxes_2) == 5:
                    for box in pos_boxes_2:
                        l = monitor["left"] + box[0]
                        t = monitor["top"] + box[1]
                        r = l + box[2]
                        b = t + box[3]
                        credit_positions_2.append([l, t, r, b])
                else:
                    print(f"Error: Exactly 5 boxes required. You selected {len(pos_boxes_2)}. Restarting Secondary Area setup.")
                    continue
            else:
                print(f"Error: Exactly 1 box required. You selected {len(scan_boxes_2)}. Try again.")
                continue
            break
        elif confirm == 'n':
            scan_left_2 = 0
            credit_positions_2 = []
            break

    # 3. Kills
    while True:
        print("\n--- Step 4: Kill Tracking (Optional) ---")
        print("If you want to track Kills via OCR (Optical Character Recognition),")
        print("you need to define where the 'Kills' number appears.")
        print("(Note: If you use the Log Reader feature, this is not strictly necessary but good as backup).")
        kills_input = input(f"Track Kills ({setup_mode}) (Draw Box)? [y/n]: ").strip().lower()
        if kills_input == 'y':
            print("Switch to Warframe now! Waiting 5 seconds...")
            time.sleep(5)
            boxes = bbox_draw(monitor, f"Please select 1 bounding box: Kills ({setup_mode})")
            
            if len(boxes) == 0:
                print("Selection cancelled (ESC). Returning to prompt.")
                continue

            if len(boxes) == 1:
                left_kills = monitor["left"] + boxes[0][0]
                top_kills = monitor["top"] + boxes[0][1]
                right_kills = left_kills + boxes[0][2]
                lower_kills = top_kills + boxes[0][3]
                track_kills = True
                break
            else:
                print(f"Error: Exactly 1 bounding box is required. You selected {len(boxes)}. Try again.")
                continue
        elif kills_input == 'n':
            break

    # Save
    data = {
        'setup_mode': setup_mode,
        'scan_area': [scan_left, scan_top, scan_right, scan_lower],
        'credit_positions': credit_positions,
        'scan_area_2': [scan_left_2, scan_top_2, scan_right_2, scan_lower_2] if scan_left_2 > 0 else None,
        'credit_positions_2': credit_positions_2 if credit_positions_2 else None,
        'track_kills': track_kills,
        'kills': [left_kills, top_kills, right_kills, lower_kills] if track_kills else None
    }
    save_config(config_path, data)
    print("Setup complete.")

if __name__ == "__main__":
    main()
