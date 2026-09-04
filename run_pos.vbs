Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' 1. Jalankan Backend FastAPI di background (Hidden)
WshShell.Run strPath & "\venv\Scripts\uvicorn.exe main:app --host 0.0.0.0 --port 8000", 0, False

' 2. Jeda 3 detik agar backend startup
WScript.Sleep 3000

' 3. Jalankan GUI PySide6 (Hidden Console)
WshShell.Run strPath & "\venv\Scripts\pythonw.exe " & strPath & "\desktop_client\gui_app.py", 0, True

' 4. Cleanup process saat GUI ditutup
WshShell.Run "taskkill /F /IM uvicorn.exe /T", 0, False
