terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.49"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    # Terraform stateをS3互換ストレージで管理する場合に設定
    # ローカル管理の場合はこのブロックを削除してください
    # bucket = "bt-sys-tfstate"
    # key    = "prod/terraform.tfstate"
    # region = "us-east-1"
  }
}
