terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---- IAM role for Lambda ----
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals { type = "Service", identifiers = ["lambda.amazonaws.com"] }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.name_prefix}-filelog-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ---- Lambda function ----
resource "aws_lambda_function" "filelog" {
  function_name = "${var.name_prefix}-file-upload-logger"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.12"
  handler       = "s3_upload_logger.handler"     # 👈 updated handler
  filename         = var.lambda_zip_path         # e.g., ../../dist/lambda_package.zip
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  timeout     = 10
  memory_size = 256

  environment {
    variables = {
      PG_HOST     = var.pg_host
      PG_PORT     = var.pg_port
      PG_DB       = var.pg_db
      PG_USER     = var.pg_user
      PG_PASSWORD = var.pg_password
    }
  }
}

# ---- Allow S3 to invoke Lambda ----
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.filelog.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn
}

# ---- S3 -> Lambda event notification ----
resource "aws_s3_bucket_notification" "notify" {
  bucket = var.s3_bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.filelog.arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix     = "uploads/"   # optional
    # filter_suffix     = ".csv"       # optional
  }

  depends_on = [aws_lambda_permission.allow_s3]
}
