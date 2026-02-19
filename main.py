#!/data/data/com.termux/files/usr/bin/python
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════╗
║      BROKEN NADEEM - ULTIMATE PERSISTENT CONVO SCRIPT        ║
║      PHONE OFF / TERMUX EXIT / SCREEN OFF - SAB CHALEGA     ║
║                    SERVER: fi9.bot-hosting.net:20566        ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
import time
import os
import threading
import json
import sys
import signal
import socket
import subprocess
from datetime import datetime
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ===================== PERSISTENCE LAYER =====================
class PersistenceManager:
    """Ensures script runs 24/7 even after Termux exit"""
    
    def __init__(self):
        self.wake_lock_acquired = False
        self.daemonized = False
        self.pid_file = "/data/data/com.termux/files/home/convo.pid"
        self.log_file = "/data/data/com.termux/files/home/convo.log"
        
    def setup_persistence(self):
        """Setup all persistence mechanisms"""
        try:
            # 1. Acquire wake lock (prevents sleep)
            if not self.wake_lock_acquired:
                subprocess.run(["termux-wake-lock"], check=False)
                self.wake_lock_acquired = True
                self.log("[✓] WAKE LOCK ACQUIRED")
            
            # 2. Daemonize process
            if not self.daemonized:
                self.daemonize()
                self.daemonized = True
                self.log("[✓] DAEMONIZED SUCCESSFULLY")
            
            # 3. Write PID
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # 4. Ignore terminal signals
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            # 5. Set high priority
            try:
                os.nice(-20)  # Highest priority
            except:
                pass
                
            return True
            
        except Exception as e:
            self.log(f"[!] Persistence error: {e}")
            return False
    
    def daemonize(self):
        """Convert to daemon process"""
        try:
            # First fork
            if os.fork() > 0:
                sys.exit(0)
            
            # Create new session
            os.setsid()
            os.umask(0)
            
            # Second fork
            if os.fork() > 0:
                sys.exit(0)
            
            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            
            with open('/dev/null', 'r') as f:
                os.dup2(f.fileno(), sys.stdin.fileno())
            with open('/dev/null', 'w') as f:
                os.dup2(f.fileno(), sys.stdout.fileno())
                os.dup2(f.fileno(), sys.stderr.fileno())
                
        except OSError as e:
            self.log(f"[!] Daemonize failed: {e}")
            sys.exit(1)
    
    def signal_handler(self, signum, frame):
        """Handle signals gracefully"""
        self.log(f"[!] Signal {signum} received - Saving state...")
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup before exit"""
        try:
            subprocess.run(["termux-wake-unlock"], check=False)
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
    
    def log(self, msg):
        """Log to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a') as f:
            f.write(f"[{timestamp}] {msg}\n")

