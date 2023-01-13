## Setup project
create poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```
If you are using bash, you need to add this line to your ~/.profile or ~/.bashrc file.  
```
export PATH="/home/kamran/.local/bin:$PATH"
```
```
export PATH="/home/User/.local/bin:$PATH"
```
If you are using fish, you need to paste it in terminal
```
fish_add_path /home/kamran/.local/bin
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
## Migrate project
create migration file with:
```
alembic revision --autogenerate
```
apply migration with:
```commandline
alembic upgrade head
```
## Setup project in local
you must create .env file in backend/app and filled it with .env.example

### Test websocket
in order to test websocket paste this line in api test-websocket
```commandline
ws://ip:port/api/v1/utils/echo-client/
```
and paste response in html file and open it
