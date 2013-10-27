# preapp

At Preblur, we heavily use Flask applications.

This is our template.

## Conventions

    - Always break out code that does different things into a different file
    - 4 space tab
    - Wrap code to 80 characters; plaintext and comments to 78

## Environment Requirements

    - UNIX-ish
    - Python 2.7.5
    - Macs:
        - Homebrew
        - `sudo easy_install pip`
        - `sudo pip install virtualenv`
        - `brew install postgres`
        - `brew install redis`
        - `brew install heroku-toolbelt`

## Setup

After cloning the project, create a new file `.env` in the root directory.
This will be used to store all client secrets.

Here is a sample `.env` which contains all the neccessary keys:

    DEBUG=true
    REDIS_URL="redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS=10
    POSTGRES_URI=postgresql://root@localhost/app

## Scripts

At the beginning of every development session--and after pulling from the
repo--run:

    $ script/init_env.sh

If you've made any changes to the environment (mostly
`script/run pip install <pkg>`) make sure to save them before committing
changes:

    $ script/save_env.sh

To run commands, instead of `$ cmd arg1 arg2`, use:

    $ script/run cmd arg1 arg2

To start the server in development mode, use:

    $ script/launch

To start the server under gunicorn (Heroku mode), use:

    $ script/hlaunch