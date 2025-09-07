# CoralCollective Deployment Guide

Comprehensive deployment instructions for CoralCollective across all environments - from development to enterprise production. This guide covers Docker, Kubernetes, cloud platforms, and enterprise deployment patterns.

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [Environment Configuration](#environment-configuration)
- [Security Configuration](#security-configuration)
- [Monitoring & Observability](#monitoring--observability)
- [Scaling & Performance](#scaling--performance)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

Ensure you have the following installed:

```bash
# Core requirements
python3.8+          # Python runtime
docker              # Container platform
docker-compose      # Multi-container orchestration
kubectl             # Kubernetes CLI (optional)
git                # Version control

# Verification
python3 --version
docker --version
docker-compose --version
kubectl version --client
```

### One-Command Setup

For immediate deployment:

```bash
# Option 1: Docker deployment (Recommended for development)
curl -sSL https://coral-init.sh | bash
cd coral-collective
./deploy_coral.sh docker --environment production

# Option 2: PyPI installation (For existing projects)
python3 -m venv venv && source venv/bin/activate
pip install coral-collective[all]
coral setup --all
coral check --system
```

### Verification

Verify your deployment:

```bash
# Check system status
coral check --all

# Test basic functionality
coral list
coral run project_architect --task "Test deployment" --dry-run

# View system information
coral info --deployment
```

## Docker Deployment

Docker is the recommended deployment method for most use cases.

### Development Environment

```bash
# Clone repository
git clone https://github.com/coral-collective/coral-collective.git
cd coral-collective

# Create environment file
cp .env.example .env
# Edit .env with your API keys

# Start development environment
docker-compose up -d

# View services
docker-compose ps

# Follow logs
docker-compose logs -f coral-collective
```

### Production Environment

```bash
# Deploy production configuration
docker-compose --profile production up -d

# Or use the deployment script
./deploy_coral.sh docker --environment production --replicas 3

# Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

### Memory-Enhanced Deployment

For applications requiring advanced memory features:

```bash
# Deploy with full memory system
docker-compose --profile memory up -d

# Verify memory system
curl http://localhost:8001/api/v1/heartbeat  # ChromaDB
docker logs coral-collective-chroma

# Test memory functionality
coral memory test --connection
```

### Docker Compose Profiles

Available profiles for different deployment scenarios:

```yaml
# Development profile (default)
docker-compose up -d

# Production profile
docker-compose --profile production up -d

# Memory system profile  
docker-compose --profile memory up -d

# Full monitoring stack
docker-compose --profile monitoring up -d

# All services
docker-compose --profile production --profile memory --profile monitoring up -d
```

### Multi-Stage Builds

Our Docker images use multi-stage builds for optimization:

```dockerfile
# Base image with security hardening
FROM python:3.11-slim as base
RUN apt-get update && apt-get install -y --no-install-recommends \
    security-updates && rm -rf /var/lib/apt/lists/*

# Development image with debugging tools
FROM base as development
RUN pip install --no-cache-dir debugpy pytest-cov

# Production image (minimal)
FROM base as production
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --find-links /wheels coral-collective[all]
```

## Kubernetes Deployment

Enterprise-grade Kubernetes deployment with auto-scaling and high availability.

### Prerequisites

```bash
# Kubernetes cluster requirements
kubectl version --short
# Client: v1.25+, Server: v1.22+

# Storage class (for persistent volumes)
kubectl get storageclass

# Ingress controller (nginx recommended)
kubectl get ingressclass
```

### Quick Kubernetes Deployment

```bash
# Deploy using provided manifests
./deploy_coral.sh k8s --namespace coral-collective --replicas 3

# Or manual deployment
kubectl create namespace coral-collective
kubectl apply -f k8s/ --namespace coral-collective

# Check deployment status
kubectl get pods,svc,ingress -n coral-collective
```

### Kubernetes Architecture

```yaml
CoralCollective Kubernetes Architecture:

┌─────────────────────────────────────────────────────────────┐
│                     Ingress Layer                           │
│  nginx-ingress ──▶ coral-collective.yourdomain.com         │
│  cert-manager  ──▶ TLS/SSL certificates                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │ coral-collective│  │ coral-collective│  │ coral-      │ │
│  │    (pod-1)      │  │    (pod-2)      │  │collective   │ │
│  │                 │  │                 │  │   (pod-3)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   PostgreSQL    │  │    ChromaDB     │  │    Redis    │ │
│  │  (Primary DB)   │  │ (Vector Store)  │  │  (Caching)  │ │
│  │                 │  │                 │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Kubernetes Configuration

#### Namespace and Basic Setup

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: coral-collective
  labels:
    name: coral-collective
    tier: production
```

#### Deployment Configuration

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coral-collective
  namespace: coral-collective
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: coral-collective
  template:
    metadata:
      labels:
        app.kubernetes.io/name: coral-collective
        app.kubernetes.io/version: "3.0.0"
    spec:
      securityContext:
        fsGroup: 1000
      containers:
      - name: coral-collective
        image: coral-collective:3.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: coral-collective-secrets
              key: postgres-url
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: data
          mountPath: /app/data
      volumes:
      - name: config
        configMap:
          name: coral-collective-config
      - name: data
        persistentVolumeClaim:
          claimName: coral-collective-pvc
```

#### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: coral-collective-hpa
  namespace: coral-collective
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: coral-collective
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

### Ingress Configuration

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: coral-collective-ingress
  namespace: coral-collective
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  tls:
  - hosts:
    - coral-collective.yourdomain.com
    secretName: coral-collective-tls
  rules:
  - host: coral-collective.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: coral-collective
            port:
              number: 8000
```

## Cloud Platform Deployment

### AWS Deployment

#### EKS Deployment

```bash
# Create EKS cluster
eksctl create cluster --name coral-collective \
  --version 1.25 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10

# Deploy CoralCollective
kubectl apply -f k8s/aws/ --recursive

# Configure ALB ingress
kubectl apply -f k8s/aws/ingress-alb.yaml
```

#### RDS Integration

```yaml
# Use AWS RDS PostgreSQL
apiVersion: v1
kind: Secret
metadata:
  name: coral-collective-secrets
type: Opaque
stringData:
  postgres-url: "postgresql://username:password@coral-db.cluster-xxx.us-west-2.rds.amazonaws.com:5432/coral"
```

### Google Cloud Platform

#### GKE Deployment

```bash
# Create GKE cluster
gcloud container clusters create coral-collective \
  --zone=us-central1-a \
  --machine-type=e2-standard-2 \
  --num-nodes=3 \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=10

# Deploy application
kubectl apply -f k8s/gcp/ --recursive
```

#### Cloud SQL Integration

```yaml
# Use Cloud SQL PostgreSQL
apiVersion: v1
kind: Secret
metadata:
  name: coral-collective-secrets
type: Opaque
stringData:
  postgres-url: "postgresql://username:password@10.x.x.x:5432/coral"
```

### Azure Deployment

#### AKS Deployment

```bash
# Create resource group
az group create --name coral-collective-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group coral-collective-rg \
  --name coral-collective \
  --node-count 3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Deploy application
kubectl apply -f k8s/azure/ --recursive
```

## Environment Configuration

### Environment Variables

#### Core Configuration

```bash
# .env file structure
# Core application settings
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# Database configuration
POSTGRES_URL=postgresql://user:password@postgres:5432/coral
REDIS_URL=redis://redis:6379/0

# AI API Keys (Required)
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# MCP Integration (Optional)
GITHUB_TOKEN=your_github_token
E2B_API_KEY=your_e2b_api_key
DOCKER_HOST=unix:///var/run/docker.sock

# Memory System Configuration
CHROMA_HOST=chroma
CHROMA_PORT=8000
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Performance Settings
MAX_CONCURRENT_AGENTS=10
TOKEN_CACHE_SIZE=1000
MEMORY_CACHE_TTL=3600

# Security Settings
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,coral-collective.yourdomain.com
CORS_ORIGINS=https://coral-collective.yourdomain.com
```

#### Development vs Production

```bash
# Development environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
AUTO_RELOAD=true

# Production environment  
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

### Configuration Management

#### Docker Secrets

```yaml
# docker-compose.yml secrets
secrets:
  claude_api_key:
    file: ./secrets/claude_api_key.txt
  postgres_password:
    file: ./secrets/postgres_password.txt

services:
  coral-collective:
    secrets:
      - claude_api_key
      - postgres_password
    environment:
      CLAUDE_API_KEY_FILE: /run/secrets/claude_api_key
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

#### Kubernetes Secrets

```bash
# Create secrets from files
kubectl create secret generic coral-collective-secrets \
  --from-file=claude-api-key=./secrets/claude_api_key.txt \
  --from-file=postgres-password=./secrets/postgres_password.txt \
  --namespace coral-collective

# Create secrets from literals  
kubectl create secret generic coral-collective-secrets \
  --from-literal=CLAUDE_API_KEY='your_claude_key' \
  --from-literal=POSTGRES_PASSWORD='your_password' \
  --namespace coral-collective
```

## Security Configuration

### Network Security

#### Docker Network Isolation

```yaml
# docker-compose.yml networks
networks:
  coral_internal:
    driver: bridge
    internal: true
  coral_external:
    driver: bridge

services:
  coral-collective:
    networks:
      - coral_external
      - coral_internal
  
  postgres:
    networks:
      - coral_internal  # Internal only
```

#### Kubernetes Network Policies

```yaml
# k8s/networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: coral-collective-netpol
  namespace: coral-collective
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: coral-collective
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: chroma
    ports:
    - protocol: TCP
      port: 8000
```

### Security Scanning

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'coral-collective:latest'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

### Access Controls

#### RBAC Configuration (Kubernetes)

```yaml
# k8s/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: coral-collective
  namespace: coral-collective
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: coral-collective
  name: coral-collective-role
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: coral-collective-rolebinding
  namespace: coral-collective
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: coral-collective-role
subjects:
- kind: ServiceAccount
  name: coral-collective
  namespace: coral-collective
```

## Monitoring & Observability

### Prometheus & Grafana Setup

```yaml
# docker-compose monitoring profile
  prometheus:
    image: prom/prometheus:latest
    profiles: ["monitoring"]
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    profiles: ["monitoring"]
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: coral
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
```

### Application Metrics

```python
# Custom metrics endpoint
@app.route('/metrics')
def metrics():
    return {
        'agents': {
            'total_executions': agent_counter.get(),
            'success_rate': success_rate.get(),
            'average_duration': avg_duration.get()
        },
        'memory': {
            'total_memories': memory_count.get(),
            'cache_hit_rate': cache_hit_rate.get()
        },
        'system': {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    }
```

### Health Checks

```python
# Health check endpoints
@app.route('/health/live')
def liveness():
    return {'status': 'alive', 'timestamp': datetime.utcnow()}

@app.route('/health/ready')
def readiness():
    checks = {
        'database': check_database_connection(),
        'memory_system': check_memory_system(),
        'mcp_servers': check_mcp_connections()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return {'status': 'ready' if all_healthy else 'not ready', 'checks': checks}, status_code
```

### Logging Configuration

```yaml
# Structured logging configuration
logging:
  version: 1
  disable_existing_loggers: false
  formatters:
    standard:
      format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    json:
      format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
  handlers:
    console:
      class: logging.StreamHandler
      formatter: json
      stream: ext://sys.stdout
    file:
      class: logging.handlers.RotatingFileHandler
      formatter: standard
      filename: /app/logs/coral-collective.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
  root:
    level: INFO
    handlers: [console, file]
  loggers:
    coral_collective:
      level: DEBUG
      handlers: [console, file]
      propagate: false
```

## Scaling & Performance

### Auto-scaling Configuration

#### Docker Swarm Mode

```yaml
# docker-compose.yml with swarm mode
version: '3.8'
services:
  coral-collective:
    image: coral-collective:3.0.0
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.25'
          memory: 512M
```

#### Kubernetes HPA with Custom Metrics

```yaml
# Advanced HPA configuration
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: coral-collective-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: coral-collective
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: agent_queue_length
      target:
        type: AverageValue
        averageValue: "10"
  - type: External
    external:
      metric:
        name: memory_system_load
      target:
        type: Value
        value: "80"
```

### Performance Optimization

#### Caching Strategy

```python
# Multi-level caching configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'memory_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'coral-collective-memory',
    },
    'session_cache': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/2',
        'TIMEOUT': 86400,  # 24 hours
    }
}
```

#### Database Optimization

```sql
-- PostgreSQL optimization for CoralCollective
-- postgresql.conf settings

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

# Checkpoint settings
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

# Indexes for common queries
CREATE INDEX CONCURRENTLY idx_projects_status ON projects(status);
CREATE INDEX CONCURRENTLY idx_agents_execution_time ON agent_executions(created_at, agent_name);
CREATE INDEX CONCURRENTLY idx_memory_similarity ON memory_entries USING ivfflat (embedding vector_cosine_ops);
```

### Load Testing

```bash
# Load testing with k6
# scripts/load_test.js
import http from 'k6/http';
import { check } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 10 },
    { duration: '5m', target: 50 },
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 0 },
  ],
};

export default function() {
  let response = http.post('http://coral-collective:8000/api/agents/run', {
    agent_name: 'project_architect',
    task: 'Design a simple web application'
  });
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 30s': (r) => r.timings.duration < 30000,
  });
}

# Run load test
k6 run scripts/load_test.js
```

## Backup & Recovery

### Database Backups

```bash
#!/bin/bash
# scripts/backup_database.sh

BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/coral_backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump $POSTGRES_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Memory System Backups

```bash
#!/bin/bash
# scripts/backup_memory.sh

BACKUP_DIR="/backups/memory"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup ChromaDB data
docker exec coral-collective-chroma \
  tar czf /tmp/chroma_backup_${TIMESTAMP}.tar.gz /chroma/data

docker cp coral-collective-chroma:/tmp/chroma_backup_${TIMESTAMP}.tar.gz \
  ${BACKUP_DIR}/

# Backup vector embeddings
python scripts/export_memory_system.py \
  --output ${BACKUP_DIR}/memory_export_${TIMESTAMP}.json
```

### Automated Backup with CronJobs

```yaml
# k8s/cronjob-backup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: coral-collective-backup
  namespace: coral-collective
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: coral-collective-backup:latest
            command:
            - /scripts/full_backup.sh
            env:
            - name: POSTGRES_URL
              valueFrom:
                secretKeyRef:
                  name: coral-collective-secrets
                  key: postgres-url
            volumeMounts:
            - name: backup-storage
              mountPath: /backups
          restartPolicy: OnFailure
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
```

### Disaster Recovery

```bash
#!/bin/bash
# scripts/disaster_recovery.sh

# Full system recovery procedure
echo "Starting disaster recovery process..."

# 1. Stop all services
kubectl scale deployment coral-collective --replicas=0 -n coral-collective

# 2. Restore database
LATEST_BACKUP=$(find /backups/postgresql -name "*.gz" | sort | tail -1)
gunzip -c $LATEST_BACKUP | psql $POSTGRES_URL

# 3. Restore memory system
LATEST_MEMORY_BACKUP=$(find /backups/memory -name "*.json" | sort | tail -1)
python scripts/import_memory_system.py --input $LATEST_MEMORY_BACKUP

# 4. Restart services
kubectl scale deployment coral-collective --replicas=3 -n coral-collective

# 5. Verify recovery
kubectl wait --for=condition=available deployment/coral-collective -n coral-collective --timeout=300s
curl -f http://coral-collective/health/ready || exit 1

echo "Disaster recovery completed successfully"
```

## Troubleshooting

### Common Deployment Issues

#### Container Won't Start

```bash
# Debug container startup issues
docker logs coral-collective-dev --tail 50

# Check resource constraints
docker stats coral-collective-dev

# Verify environment variables
docker exec coral-collective-dev env | grep CORAL

# Test configuration
docker exec coral-collective-dev coral check --all
```

#### Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/coral-collective -n coral-collective -- \
  psql $POSTGRES_URL -c "SELECT version();"

# Check database logs
kubectl logs deployment/postgres -n coral-collective

# Verify secrets
kubectl get secret coral-collective-secrets -n coral-collective -o yaml
```

#### Memory System Problems

```bash
# Test ChromaDB connection
curl -f http://chroma:8000/api/v1/heartbeat

# Check ChromaDB logs
docker logs coral-collective-chroma

# Test memory system functionality
kubectl exec -it deployment/coral-collective -n coral-collective -- \
  python -c "
from coral_collective.memory import MemorySystem
memory = MemorySystem()
print('Memory system:', 'OK' if memory.health_check() else 'FAILED')
"
```

#### Performance Issues

```bash
# Monitor resource usage
kubectl top pods -n coral-collective

# Check for bottlenecks
kubectl exec -it deployment/coral-collective -n coral-collective -- \
  coral monitor --performance

# Analyze slow queries
kubectl exec -it deployment/postgres -n coral-collective -- \
  psql $POSTGRES_URL -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 10;
  "
```

### Debugging Tools

#### Debug Mode Deployment

```yaml
# debug-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coral-collective-debug
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: coral-collective
        image: coral-collective:debug
        env:
        - name: DEBUG
          value: "true"
        - name: LOG_LEVEL
          value: "DEBUG"
        - name: ENABLE_PROFILING
          value: "true"
        command: ["/bin/bash"]
        args: ["-c", "while true; do sleep 30; done"]
        stdin: true
        tty: true
```

#### Port Forwarding for Debug

```bash
# Forward ports for local debugging
kubectl port-forward deployment/coral-collective 8000:8000 -n coral-collective &
kubectl port-forward deployment/postgres 5432:5432 -n coral-collective &
kubectl port-forward deployment/chroma 8001:8000 -n coral-collective &

# Access services locally
curl http://localhost:8000/health
psql postgresql://coral:coral@localhost:5432/coral
curl http://localhost:8001/api/v1/heartbeat
```

### Support Resources

For additional help:

1. **System Logs**: Always check logs first
   ```bash
   # Docker
   docker-compose logs -f
   
   # Kubernetes  
   kubectl logs -f deployment/coral-collective -n coral-collective
   ```

2. **Health Checks**: Use built-in diagnostics
   ```bash
   coral check --all --verbose
   curl http://localhost:8000/health/ready
   ```

3. **Community Support**:
   - GitHub Issues: Bug reports and feature requests
   - GitHub Discussions: Community help and questions
   - Documentation: Comprehensive guides in `docs/`

4. **Professional Support**: Available for enterprise deployments

---

## Summary

This deployment guide covers all aspects of deploying CoralCollective from development to enterprise production environments. Key takeaways:

- **Start Simple**: Use Docker for development and testing
- **Scale Gradually**: Move to Kubernetes for production workloads
- **Monitor Everything**: Implement comprehensive monitoring from day one
- **Security First**: Apply security best practices at every layer
- **Plan for Recovery**: Implement robust backup and disaster recovery procedures

For more specific deployment scenarios, see the specialized guides in the `docs/deployment/` directory.