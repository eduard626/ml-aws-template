## An ML template

## Setup
The following software is required for this template to work: nodejs, npm, poetry and projen.
So, in a terminal:
```
# update repo info
sudo apt update

# nodejs and npm
sudo apt install nodejs npm 

# install poetry
curl -sSL https://install.python-poetry.org | python3 -

# install projen
npm install -g projen
```

## Deploy

# Init the project with the template
python3 bootstrap.py --name "new-cool-project-name"

The script ...
* 🚀 Clones the template
* 🚀 Initializes with essential scaffolding

🎉 Success! Your new project is ready.
