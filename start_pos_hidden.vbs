Set WshShell = CreateObject("WScript.Shell")

' 1. Jalankan server uvicorn di background (window mode 0 / hidden)
WshShell.Run "cmd /c uvicorn main:app --host 0.0.0.0 --port 8000", 0, False

' 2. Tunggu 2 detik agar server siap
WScript.Sleep 2000

' 3. Buka browser ke alamat aplikasi POS
WshShell.Run "http://localhost:8000"