terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0.0"
    }
  }
  cloud {
    organization = "alexlewzey"

    workspaces {
      tags = ["markets"]
    }
  }

}


provider "aws" {
  region = "eu-west-2"
}


variable "erc_repository_name" {
  type    = string
  default = "markets-ecr-repository"
}

variable "lambda_name" {
  type    = string
  default = "markets-lambda"
}

variable "image_tag" {
  type = string
}


resource "aws_ecr_repository" "erc_repository" {
  name                 = var.erc_repository_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "ecr_repository_name" {
  value = aws_ecr_repository.erc_repository.name
}

output "repository_url" {
  value = aws_ecr_repository.erc_repository.repository_url
}


resource "aws_lambda_function" "market_lambda" {
  function_name = var.lambda_name
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.erc_repository.repository_url}:${var.image_tag}"
  role          = aws_iam_role.lambda_exec_role.arn

  timeout     = 120 # seconds
  memory_size = 512 # MB

  tracing_config {
    mode = "Active"
  }

}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "scheduler.amazonaws.com"
          ]
        }
      }
    ]
  })
}

data "aws_secretsmanager_secret" "gmail_secret" {
  name = "gmail"
}

resource "aws_iam_policy" "lambda_invoke_policy" {
  name        = "lambda-invoke-policy"
  description = "Policy for invoking Lambda functions by Scheduler"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "lambda:InvokeFunction"
        ],
        Effect   = "Allow",
        Resource = aws_lambda_function.market_lambda.arn
      },
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Effect   = "Allow",
        Resource = data.aws_secretsmanager_secret.gmail_secret.arn
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "lambda_exec_role_policy_attach" {
  name       = "lambda-invoke-attachment"
  roles      = [aws_iam_role.lambda_exec_role.name]
  policy_arn = aws_iam_policy.lambda_invoke_policy.arn
}


resource "aws_scheduler_schedule" "daily_lambda_trigger" {
  name = "daily-lambda-trigger"
  flexible_time_window {
    mode = "OFF"
  }
  schedule_expression          = "cron(0 9 * * ? *)"
  schedule_expression_timezone = "Europe/London"

  target {
    arn      = aws_lambda_function.market_lambda.arn
    role_arn = aws_iam_role.lambda_exec_role.arn
    input    = "{}"
  }


}


resource "aws_lambda_permission" "allow_scheduler" {
  statement_id  = "AllowExecutionFromScheduler"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.market_lambda.function_name
  principal     = "scheduler.amazonaws.com"
  source_arn    = aws_scheduler_schedule.daily_lambda_trigger.arn
}
