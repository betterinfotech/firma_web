variable "aws_region"      { type = string }
variable "name_prefix"     { type = string }
variable "lambda_zip_path" { type = string } # e.g., ../../dist/lambda_package.zip

variable "s3_bucket_id"  { type = string }   # bucket name
variable "s3_bucket_arn" { type = string }

variable "pg_host"      { type = string }
variable "pg_port"      { type = string default = "5432" }
variable "pg_db"        { type = string }
variable "pg_user"      { type = string }
variable "pg_password"  { type = string sensitive = true }
