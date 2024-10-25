format: ## Run black and isort
	black .
	isort .

update_reqs: ## Update requirements.txt
	pipreqs --force .