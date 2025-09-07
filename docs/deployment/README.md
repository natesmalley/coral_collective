# CoralCollective Deployment Guide

This document provides comprehensive deployment instructions for CoralCollective across different environments and platforms.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Local Development](#local-development)
5. [Production Considerations](#production-considerations)
6. [Monitoring and Observability](#monitoring-and-observability)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- kubectl (for Kubernetes deployment)
- Git

### One-Command Deployment

```bash
# Clone and deploy with Docker
git clone https://github.com/coral-collective/coral-collective.git
cd coral-collective
./scripts/deploy.sh docker -e production
```

## Docker Deployment

### Development Environment

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f coral-collective

# Stop services
docker-compose down
```

### Production Environment

```bash
# Deploy production services
./scripts/deploy.sh docker -e production

# Or manually with Docker Compose
docker-compose --profile production up -d
```

### Memory-Enabled Deployment

For applications requiring vector storage and memory features:

```bash
# Deploy with memory system
docker-compose --profile memory up -d

# Or use the deployment script
./scripts/deploy.sh docker -e memory
```

### Environment Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   # Required: Database settings
   POSTGRES_PASSWORD=your_secure_password
   
   # Required: AI API Keys
   CLAUDE_API_KEY=your_claude_api_key
   OPENAI_API_KEY=your_openai_api_key
   
   # Optional: Additional services
   GITHUB_TOKEN=your_github_token
   E2B_API_KEY=your_e2b_api_key
   ```

### Service URLs

After deployment, services are available at:

- **CoralCollective API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **ChromaDB**: http://localhost:8001
- **Redis**: localhost:6379
- **Prometheus** (if enabled): http://localhost:9090
- **Grafana** (if enabled): http://localhost:3000

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Helm (optional, for advanced deployments)

### Basic Deployment

```bash
# Deploy to Kubernetes
./scripts/deploy.sh k8s -n coral-collective -r 3

# Or manually apply manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### Configure Secrets

Update the secrets file with base64-encoded values:

```bash
# Create secrets from command line
kubectl create secret generic coral-collective-secrets \
  --from-literal=POSTGRES_USER=coral \
  --from-literal=POSTGRES_PASSWORD=your-secure-password \
  --from-literal=CLAUDE_API_KEY=your-claude-api-key \
  --from-literal=GITHUB_TOKEN=your-github-token \
  --namespace=coral-collective
```

### Ingress Configuration

For external access, configure the ingress:

```bash
# Update ingress.yaml with your domain
sed -i 's/coral-collective.yourdomain.com/coral-collective.example.com/g' k8s/ingress.yaml
sed -i 's/admin@yourdomain.com/admin@example.com/g' k8s/ingress.yaml

# Apply ingress
kubectl apply -f k8s/ingress.yaml
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment coral-collective --replicas=5 -n coral-collective

# Auto-scaling is configured via HPA (Horizontal Pod Autoscaler)
kubectl get hpa -n coral-collective
```

## Local Development

### Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .[all]

# Run CoralCollective
coral --help
```

### Database Setup

```bash
# Start PostgreSQL and ChromaDB
docker-compose up -d postgres chroma

# Set environment variables
export POSTGRES_URL="postgresql://coral:coral@localhost:5432/coral_db"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8001"

# Initialize memory system
python -m coral_collective.memory.setup_memory
```

### Development with Hot Reload

```bash
# Set development environment
export CORAL_ENV=development
export CORAL_DEBUG=true

# Run with file watching (if implemented)
coral run --watch
```

## Production Considerations

### Security

1. **Environment Variables**: Never commit secrets to version control
   ```bash
   # Use secure secret management
   kubectl create secret generic coral-secrets --from-env-file=.env.production
   ```

2. **Network Security**: Configure firewalls and network policies
   ```yaml
   # Example NetworkPolicy
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: coral-collective-netpol
   spec:
     podSelector:
       matchLabels:
         app.kubernetes.io/name: coral-collective
     policyTypes:
     - Ingress
     - Egress
   ```

3. **Container Security**: Run as non-root user (already configured)

### Performance

1. **Resource Allocation**:
   ```yaml
   resources:
     requests:
       memory: "512Mi"
       cpu: "250m"
     limits:
       memory: "2Gi"
       cpu: "1000m"
   ```

2. **Database Optimization**:
   ```bash
   # PostgreSQL tuning for production
   # Edit postgresql.conf
   shared_buffers = 256MB
   effective_cache_size = 1GB
   work_mem = 16MB
   ```

3. **Caching Strategy**:
   ```yaml
   # Redis configuration for production
   REDIS_MAXMEMORY=1gb
   REDIS_MAXMEMORY_POLICY=allkeys-lru
   ```

### High Availability

1. **Database Replication**: Configure PostgreSQL streaming replication
2. **Load Balancing**: Use multiple replicas with HPA
3. **Backup Strategy**: Implement regular backups

```bash
# Database backup script
pg_dump $POSTGRES_URL > backup-$(date +%Y%m%d-%H%M%S).sql
```

## Monitoring and Observability

### Prometheus and Grafana

```bash
# Deploy monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000
# Login: admin/coral
```

### Health Checks

CoralCollective includes built-in health checks:

- **Liveness**: `/health/live`
- **Readiness**: `/health/ready`
- **Metrics**: `/metrics` (Prometheus format)

### Logging

Configure structured logging:

```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### Alerting

Example alert rules are configured in `monitoring/alert_rules.yml`:

- Service down alerts
- High CPU/memory usage
- Database connection failures
- Memory system issues

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check PostgreSQL status
   docker-compose ps postgres
   kubectl get pods -l app.kubernetes.io/name=postgres
   
   # Check connection
   psql $POSTGRES_URL -c "SELECT 1;"
   ```

2. **Memory System Not Working**
   ```bash
   # Check ChromaDB
   curl http://localhost:8001/api/v1/heartbeat
   
   # Verify memory system
   python -c "from coral_collective.memory.memory_system import MemorySystem; print('OK')"
   ```

3. **High Memory Usage**
   ```bash
   # Monitor memory usage
   docker stats coral-collective-dev
   kubectl top pods -n coral-collective
   ```

4. **API Keys Not Working**
   ```bash
   # Verify environment variables
   echo $CLAUDE_API_KEY | head -c 10
   
   # Test API connection
   python -c "import os; print('Claude key:', bool(os.getenv('CLAUDE_API_KEY')))"
   ```

### Debug Mode

Enable debug logging:

```bash
export CORAL_DEBUG=true
export LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f coral-collective
kubectl logs -f deployment/coral-collective -n coral-collective
```

### Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check the docs/ directory for detailed guides
- **Community**: Join our discussions (links in README.md)

## Next Steps

After successful deployment:

1. **Configure CI/CD**: Set up automated deployments
2. **Monitoring**: Configure alerts and dashboards
3. **Scaling**: Plan for growth and load testing
4. **Security**: Regular security audits and updates
5. **Backup**: Implement comprehensive backup strategy

For more information, see the individual deployment guides in this directory.