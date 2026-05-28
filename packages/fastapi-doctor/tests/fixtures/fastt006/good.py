import asyncio
from fastapi import FastAPI

app = FastAPI()


@app.get("/users")
async def get_users():
    result = await fetch_users()
    return result


@app.get("/version")
async def get_version():
    proc = await asyncio.create_subprocess_exec(
        "git",
        "describe",
        "--tags",
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return {"version": stdout.decode().strip()}


@app.get("/export")
async def export_data():
    def run_export():
        import subprocess

        subprocess.run(["echo", "hello"], capture_output=True)

    return await asyncio.to_thread(run_export)


@app.get("/sync")
def sync_health():
    import subprocess

    result = subprocess.run(["uptime"], capture_output=True)
    return {"status": result.stdout.decode()}
