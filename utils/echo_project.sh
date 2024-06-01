#! /bin/bash

echo "Project directory structure:"
tree -I "__pycache__|*tfstate*|prototyping|backend"

list="pyproject.toml .pre-commit-config.yaml src/markets/app.py src/infrastructure/main.tf .github/workflows/ci-cd.yml"
for file in $list; do
	echo ""
	echo file: "$file"
	cat "$file"
done
