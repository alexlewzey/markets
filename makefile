setup-secrets:
	@python utils/create_gmail_secrets.py gmail_address=$(gmail_address) \
						gmail_password=$(gmail_password) \
						aws_access_key_id=$(aws_access_key_id) \
						aws_secret_access_key=$(aws_secret_access_key)

test:
	@pre-commit run --all-files

test-integration:
	@python -m pytest tests/test_app_integration.py

test-deployment:
	@python -m pytest tests/test_deployment.py

run:
	@echo "Running the application locally"
	@python -m src.markets.app

p2t:
	@poetry run python utils/project_to_text.py

build-local:
	@echo "Building Docker image and running container"
	@docker pull public.ecr.aws/lambda/python:3.12
	@docker image build --platform linux/amd64 -t lambda .
	@docker container run --env-file .env -p 9000:8080 lambda

invoke-local:
	@echo "Invoking a locally running lambda container"
	@curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

build:
	@echo "Building app"
	@cd src/infrastructure && terraform init
	@cd src/infrastructure && terraform apply -target=aws_ecr_repository.erc_repository -auto-approve
	@aws ecr get-login-password | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
	@docker build --platform linux/amd64 -t ecr-repository .
	@docker tag ecr-repository:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ecr-repository:latest
	@docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/ecr-repository:latest

deploy:
	@echo "Deploying app"
	@cd src/infrastructure && terraform init
	@cd src/infrastructure && terraform apply -auto-approve

destroy:
	@echo "Destroying app"
	@cd src/infrastructure && terraform init
	@cd src/infrastructure && terraform destroy -auto-approve
