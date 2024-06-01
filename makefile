install:
	@echo "Installing app dependencies"
	@poetry install
	@poetry run pre-commit install

run:
	@echo "Running the application locally"
	@poetry run python -m src.markets.app

build-local:
	@echo "Building Docker image and running container"
	@docker pull public.ecr.aws/lambda/python:3.10
	@docker image build --platform linux/amd64 -t lambda .
	@docker container run --env-file .env -p 9000:8080 lambda

invoke-local:
	@echo "Invoking a locally running lambda container"
	@curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

clean:
	@echo "Cleaning local project directory"
	@find . -type d \
		\( -name '.venv' -o \
		-name '.*_cache' -o \
		-name '__pycache__' \) \
		-exec rm -rf {} + \
		2>/dev/null || true

init-terraform:
	@source .env_tf && cd src/infrastructure/backend && \
	terraform init && \
	terraform apply -auto-approve
	@cd src/infrastructure && terraform init -backend-config=../../backend.hcl

test:
	@echo "Running tests"
	@poetry run pre-commit run --all-files

test-integration:
	@poetry run python -m pytest tests/test_app_integration.py

test-deployment:
	@poetry run python -m pytest tests/test_deployment.py

build:
	@echo "Building app"
	@cd src/infrastructure && terraform apply -target=aws_ecr_repository.erc_repository -auto-approve
	@aws ecr get-login-password | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
	@docker build --platform linux/amd64 -t ecr-repository .
	@docker tag ecr-repository:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ecr-repository:latest
	@docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ecr-repository:latest

deploy:
	@echo "Deploying app"
	@cd src/infrastructure && terraform apply -auto-approve

destroy:
	@echo "Destroying app"
	# @aws ecr list-images --repository-name ecr-repository --query 'imageIds[*]' --output json | jq -c '.[]' | while read -r image_id; do \
	# 	aws ecr batch-delete-image --repository-name ecr-repository --image-ids "$$image_id"; \
	# 	done
	@cd src/infrastructure && terraform destroy -auto-approve

test-deploy:
	@echo "Testing infrastructure"
	@bash ./tests/test_existance.sh


echo-project:
	@mkdir -p tmp
	@bash utils/echo_project.sh > tmp/project.txt
