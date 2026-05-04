variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "domain" {
  description = "Base domain (e.g. example.com)"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for VPS access"
  type        = string
}

variable "location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "fsn1" # Falkenstein (Germany) - 最安・低遅延
  # 他の選択肢: nbg1 (Nuremberg), hel1 (Helsinki), ash (Ashburn US), hil (Hillsboro US), sin (Singapore)
}
