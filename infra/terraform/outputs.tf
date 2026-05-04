output "server_ip" {
  description = "VPS IPv4 address"
  value       = hcloud_server.bt_sys.ipv4_address
}

output "server_ipv6" {
  description = "VPS IPv6 address"
  value       = hcloud_server.bt_sys.ipv6_address
}

output "api_url" {
  description = "API endpoint URL"
  value       = "https://api.${var.domain}"
}
