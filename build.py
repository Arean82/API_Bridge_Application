# ==================================================================
# File: build.py
# Description: Build script for the application.
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
import shutil
import subprocess
import sys
import time

def kill_running_app():
    """Kill any running instances of the app to free file locks."""
    if os.name == 'nt':
        print("Ensuring no existing bridge_app is running...")
        subprocess.run(["taskkill", "/F", "/IM", "bridge_app.exe", "/T"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

def clean_directory(path):
    """Safely remove a directory if it exists, with retries for file locks."""
    if os.path.exists(path):
        print(f"Cleaning up '{path}'...")
        for _ in range(5):
            try:
                shutil.rmtree(path, ignore_errors=False)
                break
            except Exception:
                time.sleep(1)
        else:
            print(f"  Warning: Could not completely delete '{path}'. PyInstaller might fail.")

def main():
    print("=== Synora Bridge Build System ===")
    print("What would you like to build?")
    print("  1. OneDir (Faster to launch, produces a folder with many files)")
    print("  2. OneFile (Slower to launch, produces a single clean .exe)")
    print("  3. Both")
    print("  4. Exit")
    
    choice = input("\nEnter your choice (1, 2, 3, or 4): ").strip()
    
    if choice == '4':
        print("Exiting.")
        return
        
    build_onedir = choice in ['1', '3']
    build_onefile = choice in ['2', '3']
    
    if not build_onedir and not build_onefile:
        print("Invalid choice. Exiting.")
        return

    print("\n1. Cleaning previous builds...")
    kill_running_app()
    clean_directory('build')
    if build_onedir:
        clean_directory(os.path.join('dist', 'onedir'))
    if build_onefile:
        clean_directory(os.path.join('dist', 'onefile'))
    
    if build_onedir:
        print("\n2. Building 'onedir' executable...")
        subprocess.run([sys.executable, "-m", "PyInstaller", "bridge_app_onedir.spec", "--clean", "--noconfirm", "--distpath", "dist"], check=True)
        # Copy .env and config.ini
        shutil.copy(".env", os.path.join("dist", "onedir", ".env"))
        shutil.copy("config.ini", os.path.join("dist", "onedir", "config.ini"))
    
    if build_onefile:
        print("\n3. Building 'onefile' executable...")
        subprocess.run([sys.executable, "-m", "PyInstaller", "bridge_app_onefile.spec", "--clean", "--noconfirm", "--distpath", "dist/onefile"], check=True)
        # Copy .env and config.ini
        shutil.copy(".env", os.path.join("dist", "onefile", ".env"))
        shutil.copy("config.ini", os.path.join("dist", "onefile", "config.ini"))
    
    print("\n=== Build Complete! ===")
    print("Your built applications are located in the 'dist' folder.")

if __name__ == "__main__":
    main()
