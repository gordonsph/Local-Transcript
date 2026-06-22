"""py2app build configuration for Local Transcript.

Build a standalone .app bundle:

    cd work/transcribe_app
    ../transcribe-venv/bin/python setup.py py2app

The bundled app runs the pywebview shell (shell.py), which boots the Flask
backend in-process. Heavy runtime artifacts (whisper-cli, the large-v3 model,
and outputs) are NOT bundled — they are resolved at runtime from
~/Library/Application Support/LocalTranscript (see app.py).
"""

from pathlib import Path

from setuptools import setup


HERE = Path(__file__).resolve().parent


def tree_data_files(*dir_names: str) -> list[tuple[str, list[str]]]:
    """Collect a directory tree as py2app data_files, preserving structure.

    Returns (dest_dir, [files]) tuples so the folders land next to the frozen
    scripts in Contents/Resources, where app.py's APP_ROOT expects them.
    """
    collected: list[tuple[str, list[str]]] = []
    for dir_name in dir_names:
        base = HERE / dir_name
        for path in base.rglob("*"):
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            dest = str(path.parent.relative_to(HERE))
            collected.append((dest, [str(path)]))
    return collected


APP = ["shell.py"]

# whisper-runtime holds the relocated, signed whisper-cli + its dylibs (produced
# by work/relocate_whisper.sh). Bundling it lands the binary at
# Contents/Resources/whisper-runtime/, where app.py resolves WHISPER_CLI when frozen.
DATA_FILES = tree_data_files("templates", "static", "whisper-runtime")

# Copy these packages wholesale. Tracing individual modules misses PyAV's
# bundled ffmpeg dylibs (av/.dylibs) and opencc's dictionary/config data, so we
# force py2app to copy the entire package directories instead.
PACKAGES = [
    "flask",
    "jinja2",
    "werkzeug",
    "click",
    "markupsafe",
    "itsdangerous",
    "blinker",
    "av",
    "numpy",
    "opencc",
    "webview",
]

INCLUDES = [
    "objc",
    "Foundation",
    "AppKit",
    "WebKit",
    "Quartz",
    "Security",
]

PLIST = {
    "CFBundleName": "Local Transcript",
    "CFBundleDisplayName": "Local Transcript",
    "CFBundleIdentifier": "com.gordonsiu.local-transcript",
    "CFBundleShortVersionString": "1.0.0",
    "CFBundleVersion": "1.0.0",
    "LSMinimumSystemVersion": "11.0",
    "NSHighResolutionCapable": True,
    # Prepared for Phase 3 (Live recording in the WebView needs this string or
    # getUserMedia is rejected silently).
    "NSMicrophoneUsageDescription": "Local Transcript records from your microphone for live transcription.",
}

OPTIONS = {
    "iconfile": str(HERE / "static" / "icons" / "app.icns"),
    "plist": PLIST,
    "packages": PACKAGES,
    "includes": INCLUDES,
    "argv_emulation": False,
}

setup(
    app=APP,
    name="Local Transcript",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    # py2app is installed by build_macos_app.sh (requirements-build.txt) before
    # this runs, so we avoid setup_requires' deprecated network fetch path.
)
