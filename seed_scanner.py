import os
import re
import sys

def get_ee_log_path():
    # Standard location for Warframe EE.log
    return os.path.expandvars(r"%LOCALAPPDATA%\Warframe\EE.log")

def scan_and_save_seed():
    log_path = get_ee_log_path()
    
    # Setup output directory and file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    seeds_dir = os.path.join(base_dir, "MAP_SEEDS")
    os.makedirs(seeds_dir, exist_ok=True)
    seeds_file = os.path.join(seeds_dir, "seeds.txt")

    if not os.path.exists(log_path):
        print(f"Error: EE.log not found at {log_path}")
        return

    # Regex to capture the seed string before .lp
    # Example line: ... /Lotus/Levels/Proc/Grineer/GrineerGalleonSurvivalRaid/evCZiIESqzqvExnSJiYyND9q5H306pVXEAACEAABAAIAAAo.lp
    seed_pattern = re.compile(r"/Lotus/Levels/Proc/.*/(?P<seed>[^/]+)\.lp")
    
    last_seed = None

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = seed_pattern.search(line)
                if match:
                    last_seed = match.group("seed")
    except Exception as e:
        print(f"Error reading log: {e}")
        return

    if last_seed:
        print(f"Found seed: {last_seed}")
        
        try:
            with open(seeds_file, 'a') as f:
                f.write(last_seed + "\n")
            print(f"Seed appended to {seeds_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("No map seed found in EE.log.")

def main():
    print("--- Warframe Map Seed Scanner ---")
    while True:
        scan_and_save_seed()
        
        while True:
            user_input = input("scan again [y/n]: ").strip().lower()
            if user_input == 'y':
                break
            elif user_input == 'n':
                sys.exit()
            # If invalid input, loop asks again

if __name__ == "__main__":
    main()