NAME = 'my_project'
PARENT_DIR = .

help:
	@echo "react-redux initial setup"
	@echo "dependencies: npx, jq, spnge"
	@echo "run: make build NAME=name PARENT_DIR=parent_dir"

create-react-app: 
	/usr/bin/npx create-react-app $(NAME) --use-npm

configure-prettier:
	cd $(NAME) && npm install husky lint-staged prettier && jq -s '.[0] * .[1]' package.json ../prettier-config.json | sponge package.json
	cd $(NAME) && /usr/bin/npx husky add .husky/pre-commit "npx lint-staged"

install-bootstrap:
	cd $(NAME) && npm install react-bootstrap bootstrap

install-redux:
	cd $(NAME) && npm install redux react-redux

install-router:
	cd $(NAME) && npm install react-router-dom

install-styled-components:
	cd $(NAME) && npm install styled-components

copy-files:
	mkdir -p  $(NAME)/src/components
	mkdir -p $(NAME)/src/actions
	mkdir -p $(NAME)/src/reducers
	cp boilerplate-action.js $(NAME)/src/actions/index.js
	cp boilerplate-reducer.js $(NAME)/src/reducers/index.js
	cp boilerplate-app.js $(NAME)/src/App.js
	cp boilerplate-index.js $(NAME)/src/index.js

git-commit:
	mv -r $(NAME) $(PARENT_DIR)/.
	cd $(PARENT_DIR)/$(NAME) && git init 
	cd $(PARENT_DIR)/$(NAME) && git add .
	cd $(PARENT_DIR)/$(NAME) && git commit -m"Initial setup of Redux and friends"

build:  create-react-app configure-prettier install-redux install-router install-bootstrap install-styled-components copy-files git-commit
	@echo "success"
