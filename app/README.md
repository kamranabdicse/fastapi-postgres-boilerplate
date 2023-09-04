## Setup project
after you cloned this project, you should install and use poetry for installing the essential packages and libraries, so you should create poetry as follows:
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

## Setup project without docker using Uvicorn
you must create .env file in both app and app/app folders and filled it with .env-example and change it according to your system configuration

you have to install and run postgres, redis and rabbitMQ server in your system and enter the ports and names and other credentials in the .env files for the project to run without problem.

if you want to run the project, after starting the named servers, migrate the project and use this command from the first "app" folder, it should look like this:
```
(app-py3.10) PS C:\some_folders\fastapi-postgres-boilerplate\app> uvicorn app.main:app --reload
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

## Create superuser
Set user email and password in .env file:

```
FIRST_SUPERUSER=
FIRST_SUPERUSER_PASSWORD=
```

Then run __initial_data.py__ file to create first superuser:

```bash
python3 initial_data.py

# or

poetry run python3 initial_data.py
```

### Test websocket
in order to test websocket paste this line in api test-websocket
```commandline
ws://ip:port/api/v1/utils/echo-client/
```
and paste response in html file and open it
