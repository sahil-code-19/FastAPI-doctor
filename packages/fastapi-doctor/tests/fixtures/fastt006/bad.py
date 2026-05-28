from fastapi import FastAPI
import subprocess
import os

app = FastAPI()


@app.get("/health")
async def check_health():
    result = subprocess.run(["uptime"], capture_output=True)
    return {"health": "ok"}


@app.get("/info")
async def get_info():
    output = subprocess.check_output(["uname", "-a"])
    return {"info": output.decode()}


@app.post("/cleanup")
async def cleanup():
    os.system("rm -rf /tmp/cache/*")
    return {"status": "cleaned"}


@app.get("/pids")
async def get_pids():
    proc = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    return {"pids": out.decode()}
