provider "aws" {
  region = "us-east-1"
}

# Random suffix so bucket name is unique
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# 1. S3 Bucket
resource "aws_s3_bucket" "my_bucket" {
  bucket = "drift-demo-bucket-${random_string.suffix.result}"
  tags = {
    Environment = "prod"
  }
}

# 2. Security Group (we will simulate drift here)
resource "aws_security_group" "my_sg" {
  name        = "drift-sg"
  description = "Security group for drift demo"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # Demo only – in real life use your IP!
  }

  tags = {
    Environment = "prod"
  }
}

# 3. EC2 Instance (we will simulate drift on tags)
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "my_ec2" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.my_sg.id]

  tags = {
    Name        = "Drift-Demo-EC2"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}

output "ec2_public_ip" {
  value = aws_instance.my_ec2.public_ip
}

output "s3_bucket_name" {
  value = aws_s3_bucket.my_bucket.bucket
}