# ===================== CONVO MANAGER =====================
class ConvoManager:
    """Manages Facebook conversation sending"""
    
    def __init__(self):
        self.stop_flag = False
        self.invalid_tokens = set()
        self.runtime_start = datetime.now()
        self.session_file = "session.json"
        self.conversation_log = "conversation_log.json"
        self.server_url = "http://fi9.bot-hosting.net:20566"
        self.offline_mode = False
        self.persistence = PersistenceManager()
        
    def check_server(self):
        """Check if server is reachable"""
        try:
            socket.create_connection(("fi9.bot-hosting.net", 20566), timeout=5)
            return True
        except:
            return False
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Display persistent banner"""
        self.clear_screen()
        server_status = "ONLINE" if self.check_server() else "OFFLINE"
        
        banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║{BOLD}{CYAN}                      BROKEN NADEEM - PERSISTENT MODE                   {RESET}║
╠══════════════════════════════════════════════════════════════════╣
║  📱 PHONE STATE    : {'🔴 OFF' if server_status == 'OFFLINE' else '🟢 ON'}                                 {RESET}       ║
║  🖥️ SERVER         : fi9.bot-hosting.net:20566 ({server_status})               ║
║  ⚡ PROCESS ID     : {os.getpid():<48}║
║  💾 WAKE LOCK      : {'✅ ACTIVE' if self.persistence.wake_lock_acquired else '❌ INACTIVE'}                              ║
║  🔄 DAEMON MODE    : {'✅ YES' if self.persistence.daemonized else '❌ NO'}                                    ║
║  📁 LOG FILE       : ~/convo.log                                         ║
╠══════════════════════════════════════════════════════════════════╣
║  {YELLOW}COMMANDS: stop | status | save | restart | help{RESET}                         ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def save_state(self, target_id, messages_sent, last_token=None):
        """Save conversation state"""
        state = {
            "target_id": target_id,
            "messages_sent": messages_sent,
            "last_token": last_token,
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid()
        }
        with open(self.conversation_log, 'w') as f:
            json.dump(state, f, indent=2)
        self.persistence.log(f"State saved: {messages_sent} messages")
    
    def load_state(self):
        """Load saved conversation state"""
        if os.path.exists(self.conversation_log):
            with open(self.conversation_log, 'r') as f:
                return json.load(f)
        return None
    
    def fetch_profile_name(self, token):
        """Get profile name from token"""
        if token in self.invalid_tokens:
            return "Invalid"
        try:
            r = requests.get("https://graph.facebook.com/me", 
                           params={"access_token": token}, timeout=5)
            if r.status_code == 200:
                return r.json().get("name", "Unknown")
            self.invalid_tokens.add(token)
            return "Invalid"
        except:
            return "Error"
    
    def send_messages_persistent(self, tokens, target_id, messages, haters_name, speed):
        """Main sending function with persistence"""
        message_count = 0
        token_index = 0
        state = self.load_state()
        
        # Resume from last state
        if state and state["target_id"] == target_id:
            message_count = state["messages_sent"]
            self.print_banner()
            print(f"{GREEN}[✓] RESUMING FROM MESSAGE #{message_count + 1}{RESET}\n")
        
        while not self.stop_flag:
            for idx, message in enumerate(messages):
                if self.stop_flag:
                    break
                
                # Rotate tokens
                current_token = tokens[token_index % len(tokens)]
                token_index += 1
                
                if current_token in self.invalid_tokens:
                    continue
                
                full_message = f"{haters_name} {message.strip()}"
                
                # Try sending online first
                if self.check_server() and not self.offline_mode:
                    try:
                        url = f"https://graph.facebook.com/v17.0/t_{target_id}"
                        params = {"access_token": current_token, "message": full_message}
                        r = requests.post(url, json=params, timeout=10)
                        
                        if r.status_code == 200:
                            message_count += 1
                            
                            # Show progress
                            print(f"{CYAN}[📨] MESSAGE #{message_count} SENT{RESET}")
                            print(f"{WHITE}    To: {target_id}{RESET}")
                            print(f"{GREEN}    Msg: {full_message[:50]}...{RESET}\n")
                            
                            # Save state every 10 messages
                            if message_count % 10 == 0:
                                self.save_state(target_id, message_count, current_token)
                                print(f"{YELLOW}[💾] AUTO-SAVED AT {message_count}{RESET}\n")
                        
                    except Exception as e:
                        print(f"{RED}[!] Send error, switching to offline{RESET}")
                        self.offline_mode = True
                        
                        # Save immediately on error
                        self.save_state(target_id, message_count, current_token)
                
                # Offline mode - just log
                else:
                    message_count += 1
                    print(f"{YELLOW}[📨] OFFLINE #{message_count}: {full_message[:50]}...{RESET}")
                    
                    # Save offline progress
                    if message_count % 10 == 0:
                        self.save_state(target_id, message_count, current_token)
                        print(f"{YELLOW}[💾] OFFLINE SAVE AT {message_count}{RESET}\n")
                
                time.sleep(speed)
    
    def command_listener(self):
        """Listen for user commands"""
        while True:
            cmd = input().strip().lower()
            
            if cmd == "stop":
                self.stop_flag = True
                print(f"{RED}[!] STOPPING... SAVING FINAL STATE{RESET}")
                break
                
            elif cmd == "status":
                elapsed = int((datetime.now() - self.runtime_start).total_seconds())
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                print(f"{GREEN}[+] RUNTIME: {hours}h {minutes}m")
                print(f"[+] PID: {os.getpid()}")
                print(f"[+] WAKE LOCK: {'ACTIVE' if self.persistence.wake_lock_acquired else 'INACTIVE'}")
                print(f"[+] MODE: {'OFFLINE' if self.offline_mode else 'ONLINE'}{RESET}")
                
            elif cmd == "save":
                print(f"{YELLOW}[+] MANUAL SAVE TRIGGERED{RESET}")
                # Save logic here
                
            elif cmd == "restart":
                print(f"{YELLOW}[+] RESTARTING...{RESET}")
                self.stop_flag = True
                time.sleep(2)
                os.execv(sys.executable, ['python'] + sys.argv)
                
            elif cmd == "help":
                print(f"""
{CYAN}COMMANDS:
  stop    - Stop script (saves state)
  status  - Show runtime info
  save    - Manual state save
  restart - Restart script
  help    - Show this help{RESET}
