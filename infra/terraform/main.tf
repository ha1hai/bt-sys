provider "hcloud" {
  token = var.hcloud_token
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# SSH鍵
resource "hcloud_ssh_key" "default" {
  name       = "bt-sys"
  public_key = var.ssh_public_key
}

# ファイアウォール
resource "hcloud_firewall" "bt_sys" {
  name = "bt-sys"

  # SSH
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "22"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTP
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  rule {
    direction = "in"
    protocol  = "tcp"
    port      = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# VPSサーバー
resource "hcloud_server" "bt_sys" {
  name        = "bt-sys"
  image       = "ubuntu-24.04"
  server_type = "cax11" # ARM 2vCPU, 4GB RAM, 40GB SSD
  location    = var.location

  ssh_keys     = [hcloud_ssh_key.default.id]
  firewall_ids = [hcloud_firewall.bt_sys.id]

  user_data = file("${path.module}/cloud-init.yaml")

  labels = {
    project = "bt-sys"
    env     = "prod"
  }
}

# Cloudflare DNS - APIサブドメイン
resource "cloudflare_record" "api" {
  zone_id = var.cloudflare_zone_id
  name    = "api"
  value   = hcloud_server.bt_sys.ipv4_address
  type    = "A"
  proxied = true # Cloudflare CDN経由
}

# Cloudflare DNS - ルートドメイン（フロントエンドはPages側で設定するため参考用）
resource "cloudflare_record" "root" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  value   = hcloud_server.bt_sys.ipv4_address
  type    = "A"
  proxied = true
}
