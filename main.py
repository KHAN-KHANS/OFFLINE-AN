#!/data/data/com.termux/files/usr/bin/python
# -*- coding: utf-8 -*-

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

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'

class PersistenceManager:
    def __init__(self):
        self.wake_lock_acquired = False
        self.daemonized = False
        self.pid_file = "/data/data/com.termux/files/home/convo.pid"
        self.log_file = "/data/data/com.termux/files/home/convo.log"
        
    def setup_persistence(self):
        """Setup with error handling"""
        try:
            # 1. Try wake lock with timeout
            try:
                result = subprocess.run(
                    ["termux-wake-lock"], 
                    timeout=5,  # Timeout add kiya
                    capture_output=True,
                    check=False
                )
                if result.returncode == 0:
                    self.wake_lock_acquired = True
                    print(f"{GREEN}[✓] WAKE LOCK ACQUIRED{RESET}")
                else:
                    print(f"{YELLOW}[!] WAKE LOCK FAILED (permission?): {result.stderr}{RESET}")
            except subprocess.TimeoutExpired:
                print(f"{YELLOW}[!] WAKE LOCK TIMEOUT - continuing without{RESET}")
            except FileNotFoundError:
                print(f"{YELLOW}[!] termux-api not installed - continuing{RESET}")
            
            # 2. Background mode (simple approach)
            if not self.daemonized and os.fork() == 0:
                # Child process
                os.setsid()
                os.umask(0)
                
                # Close fds
                for fd in range(3):
                    try:
                        os.close(fd)
                    except:
                        pass
                
                self.daemonized = True
                
            # 3. Write PID
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            # 4. Ignore hangup signal
            signal.signal(signal.SIGHUP, signal.SIG_IGN)
            
            return True
            
        except Exception as e:
            print(f"{RED}[!] Persistence error: {e}{RESET}")
            return False
    
    def cleanup(self):
        try:
            subprocess.run(["termux-wake-unlock"], timeout=2, check=False)
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass

class ConvoManager:
    def __init__(self):
        self.stop_flag = False
        self.invalid_tokens = set()
        self.runtime_start = datetime.now()
        self.session_file = "session.json"
        self.conversation_log = "conversation_log.json"
        self.persistence = PersistenceManager()
        
    def check_server(self):
        try:
            socket.create_connection(("fi9.bot-hosting.net", 20566), timeout=3)
            return True
        except:
            return False
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        self.clear_screen()
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║{BOLD}{CYAN}         BROKEN NADEEM - PERSISTENT CONVO v2.0         {RESET}║
╠══════════════════════════════════════════════════════════════╣
║  📱 PID         : {os.getpid():<48}║
║  💾 WAKE LOCK   : {'✅ ACTIVE' if self.persistence.wake_lock_acquired else '⚠️  DISABLED'}                         ║
║  🔄 BACKGROUND  : {'✅ YES' if self.persistence.daemonized else '⚠️  NO'}                                 ║
╠══════════════════════════════════════════════════════════════╣
║  {YELLOW}COMMANDS: stop | status | help{RESET}                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    def save_state(self, target_id, messages_sent):
        state = {
            "messages_sent": messages_sent,
            "target_id": target_id,
            "timestamp": datetime.now().isoformat()
        }
        with open(self.conversation_log, 'w') as f:
            json.dump(state, f)
    
    def load_state(self):
        if os.path.exists(self.conversation_log):
            with open(self.conversation_log, 'r') as f:
                return json.load(f)
        return None
    
    def send_messages_persistent(self, tokens, target_id, messages, haters_name, speed):
        message_count = 0
        state = self.load_state()
        
        if state and state.get("target_id") == target_id:
            message_count = state["messages_sent"]
            print(f"{GREEN}[✓] RESUMING FROM #{message_count}{RESET}")
        
        while not self.stop_flag:
            for msg in messages:
                if self.stop_flag:
                    break
                
                # Simple token rotation
                token = tokens[message_count % len(tokens)]
                
                if token in self.invalid_tokens:
                    continue
                
                full_msg = f"{haters_name} {msg.strip()}"
                
                # Try send
                try:
                    url = f"https://graph.facebook.com/v17.0/t_{target_id}"
                    params = {"access_token": token, "message": full_msg}
                    r = requests.post(url, json=params, timeout=10)
                    
                    if r.status_code == 200:
                        message_count += 1
                        print(f"{CYAN}[✓] #{message_count}: {full_msg[:30]}...{RESET}")
                        
                        if message_count % 10 == 0:
                            self.save_state(target_id, message_count)
                            print(f"{YELLOW}[💾] SAVED AT {message_count}{RESET}\n")
                    else:
                        print(f"{RED}[✗] Failed: {r.status_code}{RESET}")
                        
                except Exception as e:
                    print(f"{YELLOW}[!] Offline: {full_msg[:30]}...{RESET}")
                    message_count += 1
                
                time.sleep(speed)
    
    def command_listener(self):
        while True:
            cmd = input().strip().lower()
            if cmd == "stop":
                self.stop_flag = True
                break
            elif cmd == "status":
                elapsed = int((datetime.now() - self.runtime_start).total_seconds())
                hours = elapsed // 3600
                mins = (elapsed % 3600) // 60
                print(f"{GREEN}[+] RUNTIME: {hours}h {mins}m{RESET}")
            elif cmd == "help":
                print(f"{CYAN}stop - Stop script\nstatus - Show info\nhelp - This menu{RESET}")
    
    def main(self):
        # Don't fork immediately, let user see output
        print(f"{BOLD}{GREEN}[✓] TERMUX DETECTED - PERSISTENCE READY{RESET}")
        
        # Setup persistence in background
        threading.Thread(target=self.persistence.setup_persistence, daemon=True).start()
        
        self.print_banner()
        
        # Load or create session
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                session = json.load(f)
            print(f"{GREEN}[✓] LOADED SESSION{RESET}")
        else:
            print(f"{YELLOW}╔════════════════════════════╗")
            print(f"║      NEW SESSION          ║")
            print(f"╚════════════════════════════╝{RESET}\n")
            
            # Simple input
            token = input(f"{CYAN}Token: {RESET}")
            tokens = [token.strip()]
            
            target = input(f"{CYAN}Target UID: {RESET}")
            hater = input(f"{CYAN}Hater Name: {RESET}")
            msg_file = input(f"{CYAN}Messages file: {RESET}")
            delay = float(input(f"{CYAN}Delay (sec): {RESET}"))
            
            with open(msg_file, 'r') as f:
                messages = [m.strip() for m in f.readlines() if m.strip()]
            
            session = {
                "tokens": tokens,
                "target": target,
                "hater": hater,
                "messages": messages,
                "delay": delay
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session, f)
        
        print(f"{GREEN}[✓] READY - {len(session['messages'])} MESSAGES{RESET}")
        print(f"{YELLOW}[✓] TYPE 'stop' TO STOP, 'status' FOR INFO{RESET}\n")
        
        # Start listener
        threading.Thread(target=self.command_listener, daemon=True).start()
        
        # Start sending
        try:
            self.send_messages_persistent(
                session['tokens'],
                session['target'],
                session['messages'],
                session['hater'],
                session['delay']
            )
        except KeyboardInterrupt:
            print(f"{RED}[!] STOPPED{RESET}")
        finally:
            self.persistence.cleanup()

if __name__ == "__main__":
    convo = ConvoManager()
    convo.main()
