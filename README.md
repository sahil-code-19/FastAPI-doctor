How to Run Against Your FastAPI Project

1. First clone the repo.
2. Go the project root and run command `uv sync`
3. run the following commands at the project root:
```
python -m fastapi_doctor.cli fastapi_project_path_that_you_want_scan

- Full scan
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project
- With file locations
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project --verbose
- Score only
python3 -m fastapi_doctor.cli /path/to/your/fastapi-project --score```
