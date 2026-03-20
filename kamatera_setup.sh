#!/bin/bash
# kamatera_setup.sh
# Run ONCE on a fresh Kamatera Ubuntu 22.04 server to prepare it for HR Agent deployment
# Usage: bash kamatera_setup.sh

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║  SUEZ HR Agent — Kamatera Server Setup               ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── 1. System update ──────────────────────────────────────────────────────────
echo "[1/6] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# ── 2. Install Docker ─────────────────────────────────────────────────────────
echo "[2/6] Installing Docker..."
apt-get install -y ca-certificates curl gnupg lsb-release

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start  docker

echo "Docker version: $(docker --version)"

# ── 3. Install Nginx (reverse proxy) ─────────────────────────────────────────
echo "[3/6] Installing Nginx..."
apt-get install -y nginx

# Basic Nginx reverse proxy config for HR Agent
cat > /etc/nginx/sites-available/hr-agent <<'NGINX'
server {
    listen 80;
    server_name _;                         # replace _ with your domain if you have one

    client_max_body_size 50M;              # allow large resume uploads

    location / {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/hr-agent /etc/nginx/sites-enabled/hr-agent
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl enable nginx && systemctl restart nginx

echo "Nginx installed and configured."

# ── 4. Firewall ───────────────────────────────────────────────────────────────
echo "[4/6] Configuring firewall (UFW)..."
apt-get install -y ufw
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
echo "Firewall rules applied."

# ── 5. Create deploy user (optional, better than root) ───────────────────────
echo "[5/6] Creating deploy user..."
if ! id "deploy" &>/dev/null; then
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
  echo "deploy ALL=(ALL) NOPASSWD:/usr/bin/docker" >> /etc/sudoers.d/deploy
  chmod 0440 /etc/sudoers.d/deploy
  echo "User 'deploy' created and added to docker group."
else
  echo "User 'deploy' already exists."
fi

# ── 6. Create .env placeholder on server ─────────────────────────────────────
echo "[6/6] Creating /opt/hr-agent/.env placeholder..."
mkdir -p /opt/hr-agent
cat > /opt/hr-agent/.env <<'ENV'
GROQ_API_KEY=REPLACE_ME
GROQ_MODEL=llama-3.3-70b-versatile
SUPABASE_URL=REPLACE_ME
SUPABASE_KEY=REPLACE_ME
ENV
chmod 600 /opt/hr-agent/.env
echo "Edit /opt/hr-agent/.env and fill in your real keys before first deploy."

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Setup complete! Next steps:                         ║"
echo "║  1. Edit /opt/hr-agent/.env with real API keys       ║"
echo "║  2. Add SSH public key for Azure DevOps deploy user  ║"
echo "║  3. Run the Azure DevOps pipeline                    ║"
echo "╚══════════════════════════════════════════════════════╝"
