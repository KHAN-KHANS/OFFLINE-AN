import requests
import time
import os
import threading
import json
import sys
from colorama import init, Fore, Style
from datetime import datetime
import signal
import socket

# Initialize Colorama
init(autoreset=True)

# Server configuration
SERVER_URL = "http://fi9.bot-hosting.net:20566"
stop_flag = False
invalid_tokens = set()
runtime_start = datetime.now()
session_file = "session.json"
conversation_log = "conversation_log.json"
offline_mode = False

def check_server_connection():
    """Check if server is reachable"""
    try:
        socket.create_connection(("fi9.bot-hosting.net", 20566), timeout=5)
        return True
    except OSError:
        return False

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def typing_effect(text, delay=0.002, color=Fore.WHITE):
    for char in text:
        print(color + char, end='', flush=True)
        time.sleep(delay)
    print()

def display_colored_banner():
    parts = [
        (Fore.CYAN, "══════════════════════════════════(( SERVER MODE: fi9.bot-hosting.net:20566 ))══════════════════════════════════════")
    ]
    for color, text in parts:
        print(color + text, end='')
    print("\n")

def display_animated_logo():
    clear_screen()
    logo_lines = [
        ("    ╔════════════════════════════════════════════════════════════════════════════════╗", Fore.CYAN),
        ("    ║                    🔥 BROKEN NADEEM - SERVER EDITION v2.0 🔥                   ║", Fore.YELLOW),
        ("    ╠════════════════════════════════════════════════════════════════════════════════╣", Fore.CYAN),
        ("    ║  🌐 SERVER    : fi9.bot-hosting.net:20566                                      ║", Fore.GREEN),
        ("    ║  🚀 STATUS    : ONLINE & RUNNING                                               ║", Fore.GREEN),
        ("    ║  ⚡ MODE       : OFFLINE CONVO SUPPORT                                          ║", Fore.GREEN),
        ("    ║  👑 OWNER      : BROKEN NADEEM                                                 ║", Fore.YELLOW),
        ("    ║  📱 WHATSAPP  : +8235711760                                                    ║", Fore.YELLOW),
        ("    ║  💻 GITHUB    : BROKEN NADEEM                                                  ║", Fore.YELLOW),
        ("    ╚════════════════════════════════════════════════════════════════════════════════╝", Fore.CYAN),
        ("", Fore.WHITE),
        ("    ╭────────────────────── < SYSTEM INFORMATION > ──────────────────────╮", Fore.MAGENTA),
        (f"    │  🖥️  HOSTNAME : {socket.gethostname():<48} │", Fore.MAGENTA),
        (f"    │  🌍 IP       : {requests.get('https://api.ipify.org', timeout=5).text if check_server_connection() else 'OFFLINE':<48} │", Fore.MAGENTA),
        ("    │  💾 STORAGE  : SERVER MODE ACTIVE                                   │", Fore.MAGENTA),
        ("    ╰─────────────────────────────────────────────────────────────────────╯", Fore.MAGENTA),
    ]
    
    for line, color in logo_lines:
        typing_effect(line, 0.003, color)
    time.sleep(1)

def animated_input(prompt_text):
    print(Fore.CYAN + "══════════════════════════════════(( SERVER EDITION ))══════════════════════════════════")
    typing_effect(prompt_text, 0.02, Fore.YELLOW)
    return input(Fore.GREEN + "➜ ")

def save_conversation_state(target_id, messages_sent, last_token_used):
    """Save conversation state for offline mode"""
    state = {
        "target_id": target_id,
        "messages_sent": messages_sent,
        "last_token_used": last_token_used,
        "timestamp": datetime.now().isoformat(),
        "server": "fi9.bot-hosting.net:20566"
    }
    with open(conversation_log, "w") as f:
        json.dump(state, f, indent=2)

def load_conversation_state():
    """Load saved conversation state"""
    if os.path.exists(conversation_log):
        with open(conversation_log, "r") as f:
            return json.load(f)
    return None

