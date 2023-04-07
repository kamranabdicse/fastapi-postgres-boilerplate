# fastapi-postgres-boilerplate
This project template which uses FastAPi, Alembic, SQLAlchemy as ORM, Rocketry as scheduler, Celery as async task manager. It shows a complete async CRUD template. Also I setup cache app with invalidate feature. 


## Set environment variables

Create an **.env** file on root folder and copy the content from **.env.example**. Feel free to change it according to your own configuration.

## Development guide:

### Run the project using Docker containers and forcing build containers

**docker-compose-dev.yml**: a container for postgres and redis services
- When you want to build the project you should use this file to have dockerized postgres and redis attached to the project.
- To build and run postgres and redis should use this command: 
```dockerfile
docker-compose -f docker-compose-dev.yml up -d --build 
```
#### Hint:
If you get some errors like 'port already in use' for postgres or redis you can change the external port.

**docker-compose.yml**:
- Main docker-compose file for building service.For running container after  building postgres and redis 
you should run the following command : 
```dockerfile
docker-compose up -d --build
```


## TODO List:
- [ ] Add Custom Exception handler
- [ ] Add jsonb field on table sample
- [ ] Add docstrings
- [ ] Add Custom Response model
- [ ] Create sample one to many relationship
- [ ] Create sample many to many relationship
- [ ] Add Black formatter and flake8 lint
- [ ] Add export report api in csv/xlsx files using StreamingResponse
- [ ] Convert repo into template using cookiecutter