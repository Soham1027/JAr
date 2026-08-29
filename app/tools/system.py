import os
import re
import shutil
import subprocess
from pathlib import Path


UNSAFE_CHARS = re.compile(r"[&|<>^`$\n;]")

ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "notepad": "notepad",
    "note pad": "notepad",
    "not pad": "notepad",
    "not page": "notepad",
    "webpad": "notepad",
    "note page": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "explorer": "explorer",
    "file explorer": "explorer",
    "files": "explorer",
    "cmd": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "terminal": "wt",
    "windows terminal": "wt",
    "settings": "ms-settings:",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "code": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "outlook": "outlook",
    "spotify": "spotify",
    "discord": "discord",
    "steam": "steam",
    "photos": "ms-photos:",
}

FOLDERS = {
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
    "home": Path.home(),
}


def open_application(target: str) -> dict:
    name = (target or "").strip().strip("\"'")

    if not name:
        return {"ok": False, "error": "Nothing to open."}

    if UNSAFE_CHARS.search(name):
        return {"ok": False, "error": "That target looks unsafe to open."}

    name = re.sub(r"\s+(please|for me|now)$", "", name, flags=re.I).strip()

    try:
        opened = _open(name)
    except Exception as error:
        return {"ok": False, "target": name, "error": str(error)}

    if opened:
        return {"ok": True, "opened": opened, "label": name}

    return {"ok": False, "target": name, "error": f"I could not open {name}."}


def _open(name: str) -> str | None:
    lowered = name.lower()

    if lowered in FOLDERS:
        path = FOLDERS[lowered]
        if path.exists():
            os.startfile(path)
            return str(path)

    if name.startswith(("http://", "https://", "ms-settings:", "ms-photos:")):
        os.startfile(name)
        return name

    if "." in name and " " not in name and not Path(name).exists():
        if re.fullmatch(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?", name):
            url = f"https://{name}"
            os.startfile(url)
            return url

    path = Path(name).expanduser()
    if path.exists():
        os.startfile(path)
        return str(path)

    command = ALIASES.get(lowered, name)
    executable = shutil.which(command)

    if executable:
        subprocess.Popen(
            [executable],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return executable

    completed = subprocess.run(
        ["cmd", "/c", "start", "", command],
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.returncode == 0:
        return command

    return None