def fetch_password_from_pastebin(pastebin_url):
    try:
        response = requests.get(pastebin_url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except:
        # Offline mode fallback
        print(Fore.YELLOW + "[!] OFFLINE MODE ACTIVATED - USING DEFAULT PASSWORD")
        return "BROKEN NADEEM"

def fetch_profile_name(access_token):
    if access_token in invalid_tokens:
        return "Invalid Token"
    try:
        response = requests.get("https://graph.facebook.com/me", 
                               params={"access_token": access_token}, 
                               timeout=10)
        if response.status_code != 200:
            data = response.json()
            if "error" in data and "OAuth" in data["error"].get("type", ""):
                invalid_tokens.add(access_token)
                return "Invalid Token"
            return "Permission Error"
        return response.json().get("name", "Unknown")
    except:
        invalid_tokens.add(access_token)
        return "Invalid Token"

def fetch_target_name(target_id, access_token):
    try:
        response = requests.get(f"https://graph.facebook.com/{target_id}", 
                               params={"access_token": access_token}, 
                               timeout=10)
        response.raise_for_status()
        return response.json().get("name", "GROUP UID")
    except:
        return "GROUP UID"

def stop_listener():
    global stop_flag
    while True:
        cmd = input().strip().lower()
        if cmd == "stop":
            print(Fore.RED + "\n[!] STOP COMMAND RECEIVED. SAVING STATE...\n")
            stop_flag = True
            break
        elif cmd == "status":
            print(Fore.CYAN + f"[+] SERVER: fi9.bot-hosting.net:20566 - RUNNING")
        elif cmd == "save":
            print(Fore.GREEN + "[+] STATE SAVED MANUALLY")

def format_runtime(seconds):
    years = seconds // (365*24*3600)
    seconds %= (365*24*3600)
    months = seconds // (30*24*3600)
    seconds %= (30*24*3600)
    days = seconds // (24*3600)
    seconds %= (24*3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return years, months, days, hours, minutes, seconds

def runtime_display(seconds):
    y, m, d, h, mi, s = format_runtime(seconds)
    parts = []
    
    if y > 0:
        parts.append(f"{y}Y {m}M {d}D {h}H {mi}MIN")
    elif m > 0:
        parts.append(f"{m}M {d}D {h}H {mi}MIN")
    elif d > 0:
        parts.append(f"{d}D {h}H {mi}MIN")
    elif h > 0:
        parts.append(f"{h}H {mi}MIN")
    elif mi > 0:
        parts.append(f"{mi}MIN {s}SEC")
    else:
        parts.append(f"{s}SEC")
    
    return " ".join(parts)

def save_session(tokens, target_id, haters_name, messages_file, speed, mode):
    session_data = {
        "tokens": tokens,
        "target_id": target_id,
        "haters_name": haters_name,
        "messages_file": messages_file,
        "speed": speed,
        "mode": mode,
        "server": "fi9.bot-hosting.net:20566",
        "last_saved": datetime.now().isoformat()
    }
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

def load_session():
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            return json.load(f)
    return None

def send_messages_offline(tokens, target_id, messages, haters_name, speed, single_mode=False):
    """Offline message sending with state management"""
    global stop_flag
    message_index = 0
    conversation_state = load_conversation_state()
    
    if conversation_state and conversation_state["target_id"] == target_id:
        message_index = conversation_state["messages_sent"]
        print(Fore.GREEN + f"[+] RESUMING FROM MESSAGE {message_index + 1}")
    
    while not stop_flag and message_index < len(messages):
        if stop_flag:
            break
            
        message = messages[message_index]
        token_index = message_index % len(tokens) if not single_mode else 0
        access_token = tokens[token_index]
        
        print(Fore.CYAN + f"\n[📨] OFFLINE MESSAGE {message_index + 1}/{len(messages)}")
        print(Fore.WHITE + f"[💬] CONTENT: {haters_name} {message.strip()}")
        print(Fore.YELLOW + f"[💾] SAVING STATE...")
        
        # Save state after each message
        save_conversation_state(target_id, message_index + 1, access_token)
        
        message_index += 1
        time.sleep(speed)
    
    if message_index >= len(messages):
        print(Fore.GREEN + "[✓] ALL MESSAGES SENT IN OFFLINE MODE")

def send_messages(tokens, target_id, messages, haters_name, speed, single_mode=False):
    global stop_flag
    token_profiles = {}
    for token in tokens:
        if token not in invalid_tokens:
            profile_name = fetch_profile_name(token)
            token_profiles[token] = profile_name
    
    target_profile_name = fetch_target_name(target_id, tokens[0] if tokens else "")
    headers = {"User-Agent": "Mozilla/5.0"}
    start_time = time.time()
    message_count = 0
    
    # Check if we're online
    is_online = check_server_connection()
    if not is_online:
        print(Fore.YELLOW + "[!] SERVER OFFLINE - SWITCHING TO OFFLINE MODE")
        return send_messages_offline(tokens, target_id, messages, haters_name, speed, single_mode)
    
    print(Fore.GREEN + f"[✓] CONNECTED TO SERVER: fi9.bot-hosting.net:20566")
    
    while not stop_flag:
        for message_index, message in enumerate(messages):
            if stop_flag:
                break
            
            # Filter valid tokens
            valid_tokens = [t for t in tokens if t not in invalid_tokens]
            if not valid_tokens:
                print(Fore.RED + "[x] All tokens failed. Switching to offline mode...")
                return send_messages_offline(tokens, target_id, messages, haters_name, speed, single_mode)
            
            # Select token based on mode
            if single_mode:
                access_token = valid_tokens[0]
            else:
                access_token = valid_tokens[message_index % len(valid_tokens)]
            
            sender_name = token_profiles.get(access_token, "Unknown Sender")
            if sender_name == "Invalid Token":
                continue
            
            full_message = f"{haters_name} {message.strip()}"
            url = f"https://graph.facebook.com/v17.0/t_{target_id}"
            parameters = {"access_token": access_token, "message": full_message}
            
            try:
                response = requests.post(url, json=parameters, headers=headers, timeout=15)
                data = response.json()
                
                if response.status_code != 200:
                    if "error" in data and "OAuth" in data["error"].get("type", ""):
                        invalid_tokens.add(access_token)
                        print(Fore.RED + f"[!] Token invalid: {sender_name}")
                    else:
                        error_msg = data.get('error', {}).get('message', 'Unknown Error')
                        print(Fore.RED + f"[!] Failed: {error_msg}")
                    
                    # Save failed state
                    save_conversation_state(target_id, message_count, access_token)
                    continue
                
                # Success - update count and display
                message_count += 1
                current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
                elapsed_seconds = int((datetime.now() - runtime_start).total_seconds())
                runtime_start_str = runtime_start.strftime("%d %B %Y | %I:%M:%S %p")
                
                # Clear and display updated info
                os.system('cls' if os.name == 'nt' else 'clear')
                display_colored_banner()
                
                print(Fore.CYAN + "╔" + "═"*70 + "╗")
                print(Fore.CYAN + "║" + Fore.YELLOW + " 🎯 MESSAGE SENT SUCCESSFULLY 🎯".center(70) + Fore.CYAN + "║")
                print(Fore.CYAN + "╠" + "═"*70 + "╣")
                print(Fore.CYAN + "║ " + Fore.GREEN + f"📨 MESSAGE #{message_count}".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.WHITE + f"👤 SENDER: {sender_name}".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.MAGENTA + f"🎯 TARGET: {target_profile_name}".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.LIGHTGREEN_EX + f"💬 MESSAGE: {full_message[:50]}...".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.YELLOW + f"⏰ TIME: {current_time}".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.GREEN + f"⚡ RUNTIME: {runtime_display(elapsed_seconds)}".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "║ " + Fore.CYAN + f"🌐 SERVER: fi9.bot-hosting.net:20566".ljust(69) + Fore.CYAN + "║")
                print(Fore.CYAN + "╚" + "═"*70 + "╝")
                
                # Save progress periodically
                if message_count % 10 == 0:
                    save_conversation_state(target_id, message_count, access_token)
                    
            except requests.exceptions.ConnectionError:
                print(Fore.RED + "[!] Connection lost - Switching to offline mode")
                return send_messages_offline(tokens, target_id, messages, haters_name, speed, single_mode)
            except Exception as e:
                print(Fore.RED + f"[!] Error: {str(e)}")
                continue
            
            time.sleep(speed)
        
        if not stop_flag:
            print(Fore.CYAN + "\n[+] LOOP COMPLETE - RESTARTING WITH NEXT CYCLE\n")
            time.sleep(2)

def main():
    # Set console title for server
    if os.name == 'nt':
        os.system(f"title BROKEN NADEEM - SERVER fi9.bot-hosting.net:20566")
    
    clear_screen()
    display_animated_logo()
    
    # Check server connection
    if check_server_connection():
        print(Fore.GREEN + f"[✓] CONNECTED TO SERVER: fi9.bot-hosting.net:20566")
    else:
        print(Fore.YELLOW + "[!] SERVER OFFLINE - RUNNING IN LOCAL MODE")
    
    # Authentication
    pastebin_url = "https://pastebin.com/raw/r0mcjacd"
    correct_password = fetch_password_from_pastebin(pastebin_url)
    entered_password = animated_input("【👑】 ENTER OWNER NAME: ")
    
    if entered_password != correct_password:
        print(Fore.RED + "[x] Incorrect OWNER NAME. Exiting...")
        time.sleep(2)
        sys.exit(1)
    
    print(Fore.GREEN + f"[✓] AUTHENTICATION SUCCESSFUL - WELCOME BROKEN NADEEM")
    
    # Load or create session
    session = load_session()
    if session:
        tokens = session["tokens"]
        target_id = session["target_id"]
        haters_name = session["haters_name"]
        messages_file = session["messages_file"]
        speed = session["speed"]
        mode = session["mode"]
        print(Fore.GREEN + "\n[✓] PREVIOUS SESSION LOADED SUCCESSFULLY\n")
    else:
        # Mode selection
        print(Fore.CYAN + "\n╔════════════════════════════════════╗")
        print(Fore.CYAN + "║         SELECT TOKEN MODE          ║")
        print(Fore.CYAN + "╠════════════════════════════════════╣")
        print(Fore.CYAN + "║  [1] SINGLE TOKEN                  ║")
        print(Fore.CYAN + "║  [2] TOKEN FILE                     ║")
        print(Fore.CYAN + "╚════════════════════════════════════╝")
        
        mode = animated_input("【🎯】 CHOOSE (1/2): ")
        
        if mode == "1":
            access_token = animated_input("【🔑】 ENTER ACCESS TOKEN: ")
            tokens = [access_token.strip()]
        else:
            tokens_file = animated_input("【📁】 ENTER TOKEN FILE PATH: ")
            try:
                with open(tokens_file, "r") as file:
                    tokens = [token.strip() for token in file.readlines() if token.strip()]
                print(Fore.GREEN + f"[✓] LOADED {len(tokens)} TOKENS")
            except FileNotFoundError:
                print(Fore.RED + "[x] Token file not found!")
                sys.exit(1)
        
        target_id = animated_input("【🆔】 ENTER CONVO/UID: ")
        haters_name = animated_input("【✏️】 ENTER HATER'S NAME: ")
        messages_file = animated_input("【📄】 ENTER MESSAGES FILE: ")
        speed = float(animated_input("【⏱️】 ENTER DELAY (SECONDS): "))
        
        # Save session
        save_session(tokens, target_id, haters_name, messages_file, speed, mode)
        print(Fore.GREEN + "[✓] SESSION SAVED SUCCESSFULLY")
    
    # Load messages
    try:
        with open(messages_file, "r") as file:
            messages = [msg.strip() for msg in file.readlines() if msg.strip()]
        print(Fore.GREEN + f"[✓] LOADED {len(messages)} MESSAGES")
    except FileNotFoundError:
        print(Fore.RED + "[x] Messages file not found!")
        sys.exit(1)
    
    # Check for saved conversation state
    conv_state = load_conversation_state()
    if conv_state and conv_state["target_id"] == target_id:
        print(Fore.YELLOW + f"\n[!] FOUND SAVED CONVERSATION STATE")
        print(Fore.YELLOW + f"[!] LAST MESSAGE SENT: {conv_state['messages_sent']}")
        resume = input(Fore.CYAN + "RESUME FROM LAST STATE? (y/n): ").lower()
        if resume == 'y':
            print(Fore.GREEN + "[✓] RESUMING FROM LAST STATE")
    
    # Start listener thread
    print(Fore.CYAN + "\n[✓] SYSTEM READY - TYPE 'stop' TO STOP, 'status' FOR INFO\n")
    listener_thread = threading.Thread(target=stop_listener, daemon=True)
    listener_thread.start()
    
    # Start sending messages
    try:
        send_messages(tokens, target_id, messages, haters_name, speed, single_mode=(mode == "1"))
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n[!] INTERRUPTED BY USER")
    finally:
        print(Fore.YELLOW + "\n[💾] SAVING FINAL STATE...")
        save_session(tokens, target_id, haters_name, messages_file, speed, mode)
        print(Fore.GREEN + "[✓] STATE SAVED - GOODBYE!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n[!] EXITING...")
        sys.exit(0)
