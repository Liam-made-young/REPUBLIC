#!/usr/bin/env python3
"""
Build script for creating REPUBLIC executables for Mac and Windows.

Usage:
    python build_exe.py          # Build for current platform
    python build_exe.py --clean  # Clean build directories first
    python build_exe.py --onedir # Create a directory instead of single file

Requirements:
    pip install pyinstaller
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys


def get_platform():
    """Returns the current platform: 'mac', 'windows', or 'linux'."""
    system = platform.system().lower()
    if system == "darwin":
        return "mac"
    elif system == "windows":
        return "windows"
    else:
        return "linux"


def clean_build_dirs():
    """Remove previous build artifacts."""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["REPUBLIC.spec"] if os.path.exists("republic.spec") else []

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}/...")
            shutil.rmtree(dir_name)

    # Clean __pycache__ in subdirectories
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                path = os.path.join(root, dir_name)
                print(f"Removing {path}...")
                shutil.rmtree(path)


def check_dependencies():
    """Check if required packages are installed."""
    try:
        import PyInstaller

        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    try:
        import pygame

        print(f"Pygame version: {pygame.version.ver}")
    except ImportError:
        print("ERROR: Pygame is not installed.")
        print("Install it with: pip install pygame-ce")
        sys.exit(1)

    try:
        import noise

        print("Noise library: installed")
    except ImportError:
        print("ERROR: Noise library is not installed.")
        print("Install it with: pip install noise")
        sys.exit(1)


def build_executable(one_dir=False):
    """Build the executable using PyInstaller."""
    current_platform = get_platform()
    print(f"\nBuilding for platform: {current_platform}")

    # Base PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=REPUBLIC",
        "--noconsole",  # No console window (use --console for debugging)
        "--clean",
    ]

    # Add data files (assets)
    assets_path = os.path.join(os.path.dirname(__file__), "assets")
    if os.path.exists(assets_path):
        if current_platform == "windows":
            cmd.append(f"--add-data=assets;assets")
        else:
            cmd.append(f"--add-data=assets:assets")
    else:
        print("WARNING: Assets folder not found!")

    # One file or one directory
    if one_dir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    # Platform-specific options
    if current_platform == "mac":
        cmd.extend(
            [
                "--osx-bundle-identifier=com.republic.game",
                "--target-architecture=universal2",  # Support both Intel and Apple Silicon
            ]
        )
        # Check for icon
        if os.path.exists("icon.icns"):
            cmd.append("--icon=icon.icns")
    elif current_platform == "windows":
        # Check for icon
        if os.path.exists("icon.ico"):
            cmd.append("--icon=icon.ico")
        cmd.append("--uac-admin=false")

    # Hidden imports that PyInstaller might miss
    hidden_imports = [
        "pygame",
        "pygame.locals",
        "pygame.font",
        "pygame.mixer",
        "pygame.image",
        "pygame.transform",
        "pygame.draw",
        "pygame.display",
        "pygame.event",
        "pygame.time",
        "pygame.key",
        "pygame.mouse",
        "noise",
        "asyncio",
    ]

    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # Exclude unnecessary modules to reduce size
    excludes = [
        "tkinter",
        "matplotlib",
        "numpy.testing",
        "scipy",
        "PIL.ImageTk",
        "IPython",
        "jupyter",
        "notebook",
    ]

    for exc in excludes:
        cmd.append(f"--exclude-module={exc}")

    # The main script
    cmd.append("republic_main.py")

    print("\nRunning PyInstaller with command:")
    print(" ".join(cmd))
    print()

    # Run PyInstaller
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)

        if one_dir:
            output_path = os.path.join("dist", "REPUBLIC")
        else:
            if current_platform == "mac":
                output_path = os.path.join("dist", "REPUBLIC.app")
                if not os.path.exists(output_path):
                    output_path = os.path.join("dist", "REPUBLIC")
            elif current_platform == "windows":
                output_path = os.path.join("dist", "REPUBLIC.exe")
            else:
                output_path = os.path.join("dist", "REPUBLIC")

        print(f"\nExecutable created at: {os.path.abspath(output_path)}")

        # Print size
        if os.path.exists(output_path):
            if os.path.isfile(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                print(f"Size: {size_mb:.1f} MB")
            else:
                # Calculate directory size
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(output_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                size_mb = total_size / (1024 * 1024)
                print(f"Total size: {size_mb:.1f} MB")

        print("\nTo distribute:")
        if current_platform == "mac":
            print("  - Zip the .app bundle or REPUBLIC folder")
            print("  - Users can run by double-clicking the app")
            print(
                "  - Note: Users may need to right-click > Open on first run due to Gatekeeper"
            )
        elif current_platform == "windows":
            print("  - Share the REPUBLIC.exe file directly")
            print("  - Or zip it for easier distribution")
            print("  - Users can run by double-clicking the exe")
        else:
            print("  - Share the REPUBLIC file")
            print("  - Users may need to: chmod +x REPUBLIC")

        return True
    else:
        print("\n" + "=" * 50)
        print("BUILD FAILED!")
        print("=" * 50)
        print("Check the error messages above.")
        return False


def create_mac_dmg():
    """Create a DMG file for macOS distribution (optional)."""
    if get_platform() != "mac":
        print("DMG creation is only available on macOS")
        return False

    app_path = os.path.join("dist", "REPUBLIC.app")
    if not os.path.exists(app_path):
        app_path = os.path.join("dist", "REPUBLIC")

    if not os.path.exists(app_path):
        print("No app bundle found to create DMG")
        return False

    dmg_path = os.path.join("dist", "REPUBLIC.dmg")

    # Remove existing DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    print("\nCreating DMG...")
    cmd = [
        "hdiutil",
        "create",
        "-volname",
        "REPUBLIC",
        "-srcfolder",
        app_path,
        "-ov",
        "-format",
        "UDZO",
        dmg_path,
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"DMG created at: {os.path.abspath(dmg_path)}")
        return True
    else:
        print("Failed to create DMG")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build REPUBLIC game executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_exe.py              # Build single-file executable
  python build_exe.py --clean      # Clean and build
  python build_exe.py --onedir     # Build as directory (faster startup)
  python build_exe.py --dmg        # Create macOS DMG (Mac only)
        """,
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean build directories before building"
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="Create a directory instead of single file",
    )
    parser.add_argument(
        "--dmg", action="store_true", help="Create macOS DMG after building (Mac only)"
    )
    parser.add_argument(
        "--check", action="store_true", help="Only check dependencies, do not build"
    )

    args = parser.parse_args()

    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {script_dir}")

    # Check dependencies
    print("\nChecking dependencies...")
    check_dependencies()

    if args.check:
        print("\nDependency check complete.")
        return

    # Clean if requested
    if args.clean:
        print("\nCleaning build directories...")
        clean_build_dirs()

    # Build
    success = build_executable(one_dir=args.onedir)

    # Create DMG if requested (Mac only)
    if success and args.dmg and get_platform() == "mac":
        create_mac_dmg()

    print("\nDone!")


if __name__ == "__main__":
    main()