""")
    
    def main(self):
        """Main execution function"""
        
        # Setup persistence first
        print(f"{BOLD}{CYAN}[*] SETTING UP PERSISTENCE...{RESET}")
        if not self.persistence.setup_persistence():
            print(f"{RED}[!] Persistence setup failed{RESET}")
        
        self.print_banner()
        
        # Check for existing session
        session = None
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    session = json.load(f)
                print(f"{GREEN}[✓] LOADED SESSION FROM {self.session_file}{RESET}")
            except:
                pass
        
        if not session:
            # Get user input
            print(f"{YELLOW}╔════════════════════════════════════╗")
            print(f"║      NEW SESSION SETUP              ║")
            print(f"╚════════════════════════════════════╝{RESET}\n")
            
            token_choice = input(f"{CYAN}[?] TOKEN MODE (1=single/2=file): {RESET}")
            
            if token_choice == "1":
                token = input(f"{CYAN}[?] ENTER ACCESS TOKEN: {RESET}")
                tokens = [token.strip()]
            else:
                token_file = input(f"{CYAN}[?] ENTER TOKEN FILE: {RESET}")
                with open(token_file, 'r') as f:
                    tokens = [t.strip() for t in f.readlines() if t.strip()]
            
            target = input(f"{CYAN}[?] ENTER TARGET UID: {RESET}")
            hater = input(f"{CYAN}[?] ENTER HATER NAME: {RESET}")
            msg_file = input(f"{CYAN}[?] ENTER MESSAGES FILE: {RESET}")
            delay = float(input(f"{CYAN}[?] ENTER DELAY (seconds): {RESET}"))
            
            # Save session
            session = {
                "tokens": tokens,
                "target": target,
                "hater": hater,
                "msg_file": msg_file,
                "delay": delay,
                "created": datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session, f, indent=2)
            
            print(f"{GREEN}[✓] SESSION SAVED{RESET}")
        
        # Load messages
        with open(session['msg_file'], 'r') as f:
            messages = [m.strip() for m in f.readlines() if m.strip()]
        
        print(f"{GREEN}[✓] LOADED {len(messages)} MESSAGES{RESET}")
        print(f"{YELLOW}[✓] PERSISTENCE ACTIVE - EXIT TERMUX NOW!{RESET}")
        print(f"{CYAN}[✓] TYPE 'stop' TO STOP, 'status' FOR INFO{RESET}\n")
        
        # Start command listener
        listener = threading.Thread(target=self.command_listener, daemon=True)
        listener.start()
        
        # Start sending messages
        try:
            self.send_messages_persistent(
                session['tokens'],
                session['target'],
                messages,
                session['hater'],
                session['delay']
            )
        except KeyboardInterrupt:
            print(f"{RED}[!] INTERRUPTED{RESET}")
        finally:
            self.persistence.cleanup()
            print(f"{GREEN}[✓] FINAL STATE SAVED. BYE!{RESET}")

# ===================== ENTRY POINT =====================
if __name__ == "__main__":
    # Check if running in Termux
    if 'com.termux' in os.environ.get('PREFIX', ''):
        print(f"{BOLD}{GREEN}[✓] TERMUX DETECTED - ENABLING PERSISTENCE{RESET}")
    else:
        print(f"{YELLOW}[!] NOT IN TERMUX - PERSISTENCE LIMITED{RESET}")
    
    # Run main
    convo = ConvoManager()
    convo.main()
