NAME = 'my_project'
PARENT_DIR = .

help:
	@echo "react-redux initial setup"
	@echo "dependencies: npx, jq, sponge"
	@echo "run: make build NAME=name PARENT_DIR=parent_dir"

create-react-app: 
	/usr/bin/npx create-react-app $(NAME) --use-npm --template typescript

#removed -- husky v 5+ fails to create git hook
configure-prettier:
	cd $(NAME) && npm install husky lint-staged prettier && jq -s '.[0] * .[1]' package.json ../prettier-config.json | sponge package.json
	cd $(NAME) && /usr/bin/npx husky add .husky/pre-commit "npx lint-staged"

install-bootstrap:
	cd $(NAME) && npm install react-bootstrap bootstrap --legacy-peer-deps

install-redux:
	cd $(NAME) && npm install redux react-redux --legacy-peer-deps

install-router:
	cd $(NAME) && npm install react-router-dom --legacy-peer-deps

install-styled-components:
	cd $(NAME) && npm install styled-components --legacy-peer-deps

copy-files:
	mkdir -p  $(NAME)/src/components
	mkdir -p $(NAME)/src/actions
	mkdir -p $(NAME)/src/reducers
	cp boilerplate-action.js $(NAME)/src/actions/index.tsx
	cp boilerplate-reducer.js $(NAME)/src/reducers/index.tsx
	cp boilerplate-app.js $(NAME)/src/App.tsx
	cp boilerplate-index.js $(NAME)/src/index.tsx

git-commit:
	mv $(NAME) $(PARENT_DIR)/.
	cd $(PARENT_DIR)/$(NAME) && git init 
	cd $(PARENT_DIR)/$(NAME) && git add .
	cd $(PARENT_DIR)/$(NAME) && git commit -m"Initial setup of Redux and friends"

build:  create-react-app install-redux install-router install-bootstrap install-styled-components copy-files git-commit
	@echo "success"
