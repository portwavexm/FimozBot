# Deployment options

This repository includes two deployment approaches:

- Windows installer (PyInstaller + Inno Setup)
- Docker (recommended for servers/VPS)

1) Windows installer (developer machine)

- Requirements on build machine: Python 3.x, PyInstaller, Inno Setup (ISCC.exe)
- Build:
```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```
- The script will create `dist\run.exe`. If Inno Setup is installed, it will also run `installer.iss` to create an installer .exe.

Run produced executable on target machine. You can pass the same CLI args as `run.py`.

2) Portable ZIP (simple)

- Create a zip of the project root, send to target machine.
- On target:
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

3) Docker (server-friendly)

- Build and run locally:
```bash
docker compose up --build
```
- `docker-compose.yml` runs a Lavalink container using the `lavalink-server` folder (you must place `Lavalink.jar` there and configuration).
