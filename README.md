
# Nakhll

Nakhll is a market place, allows pepole to communicate with each other in order to grow together.

# Installation and setup
- [Manual Installation](#manual_installation)

## Maual Installation {#manual_installation}

### Linux

1. `sudo apt install git postgresql virtualenv lzma lzma-dev python3 python3-dev libmysqlclient-dev`
2. `git clone https://github.com/nakhll-company/nakhll_backend && cd nakhll_backend`
3. `virtualenv .venv`
4. `source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. setup Postgres database as described [here](#setup_db)


### Windows

1. Install python3 from [python website](https://www.python.org/downloads/windows/)
2. Install Git, postgres
3. `git clone https://github.com/nakhll-company/nakhll_backend && cd nakhll_backend`
4. `C:/Program Files/python3/bin/python -m venv .venv`
5. `.venv/bin/activate.bat`
6. `pip install -r requirements.txt`
7. setup Postgres database as described [here](#setup_db)
8. `python3 manage.py migrate`
9. `python3 manage.py runserver`

## Docker Installation

1. Install [Docker](https://docs.docker.com/engine/install/) and
   [docker-compose](https://docs.docker.com/compose/install/)
2. Download our `Dockerfile` file from 
   [here](https://raw.githubusercontent.com/nakhll-company/nakhll_backend/main/Dockerfile)
3. run `docker-compose 


## Database setup {#setup_db}

1. `sudo -su postgres`
2. `psql`
3. `CREATE ROLE nakhll WITH ENCRYPTED PASSWORD '12345';`
4. `CREATE DATABASE nakhlldb;`
5. `GRANT ALL PRIVILEGES ON DATABASE nakhlldb TO nakhll;`
6. `ALTER ROLE "nakhll" WITH LOGIN;`
7. `python3 manage.py migrate`
8. `python3 manage.py runserver`

## .env setup

Rename `sample.env` to `.env`, fill all data that is available. Note that you can leave
values as they are, but we recommend to replace them with some appropriate values.
For each value, there is a description about how it should be filled, see 
[docs](https://docs.nakhll.com/nakhll/.env) for more info



## Config linter for project

We use `autopep8` and `pylint` for formatting and linting our project. Code is
much more cleaner and readable in result. Here is how you can config formatter
and linter:

### VSCode

1. Install `pep8`, `autopep8`, `pylint`, `pylint-django` using `pip`. You
   probably installed them while installing all project dependencies using
   `pip install -r requirements.txt`
2. Add this lines to `settings.json` file in vscode (<kbd>Ctrl</kbd> + <kbd>,</kbd>
   or File > Preferences > Settings):

```
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.pycodestyleEnabled": true,
    "python.formatting.provider": "autopep8",
    "python.linting.pylintArgs": [
        "--load-plugins=pylint_django"
    ],
    "python.formatting.autopep8Args": [
        "--max-line-length",
        "80",
        "--aggressive",
        "--experimental"
    ],
    "editor.formatOnSave": true,
    "editor.formatOnSaveMode": "modifications",
}
```

### PyCharm

[COMPLETE_THIS_SECTION]


