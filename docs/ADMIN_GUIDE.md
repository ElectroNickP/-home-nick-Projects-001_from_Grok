# Telegram Bot Manager - Руководство администратора

**Версия:** 2.0.0 (Hexagonal Architecture)  
**Дата:** 21.08.2025

## 📚 Содержание

1. [Установка и развертывание](#установка-и-развертывание)
2. [Конфигурация системы](#конфигурация-системы)
3. [Безопасность](#безопасность)
4. [Мониторинг и алертинг](#мониторинг-и-алертинг)
5. [Backup и восстановление](#backup-и-восстановление)
6. [Производительность и масштабирование](#производительность-и-масштабирование)
7. [Обслуживание](#обслуживание)
8. [Устранение неполадок](#устранение-неполадок)

## 🚀 Установка и развертывание

### Системные требования

#### Минимальные требования
- **ОС:** Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python:** 3.9+
- **RAM:** 1GB (2GB рекомендуется)
- **CPU:** 1 vCPU (2+ рекомендуется)
- **Диск:** 5GB свободного места
- **Сеть:** Доступ к api.telegram.org и api.openai.com

#### Производственные требования
- **ОС:** Ubuntu 22.04 LTS / RHEL 9
- **Python:** 3.11+
- **RAM:** 4GB+ (зависит от количества ботов)
- **CPU:** 4+ vCPU
- **Диск:** 50GB+ SSD
- **Сеть:** Выделенный IP, CDN

### Методы установки

#### Docker развертывание (рекомендуется)

**1. Подготовка окружения:**
```bash
# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt-get install docker-compose-plugin

# Создание директории проекта
mkdir /opt/telegram-bot-manager
cd /opt/telegram-bot-manager
```

**2. Docker Compose конфигурация:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  bot-manager:
    image: telegram-bot-manager:2.0.0
    container_name: telegram-bot-manager
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - ENV=production
      - LOG_LEVEL=INFO
      - DATABASE_URL=postgresql://postgres:password@db:5432/telegram_bots
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    container_name: telegram-bot-manager-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=telegram_bots
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: telegram-bot-manager-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    container_name: telegram-bot-manager-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - bot-manager

volumes:
  postgres_data:
  redis_data:
```

**3. Переменные окружения:**
```bash
# .env
SECRET_KEY=your-very-secure-secret-key-here
POSTGRES_PASSWORD=your-secure-database-password
ADMIN_PASSWORD=your-secure-admin-password
OPENAI_API_KEY=your-openai-api-key
```

**4. Запуск:**
```bash
# Генерация секретных ключей
openssl rand -hex 32 > .secret_key

# Запуск сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
docker-compose logs -f bot-manager
```

#### Systemd сервис (альтернативный способ)

**1. Установка зависимостей:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev
sudo apt-get install postgresql-15 redis-server nginx

# CentOS/RHEL
sudo dnf install python3.11 python3.11-pip
sudo dnf install postgresql15-server redis nginx
```

**2. Создание пользователя:**
```bash
sudo useradd -m -s /bin/bash telegram-bot-manager
sudo usermod -aG sudo telegram-bot-manager
```

**3. Установка приложения:**
```bash
# Клонирование и настройка
sudo -u telegram-bot-manager bash << 'EOF'
cd /home/telegram-bot-manager
git clone https://github.com/your-org/telegram-bot-manager.git
cd telegram-bot-manager

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# Настройка конфигурации
cp config/production.env.example .env
EOF
```

**4. Systemd сервис:**
```ini
# /etc/systemd/system/telegram-bot-manager.service
[Unit]
Description=Telegram Bot Manager
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=simple
User=telegram-bot-manager
Group=telegram-bot-manager
WorkingDirectory=/home/telegram-bot-manager/telegram-bot-manager
Environment=PATH=/home/telegram-bot-manager/telegram-bot-manager/venv/bin
ExecStart=/home/telegram-bot-manager/telegram-bot-manager/venv/bin/python src/integration/unified_app.py --port 5000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/home/telegram-bot-manager/telegram-bot-manager/data
ReadWritePaths=/home/telegram-bot-manager/telegram-bot-manager/logs

[Install]
WantedBy=multi-user.target
```

**5. Активация сервиса:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot-manager
sudo systemctl start telegram-bot-manager
sudo systemctl status telegram-bot-manager
```

### Kubernetes развертывание

**1. Namespace и ConfigMap:**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: telegram-bot-manager

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: telegram-bot-manager
data:
  LOG_LEVEL: "INFO"
  ENV: "production"
  DATABASE_URL: "postgresql://postgres:password@postgres:5432/telegram_bots"
  REDIS_URL: "redis://redis:6379/0"
```

**2. Secrets:**
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: telegram-bot-manager
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  ADMIN_PASSWORD: <base64-encoded-password>
  POSTGRES_PASSWORD: <base64-encoded-password>
```

**3. Deployment:**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-bot-manager
  namespace: telegram-bot-manager
spec:
  replicas: 3
  selector:
    matchLabels:
      app: telegram-bot-manager
  template:
    metadata:
      labels:
        app: telegram-bot-manager
    spec:
      containers:
      - name: app
        image: telegram-bot-manager:2.0.0
        ports:
        - containerPort: 5000
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: SECRET_KEY
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        volumeMounts:
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: logs-pvc
```

## ⚙️ Конфигурация системы

### Файлы конфигурации

#### Основная конфигурация

**production.env:**
```bash
# Основные настройки
ENV=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/telegram_bots
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis кэширование
REDIS_URL=redis://localhost:6379/0
CACHE_DEFAULT_TIMEOUT=300
CACHE_KEY_PREFIX=tbm:

# Веб-сервер
HOST=0.0.0.0
PORT=5000
WORKERS=4
WORKER_CONNECTIONS=1000

# Безопасность
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=pbkdf2:sha256:...
SESSION_TIMEOUT=3600
JWT_EXPIRE_HOURS=24

# Внешние API
TELEGRAM_API_URL=https://api.telegram.org
OPENAI_API_URL=https://api.openai.com
HTTP_TIMEOUT=30
MAX_RETRIES=3

# Файловая система
DATA_DIR=/app/data
LOG_DIR=/app/logs
BACKUP_DIR=/app/backups
UPLOAD_MAX_SIZE=10485760  # 10MB

# Мониторинг
METRICS_ENABLED=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Производительность
MAX_BOTS_PER_INSTANCE=50
MESSAGE_QUEUE_SIZE=10000
WORKER_POOL_SIZE=10
```

#### Конфигурация логирования

**logging.yaml:**
```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s'
  json:
    class: src.monitoring.logging_system.JSONFormatter
    include_traceback: true
    include_thread_info: true

filters:
  sensitive_filter:
    class: src.monitoring.logging_system.SensitiveDataFilter
    sensitive_fields: [password, token, key, secret, auth]

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
    filters: [sensitive_filter]
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /app/logs/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 10
    filters: [sensitive_filter]
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /app/logs/error.log
    maxBytes: 10485760
    backupCount: 5
    filters: [sensitive_filter]

loggers:
  telegram_bot_manager:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false
  
  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false
  
  sqlalchemy.engine:
    level: WARNING
    handlers: [file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

#### Конфигурация мониторинга

**monitoring.yaml:**
```yaml
metrics:
  enabled: true
  collection_interval: 15  # seconds
  retention_hours: 24
  export_format: prometheus

alerts:
  enabled: true
  channels:
    - type: telegram
      token: BOT_TOKEN
      chat_id: ADMIN_CHAT_ID
    - type: email
      smtp_host: smtp.gmail.com
      smtp_port: 587
      username: alerts@yourdomain.com
      password: app_password
      recipients: [admin@yourdomain.com]

rules:
  - name: high_memory_usage
    metric: system.memory.percent
    operator: gt
    threshold: 80
    severity: warning
    duration: 5m
  
  - name: critical_memory_usage
    metric: system.memory.percent
    operator: gt
    threshold: 90
    severity: critical
    duration: 2m
  
  - name: high_error_rate
    metric: app.error_rate
    operator: gt
    threshold: 5  # errors per minute
    severity: critical
    duration: 1m
  
  - name: bot_down
    metric: bot.status
    operator: eq
    threshold: 0  # 0 = stopped
    severity: warning
    duration: 30s

health_checks:
  - name: database
    type: postgresql
    url: $DATABASE_URL
    timeout: 5
  
  - name: redis
    type: redis
    url: $REDIS_URL
    timeout: 3
  
  - name: telegram_api
    type: http
    url: https://api.telegram.org/bot$BOT_TOKEN/getMe
    timeout: 10
  
  - name: disk_space
    type: disk
    path: /app/data
    threshold: 90  # percent
```

### Настройка базы данных

#### PostgreSQL конфигурация

**postgresql.conf (основные настройки):**
```ini
# Подключения
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB

# Производительность
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB

# Логирование
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%a.log'
log_truncate_on_rotation = on
log_rotation_age = 1d
log_rotation_size = 100MB
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
log_min_duration_statement = 1000  # Log slow queries

# Архивирование и репликация
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
max_wal_senders = 3
```

**Создание пользователя и базы данных:**
```sql
-- Создание пользователя
CREATE USER telegram_bot_manager WITH PASSWORD 'secure_password';

-- Создание базы данных
CREATE DATABASE telegram_bots OWNER telegram_bot_manager;

-- Предоставление прав
GRANT ALL PRIVILEGES ON DATABASE telegram_bots TO telegram_bot_manager;

-- Настройка расширений
\c telegram_bots
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

**Инициализация схемы:**
```sql
-- Таблица ботов
CREATE TABLE bots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    token VARCHAR(512) NOT NULL UNIQUE,
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'stopped',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица диалогов
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    bot_id INTEGER REFERENCES bots(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bot_id, chat_id)
);

-- Таблица сообщений
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content TEXT,
    message_type VARCHAR(50) DEFAULT 'text',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_conversations_bot_id ON conversations(bot_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_bots_status ON bots(status);

-- Триггеры для updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON bots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Настройка веб-сервера

#### Nginx конфигурация

**nginx.conf:**
```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Логирование
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time ut="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main;
    
    # Производительность
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web:10m rate=5r/s;
    
    # Upstream для приложения
    upstream telegram_bot_manager {
        least_conn;
        server 127.0.0.1:5000 max_fails=3 fail_timeout=30s;
        server 127.0.0.1:5001 max_fails=3 fail_timeout=30s backup;
    }
    
    # HTTPS сервер
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;
        
        # SSL конфигурация
        ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
        ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_prefer_server_ciphers on;
        ssl_stapling on;
        ssl_stapling_verify on;
        
        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # Основное приложение
        location / {
            limit_req zone=web burst=20 nodelay;
            
            proxy_pass http://telegram_bot_manager;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # WebSocket поддержка
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # API endpoints с отдельным rate limiting
        location /api/ {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://telegram_bot_manager;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Статические файлы
        location /static/ {
            alias /opt/telegram-bot-manager/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            access_log off;
            proxy_pass http://telegram_bot_manager;
        }
        
        # Метрики (только для внутренних IP)
        location /metrics {
            allow 127.0.0.1;
            allow 10.0.0.0/8;
            allow 192.168.0.0/16;
            deny all;
            
            proxy_pass http://telegram_bot_manager;
        }
    }
    
    # HTTP редирект на HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }
}
```

## 🔒 Безопасность

### Аутентификация и авторизация

#### JWT конфигурация

**Настройка JWT:**
```python
# В конфигурации приложения
JWT_SECRET_KEY = 'your-jwt-secret-key'
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
JWT_ALGORITHM = 'HS256'

# Настройка cookie для JWT
JWT_TOKEN_LOCATION = ['headers', 'cookies']
JWT_COOKIE_SECURE = True  # Только для HTTPS
JWT_COOKIE_CSRF_PROTECT = True
JWT_COOKIE_SAMESITE = 'Lax'
```

**Управление ролями:**
```python
# Определение ролей
ROLES = {
    'admin': {
        'permissions': ['*'],  # Все права
        'description': 'Полный административный доступ'
    },
    'operator': {
        'permissions': [
            'bots.read', 'bots.start', 'bots.stop',
            'conversations.read', 'system.status'
        ],
        'description': 'Управление ботами и просмотр данных'
    },
    'viewer': {
        'permissions': [
            'bots.read', 'conversations.read', 'system.status'
        ],
        'description': 'Только просмотр данных'
    }
}
```

#### Защита API endpoints

**Rate limiting:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

# Настройка лимитов для разных endpoints
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass

@app.route('/api/bots', methods=['GET'])
@limiter.limit("60 per minute")
def list_bots():
    pass
```

**CORS настройка:**
```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

### Защита данных

#### Шифрование чувствительных данных

**Настройка шифрования:**
```python
from cryptography.fernet import Fernet
import base64

class DataEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        """Шифрование строки."""
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Расшифровка строки."""
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()

# Использование для токенов ботов
encryption = DataEncryption(ENCRYPTION_KEY)
encrypted_token = encryption.encrypt(bot_token)
```

#### Безопасное хранение секретов

**Использование внешних секретов:**
```python
# AWS Secrets Manager
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# HashiCorp Vault
import hvac

def get_vault_secret(path):
    client = hvac.Client(url='https://vault.yourdomain.com')
    client.token = os.environ['VAULT_TOKEN']
    response = client.secrets.kv.v2.read_secret_version(path=path)
    return response['data']['data']

# Kubernetes Secrets
def get_k8s_secret(secret_name, key):
    with open(f'/var/run/secrets/{secret_name}/{key}', 'r') as f:
        return f.read().strip()
```

### Сетевая безопасность

#### Firewall настройка

**UFW (Ubuntu):**
```bash
# Базовая конфигурация
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешить SSH
sudo ufw allow ssh

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Разрешить доступ к приложению только через nginx
sudo ufw allow from 127.0.0.1 to any port 5000

# Ограничить доступ к базе данных
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Активация
sudo ufw enable
```

**iptables правила:**
```bash
#!/bin/bash
# firewall.sh

# Очистка существующих правил
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Политики по умолчанию
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Loopback интерфейс
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Установленные соединения
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH (ограничить по IP если возможно)
iptables -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Приложение (только с localhost)
iptables -A INPUT -p tcp -s 127.0.0.1 --dport 5000 -j ACCEPT

# PostgreSQL (только с приватных сетей)
iptables -A INPUT -p tcp -s 10.0.0.0/8 --dport 5432 -j ACCEPT
iptables -A INPUT -p tcp -s 192.168.0.0/16 --dport 5432 -j ACCEPT

# Redis (только с localhost)
iptables -A INPUT -p tcp -s 127.0.0.1 --dport 6379 -j ACCEPT

# Сохранение правил
iptables-save > /etc/iptables/rules.v4
```

#### VPN и туннелирование

**WireGuard для удаленного доступа:**
```ini
# /etc/wireguard/wg0.conf (сервер)
[Interface]
PrivateKey = SERVER_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Клиент администратора
[Peer]
PublicKey = ADMIN_PUBLIC_KEY
AllowedIPs = 10.0.0.2/32

# Клиент мониторинга
[Peer]
PublicKey = MONITORING_PUBLIC_KEY
AllowedIPs = 10.0.0.3/32
```

### Аудит безопасности

#### Логирование событий безопасности

**Конфигурация аудита:**
```python
import logging
from datetime import datetime

security_logger = logging.getLogger('security')

class SecurityAuditFilter(logging.Filter):
    def filter(self, record):
        # Добавляем метки безопасности
        record.security_event = True
        record.timestamp = datetime.utcnow().isoformat()
        return True

# События для аудита
def log_login_attempt(username, ip_address, success):
    security_logger.info(
        "Login attempt",
        extra={
            'event_type': 'login_attempt',
            'username': username,
            'ip_address': ip_address,
            'success': success,
            'user_agent': request.headers.get('User-Agent', '')
        }
    )

def log_permission_denied(username, resource, action):
    security_logger.warning(
        "Permission denied",
        extra={
            'event_type': 'permission_denied',
            'username': username,
            'resource': resource,
            'action': action,
            'ip_address': request.remote_addr
        }
    )

def log_sensitive_operation(username, operation, target):
    security_logger.info(
        "Sensitive operation",
        extra={
            'event_type': 'sensitive_operation',
            'username': username,
            'operation': operation,
            'target': target,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
```

#### Автоматическое обнаружение угроз

**Обнаружение аномалий:**
```python
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

class ThreatDetector:
    def __init__(self):
        self.login_attempts = defaultdict(lambda: deque(maxlen=10))
        self.api_requests = defaultdict(lambda: deque(maxlen=100))
        self.lock = threading.RLock()
    
    def check_brute_force(self, ip_address):
        """Проверка на brute force атаки."""
        with self.lock:
            now = datetime.utcnow()
            attempts = self.login_attempts[ip_address]
            
            # Удаляем старые попытки (старше 1 часа)
            while attempts and attempts[0] < now - timedelta(hours=1):
                attempts.popleft()
            
            # Проверяем количество попыток
            if len(attempts) >= 5:
                self.block_ip(ip_address, reason="Brute force detected")
                return True
            
            return False
    
    def check_rate_limit_abuse(self, ip_address):
        """Проверка на превышение лимитов API."""
        with self.lock:
            now = datetime.utcnow()
            requests = self.api_requests[ip_address]
            
            # Удаляем старые запросы (старше 1 минуты)
            while requests and requests[0] < now - timedelta(minutes=1):
                requests.popleft()
            
            # Проверяем количество запросов
            if len(requests) >= 60:  # 60 запросов в минуту
                self.block_ip(ip_address, reason="Rate limit abuse")
                return True
            
            return False
    
    def block_ip(self, ip_address, reason):
        """Блокировка IP адреса."""
        # Добавление в iptables
        os.system(f"iptables -A INPUT -s {ip_address} -j DROP")
        
        # Логирование
        security_logger.critical(
            f"IP blocked: {ip_address}",
            extra={
                'event_type': 'ip_blocked',
                'ip_address': ip_address,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Уведомление администратора
        self.notify_admin(f"IP {ip_address} blocked: {reason}")

threat_detector = ThreatDetector()
```

---

*Продолжение следует в следующей части документации...*







