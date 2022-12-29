## Setup project
create poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```
```
export PATH="/home/kamran/.local/bin:$PATH"
```
```
cd backend
```
## Project setup
#### First, let’s create our new project, let’s call it "app"
```
poetry new app
```
```
pip3 install uvicorn gunicorn fastapi
```
```
cd /backend/app
```
```
poetry add "package_name"
```
## Initialising a pre-existing project
```
cd /backend/app
```
```
poetry shell
```
```
poetry install
```

