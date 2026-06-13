import subprocess, sys, time, os, signal, socket

BASE = os.path.dirname(os.path.abspath(__file__))
WEB_APP = os.path.join(BASE, "web", "app.py")

def port_open(port=5000):
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False

# Stop old Flask
try:
    import psutil
    for p in psutil.process_iter(["pid", "cmdline"]):
        cmd = p.info.get("cmdline") or []
        if any("app.py" in c for c in cmd):
            p.terminate()
            p.wait(timeout=3)
except:
    pass

# Kill port 5000
if os.name == "nt":
    result = subprocess.run(
        f'for /f "tokens=5" %a in (\'netstat -ano ^| findstr ":5000 "\') do taskkill /f /pid %a',
        shell=True, capture_output=True, text=True
    )
else:
    subprocess.run(["fuser", "-k", "5000/tcp"], capture_output=True)

time.sleep(2)

proc = subprocess.Popen(
    [sys.executable, WEB_APP],
    cwd=BASE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW,
)

for i in range(15):
    if port_open():
        print(f"SERVER STARTED at http://127.0.0.1:5000/")
        break
    time.sleep(1)
else:
    print("SERVER FAILED TO START")
    sys.exit(1)
