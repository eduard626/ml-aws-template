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
At the root of your new project, add this template as submodule
```
git submodule add https://github.com/eduard626/ml-aws-template.git ml-aws-template
```

Run the boostrap script
```
python3 ml-aws-template/bootstrap.py --name "new-cool-project-name"
```

The script ...
* 🚀 Clones the template
* 🚀 Initializes with essential scaffolding

🎉 Success! Your new project is ready.
