# ==================================================================
# File: synora_connect.py
# Description: Utility script to automatically prepend standard headers to Python files.
#
# Copyright (C) 2026 Arean Narrayan - SynoraStudio
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==================================================================

import os
import sys

# VENV Enforcement
if not getattr(sys, 'frozen', False):
    in_venv = sys.prefix != sys.base_prefix
    if not in_venv:
        venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'Scripts', 'python.exe')
        if os.path.exists(venv_python) and sys.executable.lower() != venv_python.lower():
            print("[System] Automatically restarting inside virtual environment...")
            import subprocess
            sys.exit(subprocess.call([venv_python] + sys.argv))
import threading
import time
import argparse
import configparser
import webbrowser
from dotenv import load_dotenv

load_dotenv()

import platform

from bridge_app.app import create_app
app = create_app()

def is_docker():
    return os.path.exists('/.dockerenv')

def start_flask_server(host, port, debug):
    """Run Flask in a daemon thread."""
    app.run(host=host, port=port, debug=debug, use_reloader=False)

def run_gui(host, port, debug, base_dir):
    """Run the CustomTkinter GUI."""
    try:
        import customtkinter as ctk
        import tkinter as tk
        from tkinter import messagebox
        import queue
        import sys
        
        # Set appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        root = ctk.CTk()
        root.title("Synora Connect - Server Console")
        root.geometry("800x550")
        
        # --- Windows Taskbar Icon Fix ---
        if platform.system() == 'Windows':
            try:
                import ctypes
                myappid = 'synora.connect.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass
                
        # Set Window Icon
        try:
            icon_path = os.path.join(base_dir, 'bridge_app', 'static', 'icon.png')
            if os.path.exists(icon_path):
                root.iconphoto(False, tk.PhotoImage(file=icon_path))
        except Exception:
            pass

        def open_browser():
            webbrowser.open(f'http://127.0.0.1:{port}')

        def set_theme(mode):
            ctk.set_appearance_mode(mode)
            print(f"[UI] Theme changed to {mode}")

        def show_reader(filename):
            """Internal window to read MD files"""
            reader = ctk.CTkToplevel(root)
            reader.title(f"Reading: {filename}")
            reader.geometry("700x600")
            reader.after(10, reader.lift)
            
            try:
                import markdown
                from tkinterweb import HtmlFrame
                
                file_path = os.path.join(base_dir, 'docs', filename)
                if not os.path.exists(file_path):
                    file_path = os.path.join(base_dir, filename)
                    
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    
                html_content = markdown.markdown(file_content)
                
                is_dark = ctk.get_appearance_mode() == "Dark"
                bg = "#1a1a1a" if is_dark else "#ffffff"
                fg = "#e0e0e0" if is_dark else "#1a1a1a"
                
                html = f"<html><body style='font-family: sans-serif; background: {bg}; color: {fg}; padding: 20px;'>{html_content}</body></html>"
                
                frame = HtmlFrame(reader, messages_enabled=False)
                frame.load_html(html)
                frame.pack(expand=True, fill='both')
            except ImportError:
                is_dark = ctk.get_appearance_mode() == "Dark"
                bg_col = "#1a1a1a" if is_dark else "#ffffff"
                fg_col = "#e0e0e0" if is_dark else "#1a1a1a"
                txt = tk.Text(reader, wrap='word', bg=bg_col, fg=fg_col, font=("Segoe UI", 11), padx=20, pady=20, border=0)
                txt.pack(expand=True, fill='both')
                file_path = os.path.join(base_dir, 'docs', filename)
                if not os.path.exists(file_path): 
                    file_path = os.path.join(base_dir, filename)
                try:
                    txt.insert('1.0', open(file_path, 'r', encoding='utf-8').read())
                except Exception as e:
                    txt.insert('1.0', f"Error reading file: {e}")
                txt.config(state='disabled')

        


        def quit_app():
            if messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__
                print("Closing Server...")
                root.destroy()
                os._exit(0)

        # Standard Menu Bar
        menubar = tk.Menu(root)
        
        # 1. File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="  Open Web UI", command=open_browser)
        
        file_menu.add_separator()
        file_menu.add_command(label="  Exit", command=quit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        # 2. Theme Menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="  ☀️ Light Mode", command=lambda: set_theme("light"))
        theme_menu.add_command(label="  🌙 Dark Mode", command=lambda: set_theme("dark"))
        menubar.add_cascade(label="Theme", menu=theme_menu)

        # 3. Documentation Menu
        docs_menu = tk.Menu(menubar, tearoff=0)
        docs_menu.add_command(label="  README", command=lambda: show_reader("README.md"))
        docs_menu.add_separator()
        docs_menu.add_command(label="  INSTALLATION MANUAL", command=lambda: show_reader("INSTALLATION_MANUAL.md"))
        docs_menu.add_command(label="  USER MANUAL", command=lambda: show_reader("user_manual.md"))
        docs_menu.add_command(label="  SCALING MEMURAI", command=lambda: show_reader("SCALING_REDIS_MEMURAI.md"))
        docs_menu.add_separator()
        docs_menu.add_command(label="  SECURITY", command=lambda: show_reader("SECURITY.md"))
        docs_menu.add_command(label="  LICENSE", command=lambda: show_reader("LICENSE"))
        menubar.add_cascade(label="Documentation", menu=docs_menu)
        
        root.config(menu=menubar)

        # --- CONSOLE AREA ---
        console_frame = ctk.CTkFrame(root, corner_radius=10)
        console_frame.pack(expand=True, fill='both', padx=10, pady=10)

        text_area = tk.Text(console_frame, wrap='word', bg='#000000', fg='#00FF00', font=("Consolas", 10), border=0, padx=10, pady=10)
        text_area.pack(side="left", expand=True, fill='both')
        
        scrollbar = ctk.CTkScrollbar(console_frame, command=text_area.yview)
        scrollbar.pack(side="right", fill="y")
        text_area.configure(yscrollcommand=scrollbar.set)

        # --- Redirect Stdout with Async Queue ---
        log_queue = queue.Queue()

        class TextRedirector:
            def __init__(self, q):
                self.q = q
            def write(self, string):
                self.q.put(string)
            def flush(self): pass

        sys.stdout = TextRedirector(log_queue)
        sys.stderr = TextRedirector(log_queue)

        def process_logs():
            try:
                count = 0
                while count < 100:
                    msg = log_queue.get_nowait()
                    text_area.config(state='normal')
                    text_area.insert(tk.END, msg)
                    text_area.config(state='disabled')
                    text_area.see(tk.END)
                    count += 1
            except queue.Empty:
                pass
            root.after(100, process_logs)

        root.after(100, process_logs)
        root.protocol("WM_DELETE_WINDOW", quit_app)

        # Start Flask
        flask_thread = threading.Thread(target=start_flask_server, args=(host, port, debug))
        flask_thread.daemon = True
        flask_thread.start()

        # Welcome message
        print(f"Synora Connect Server running on http://127.0.0.1:{port}")
        print("-" * 50)

        # Auto-open browser
        # Auto-browser launch removed per user request

        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("[System] GUI failed to start. Falling back to terminal.")
        run_terminal(host, port, debug)

def run_terminal(host, port, debug):
    """Fallback interactive terminal."""
    print("=" * 50)
    print("Synora Connect - Terminal Mode")
    print("=" * 50)
    
    server_thread = threading.Thread(target=start_flask_server, args=(host, port, debug), daemon=True)
    server_thread.start()
    
    time.sleep(1)
    print(f"\nServer is running on http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

def main():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))

    config = configparser.ConfigParser()
    config.read(os.path.join(base_dir, 'config.ini'))
    
    host = config.get('Server', 'host', fallback='0.0.0.0')
    port = config.getint('Server', 'port', fallback=5000)
    debug = config.getboolean('Server', 'debug', fallback=False)
    
    parser = argparse.ArgumentParser(description="Synora Connect Launcher")
    parser.add_argument('--mode', choices=['docker', 'gui', 'terminal'], default='gui', help="Launch mode")
    args = parser.parse_args()
    
    if is_docker() or args.mode == 'docker':
        start_flask_server(host, port, debug)
    elif args.mode == 'gui':
        run_gui(host, port, debug, base_dir)
    else:
        run_terminal(host, port, debug)

if __name__ == '__main__':
    main()