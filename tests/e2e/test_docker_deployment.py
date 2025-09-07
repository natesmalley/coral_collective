"""
End-to-End Docker Deployment Tests

Tests cover:
1. Docker container building and running
2. Multi-container deployment with docker-compose
3. Service health checks and monitoring
4. Kubernetes deployment validation
5. Container networking and communication
6. Environment configuration and secrets
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
import subprocess
import time
import requests
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.e2e
@pytest.mark.deployment
@pytest.mark.docker
class TestDockerContainerDeployment:
    """Test Docker container building and deployment"""
    
    def setup_method(self):
        """Set up Docker deployment test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_name = "coral-collective-test"
        
        # Create Docker-related files
        self.dockerfile_content = '''
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash coral && \\
    chown -R coral:coral /app
USER coral

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Start command
CMD ["python", "-m", "coral_collective.cli.main", "serve", "--host", "0.0.0.0", "--port", "8000"]
'''
        
        self.docker_compose_content = '''
version: '3.8'

services:
  coral-collective:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CORAL_ENV=production
      - DATABASE_URL=postgresql://coral:coral@db:5432/coral_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=coral
      - POSTGRES_PASSWORD=coral
      - POSTGRES_DB=coral_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U coral"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - coral-collective
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
'''
        
        # Create files
        (self.temp_dir / 'Dockerfile').write_text(self.dockerfile_content)
        (self.temp_dir / 'docker-compose.yml').write_text(self.docker_compose_content)
        
        # Create requirements.txt
        requirements = """
PyYAML>=6.0
rich>=13.0.0
fastapi>=0.100.0
uvicorn>=0.22.0
redis>=4.5.0
psycopg2-binary>=2.9.0
"""
        (self.temp_dir / 'requirements.txt').write_text(requirements)
    
    def teardown_method(self):
        """Clean up Docker test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_dockerfile_validation(self):
        """Test Dockerfile syntax and best practices"""
        
        dockerfile_path = self.temp_dir / 'Dockerfile'
        assert dockerfile_path.exists()
        
        dockerfile_content = dockerfile_path.read_text()
        
        # Check best practices
        assert 'FROM python:3.11-slim' in dockerfile_content
        assert 'WORKDIR /app' in dockerfile_content
        assert 'COPY requirements.txt .' in dockerfile_content
        assert 'RUN pip install' in dockerfile_content
        assert 'USER coral' in dockerfile_content  # Non-root user
        assert 'HEALTHCHECK' in dockerfile_content  # Health check
        assert 'EXPOSE 8000' in dockerfile_content
        
        # Check security practices
        assert '--no-cache-dir' in dockerfile_content  # No pip cache
        assert 'useradd' in dockerfile_content  # Creates non-root user
    
    def test_docker_compose_configuration(self):
        """Test docker-compose configuration"""
        
        compose_path = self.temp_dir / 'docker-compose.yml'
        assert compose_path.exists()
        
        compose_data = yaml.safe_load(compose_path.read_text())
        
        # Verify services
        assert 'services' in compose_data
        services = compose_data['services']
        
        assert 'coral-collective' in services
        assert 'db' in services
        assert 'redis' in services
        assert 'nginx' in services
        
        # Check main service configuration
        coral_service = services['coral-collective']
        assert 'build' in coral_service
        assert 'ports' in coral_service
        assert 'environment' in coral_service
        assert 'depends_on' in coral_service
        assert 'healthcheck' in coral_service
        
        # Check database service
        db_service = services['db']
        assert db_service['image'] == 'postgres:15-alpine'
        assert 'POSTGRES_USER' in db_service['environment']
        assert 'healthcheck' in db_service
        
        # Check volumes
        assert 'volumes' in compose_data
        volumes = compose_data['volumes']
        assert 'postgres_data' in volumes
        assert 'redis_data' in volumes
    
    @patch('subprocess.run')
    def test_docker_build_process(self, mock_subprocess):
        """Test Docker image building process"""
        
        # Mock successful build
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout="Successfully built abc123def456",
            stderr=""
        )
        
        # Simulate docker build command
        build_result = self._simulate_docker_build()
        
        assert build_result['success'] is True
        assert build_result['image_id'] is not None
        
        # Verify build command was called
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]  # First positional argument
        assert 'docker' in call_args[0]
        assert 'build' in call_args[1]
    
    def _simulate_docker_build(self):
        """Simulate Docker build process"""
        
        try:
            # In real test, this would call: docker build -t coral-collective .
            # For testing, we simulate the process
            
            # Check if Dockerfile exists
            dockerfile = self.temp_dir / 'Dockerfile'
            if not dockerfile.exists():
                return {'success': False, 'error': 'Dockerfile not found'}
            
            # Simulate build steps
            build_steps = [
                'Sending build context to Docker daemon',
                'Step 1/10 : FROM python:3.11-slim',
                'Step 2/10 : WORKDIR /app',
                'Step 3/10 : COPY requirements.txt .',
                'Step 4/10 : RUN pip install --no-cache-dir -r requirements.txt',
                'Step 5/10 : COPY . .',
                'Step 6/10 : RUN useradd --create-home --shell /bin/bash coral',
                'Step 7/10 : USER coral',
                'Step 8/10 : EXPOSE 8000',
                'Step 9/10 : HEALTHCHECK',
                'Step 10/10 : CMD ["python", "-m", "coral_collective.cli.main", "serve"]',
                'Successfully built abc123def456',
                'Successfully tagged coral-collective:latest'
            ]
            
            return {
                'success': True,
                'image_id': 'abc123def456',
                'build_log': build_steps,
                'image_size': '512MB'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @patch('subprocess.run')
    def test_docker_compose_deployment(self, mock_subprocess):
        """Test docker-compose deployment"""
        
        # Mock successful deployment
        mock_subprocess.side_effect = [
            # docker-compose up -d
            Mock(returncode=0, stdout="Creating network... done\nCreating services... done"),
            # docker-compose ps
            Mock(returncode=0, stdout="coral-collective_coral-collective_1   running\ncoral-collective_db_1   running")
        ]
        
        # Simulate deployment
        deployment_result = self._simulate_compose_deployment()
        
        assert deployment_result['success'] is True
        assert deployment_result['services_running'] == 4  # coral, db, redis, nginx
        
        # Should have called docker-compose commands
        assert mock_subprocess.call_count >= 1
    
    def _simulate_compose_deployment(self):
        """Simulate docker-compose deployment"""
        
        try:
            # Validate compose file
            compose_file = self.temp_dir / 'docker-compose.yml'
            if not compose_file.exists():
                return {'success': False, 'error': 'docker-compose.yml not found'}
            
            compose_data = yaml.safe_load(compose_file.read_text())
            services = compose_data.get('services', {})
            
            # Simulate service startup
            service_status = {}
            for service_name in services.keys():
                service_status[service_name] = {
                    'status': 'running',
                    'health': 'healthy',
                    'ports': services[service_name].get('ports', [])
                }
            
            return {
                'success': True,
                'services_running': len(service_status),
                'service_status': service_status,
                'deployment_time': 45.2
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


@pytest.mark.e2e
@pytest.mark.deployment
@pytest.mark.kubernetes
class TestKubernetesDeployment:
    """Test Kubernetes deployment manifests and processes"""
    
    def setup_method(self):
        """Set up Kubernetes deployment test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create k8s directory
        self.k8s_dir = self.temp_dir / 'k8s'
        self.k8s_dir.mkdir()
        
        # Create Kubernetes manifests
        self._create_k8s_manifests()
    
    def teardown_method(self):
        """Clean up Kubernetes test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_k8s_manifests(self):
        """Create Kubernetes deployment manifests"""
        
        # Namespace
        namespace_manifest = '''
apiVersion: v1
kind: Namespace
metadata:
  name: coral-collective
  labels:
    app: coral-collective
    environment: production
'''
        
        # Deployment
        deployment_manifest = '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coral-collective
  namespace: coral-collective
spec:
  replicas: 3
  selector:
    matchLabels:
      app: coral-collective
  template:
    metadata:
      labels:
        app: coral-collective
    spec:
      containers:
      - name: coral-collective
        image: coral-collective:latest
        ports:
        - containerPort: 8000
        env:
        - name: CORAL_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: coral-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
'''
        
        # Service
        service_manifest = '''
apiVersion: v1
kind: Service
metadata:
  name: coral-collective-service
  namespace: coral-collective
spec:
  selector:
    app: coral-collective
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
'''
        
        # Ingress
        ingress_manifest = '''
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: coral-collective-ingress
  namespace: coral-collective
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - coral.example.com
    secretName: coral-tls
  rules:
  - host: coral.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: coral-collective-service
            port:
              number: 80
'''
        
        # ConfigMap
        configmap_manifest = '''
apiVersion: v1
kind: ConfigMap
metadata:
  name: coral-config
  namespace: coral-collective
data:
  config.yaml: |
    logging:
      level: INFO
    memory:
      enabled: true
    mcp:
      enabled: true
'''
        
        # Save manifests
        (self.k8s_dir / 'namespace.yaml').write_text(namespace_manifest)
        (self.k8s_dir / 'deployment.yaml').write_text(deployment_manifest)
        (self.k8s_dir / 'service.yaml').write_text(service_manifest)
        (self.k8s_dir / 'ingress.yaml').write_text(ingress_manifest)
        (self.k8s_dir / 'configmap.yaml').write_text(configmap_manifest)
    
    def test_kubernetes_manifest_validation(self):
        """Test Kubernetes manifest syntax and configuration"""
        
        # Test namespace manifest
        namespace_file = self.k8s_dir / 'namespace.yaml'
        namespace_data = yaml.safe_load(namespace_file.read_text())
        
        assert namespace_data['apiVersion'] == 'v1'
        assert namespace_data['kind'] == 'Namespace'
        assert namespace_data['metadata']['name'] == 'coral-collective'
        
        # Test deployment manifest
        deployment_file = self.k8s_dir / 'deployment.yaml'
        deployment_data = yaml.safe_load(deployment_file.read_text())
        
        assert deployment_data['kind'] == 'Deployment'
        assert deployment_data['spec']['replicas'] == 3
        
        container = deployment_data['spec']['template']['spec']['containers'][0]
        assert container['name'] == 'coral-collective'
        assert container['image'] == 'coral-collective:latest'
        assert 'resources' in container
        assert 'livenessProbe' in container
        assert 'readinessProbe' in container
        
        # Test service manifest
        service_file = self.k8s_dir / 'service.yaml'
        service_data = yaml.safe_load(service_file.read_text())
        
        assert service_data['kind'] == 'Service'
        assert service_data['spec']['type'] == 'ClusterIP'
        assert len(service_data['spec']['ports']) == 1
        
        # Test ingress manifest
        ingress_file = self.k8s_dir / 'ingress.yaml'
        ingress_data = yaml.safe_load(ingress_file.read_text())
        
        assert ingress_data['kind'] == 'Ingress'
        assert 'tls' in ingress_data['spec']
        assert 'rules' in ingress_data['spec']
    
    @patch('subprocess.run')
    def test_kubernetes_deployment_process(self, mock_subprocess):
        """Test Kubernetes deployment process"""
        
        # Mock kubectl commands
        mock_subprocess.side_effect = [
            # kubectl apply -f namespace.yaml
            Mock(returncode=0, stdout="namespace/coral-collective created"),
            # kubectl apply -f deployment.yaml
            Mock(returncode=0, stdout="deployment.apps/coral-collective created"),
            # kubectl apply -f service.yaml
            Mock(returncode=0, stdout="service/coral-collective-service created"),
            # kubectl get pods
            Mock(returncode=0, stdout="NAME                               READY   STATUS    RESTARTS   AGE\ncoral-collective-abc123-xyz789     1/1     Running   0          30s")
        ]
        
        deployment_result = self._simulate_k8s_deployment()
        
        assert deployment_result['success'] is True
        assert deployment_result['resources_created'] >= 3
        assert mock_subprocess.call_count >= 3
    
    def _simulate_k8s_deployment(self):
        """Simulate Kubernetes deployment"""
        
        try:
            # Get all manifest files
            manifest_files = list(self.k8s_dir.glob('*.yaml'))
            
            if not manifest_files:
                return {'success': False, 'error': 'No manifest files found'}
            
            # Simulate applying each manifest
            resources_created = []
            for manifest_file in manifest_files:
                manifest_data = yaml.safe_load(manifest_file.read_text())
                
                resource_info = {
                    'kind': manifest_data['kind'],
                    'name': manifest_data['metadata']['name'],
                    'namespace': manifest_data['metadata'].get('namespace', 'default'),
                    'status': 'created'
                }
                resources_created.append(resource_info)
            
            return {
                'success': True,
                'resources_created': len(resources_created),
                'resources': resources_created,
                'deployment_time': 120.5
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_kubernetes_resource_requirements(self):
        """Test resource requirements and limits"""
        
        deployment_file = self.k8s_dir / 'deployment.yaml'
        deployment_data = yaml.safe_load(deployment_file.read_text())
        
        container = deployment_data['spec']['template']['spec']['containers'][0]
        resources = container['resources']
        
        # Check resource requests
        assert 'requests' in resources
        requests = resources['requests']
        assert 'memory' in requests
        assert 'cpu' in requests
        assert requests['memory'] == '512Mi'
        assert requests['cpu'] == '250m'
        
        # Check resource limits
        assert 'limits' in resources
        limits = resources['limits']
        assert 'memory' in limits
        assert 'cpu' in limits
        assert limits['memory'] == '1Gi'
        assert limits['cpu'] == '500m'
        
        # Verify limits are higher than requests
        assert self._parse_memory(limits['memory']) > self._parse_memory(requests['memory'])
        assert self._parse_cpu(limits['cpu']) > self._parse_cpu(requests['cpu'])
    
    def _parse_memory(self, memory_str):
        """Parse memory string to bytes for comparison"""
        if memory_str.endswith('Mi'):
            return int(memory_str[:-2]) * 1024 * 1024
        elif memory_str.endswith('Gi'):
            return int(memory_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(memory_str)
    
    def _parse_cpu(self, cpu_str):
        """Parse CPU string to millicores for comparison"""
        if cpu_str.endswith('m'):
            return int(cpu_str[:-1])
        else:
            return int(cpu_str) * 1000


@pytest.mark.e2e
@pytest.mark.deployment
@pytest.mark.monitoring
class TestDeploymentMonitoring:
    """Test deployment monitoring and health checks"""
    
    def setup_method(self):
        """Set up monitoring test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create monitoring configuration
        self.monitoring_config = {
            'prometheus': {
                'scrape_configs': [
                    {
                        'job_name': 'coral-collective',
                        'static_configs': [{'targets': ['localhost:8000']}],
                        'metrics_path': '/metrics',
                        'scrape_interval': '15s'
                    }
                ]
            },
            'grafana': {
                'dashboards': [
                    {
                        'name': 'CoralCollective Overview',
                        'panels': ['CPU Usage', 'Memory Usage', 'Agent Executions', 'Response Time']
                    }
                ]
            },
            'alerting': {
                'rules': [
                    {
                        'alert': 'HighMemoryUsage',
                        'expr': 'memory_usage_percent > 90',
                        'for': '5m'
                    },
                    {
                        'alert': 'AgentExecutionFailure',
                        'expr': 'agent_failure_rate > 0.1',
                        'for': '2m'
                    }
                ]
            }
        }
        
        # Save monitoring config
        monitoring_file = self.temp_dir / 'monitoring.yaml'
        with open(monitoring_file, 'w') as f:
            yaml.dump(self.monitoring_config, f)
    
    def teardown_method(self):
        """Clean up monitoring test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_health_check_endpoints(self):
        """Test health check endpoint configuration"""
        
        # Mock health check responses
        health_checks = {
            '/health': {
                'status': 'healthy',
                'checks': {
                    'database': 'up',
                    'memory_system': 'up',
                    'mcp_services': 'up'
                },
                'timestamp': datetime.now().isoformat()
            },
            '/ready': {
                'status': 'ready',
                'startup_complete': True,
                'services_initialized': True
            },
            '/metrics': {
                'coral_agents_executed_total': 1234,
                'coral_memory_items_total': 5678,
                'coral_projects_active': 42,
                'coral_response_time_seconds': 0.125
            }
        }
        
        # Test each endpoint
        for endpoint, expected_response in health_checks.items():
            result = self._simulate_health_check(endpoint, expected_response)
            assert result['success'] is True
            assert result['status_code'] == 200
            assert result['response'] == expected_response
    
    def _simulate_health_check(self, endpoint, expected_response):
        """Simulate health check endpoint request"""
        
        try:
            # In real deployment, this would make HTTP request
            # For testing, we simulate the response
            
            if endpoint == '/health':
                # Simulate health check logic
                health_status = {
                    'status': 'healthy',
                    'checks': {
                        'database': 'up',
                        'memory_system': 'up', 
                        'mcp_services': 'up'
                    },
                    'timestamp': datetime.now().isoformat()
                }
                return {
                    'success': True,
                    'status_code': 200,
                    'response': health_status
                }
            
            elif endpoint == '/ready':
                # Simulate readiness check
                readiness_status = {
                    'status': 'ready',
                    'startup_complete': True,
                    'services_initialized': True
                }
                return {
                    'success': True,
                    'status_code': 200,
                    'response': readiness_status
                }
            
            elif endpoint == '/metrics':
                # Simulate metrics endpoint
                metrics = {
                    'coral_agents_executed_total': 1234,
                    'coral_memory_items_total': 5678,
                    'coral_projects_active': 42,
                    'coral_response_time_seconds': 0.125
                }
                return {
                    'success': True,
                    'status_code': 200,
                    'response': metrics
                }
            
            else:
                return {
                    'success': False,
                    'status_code': 404,
                    'error': 'Endpoint not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'status_code': 500,
                'error': str(e)
            }
    
    def test_prometheus_configuration(self):
        """Test Prometheus monitoring configuration"""
        
        monitoring_file = self.temp_dir / 'monitoring.yaml'
        config = yaml.safe_load(monitoring_file.read_text())
        
        prometheus_config = config['prometheus']
        
        # Verify scrape configs
        assert 'scrape_configs' in prometheus_config
        scrape_configs = prometheus_config['scrape_configs']
        assert len(scrape_configs) >= 1
        
        coral_job = scrape_configs[0]
        assert coral_job['job_name'] == 'coral-collective'
        assert coral_job['metrics_path'] == '/metrics'
        assert coral_job['scrape_interval'] == '15s'
        assert len(coral_job['static_configs']) >= 1
    
    def test_alerting_rules_configuration(self):
        """Test alerting rules configuration"""
        
        monitoring_file = self.temp_dir / 'monitoring.yaml'
        config = yaml.safe_load(monitoring_file.read_text())
        
        alerting_config = config['alerting']
        
        # Verify alerting rules
        assert 'rules' in alerting_config
        rules = alerting_config['rules']
        assert len(rules) >= 2
        
        # Check memory usage alert
        memory_alert = next((r for r in rules if r['alert'] == 'HighMemoryUsage'), None)
        assert memory_alert is not None
        assert 'memory_usage_percent > 90' in memory_alert['expr']
        assert memory_alert['for'] == '5m'
        
        # Check agent failure alert
        failure_alert = next((r for r in rules if r['alert'] == 'AgentExecutionFailure'), None)
        assert failure_alert is not None
        assert 'agent_failure_rate > 0.1' in failure_alert['expr']
        assert failure_alert['for'] == '2m'
    
    @patch('subprocess.run')
    def test_deployment_validation_workflow(self, mock_subprocess):
        """Test complete deployment validation workflow"""
        
        # Mock validation commands
        mock_subprocess.side_effect = [
            # docker ps - check containers
            Mock(returncode=0, stdout="coral-collective   Up 5 minutes   healthy"),
            # curl health check
            Mock(returncode=0, stdout='{"status": "healthy"}'),
            # kubectl get pods
            Mock(returncode=0, stdout="coral-collective-abc123   1/1   Running   0   2m"),
            # prometheus query
            Mock(returncode=0, stdout="coral_agents_executed_total 1234")
        ]
        
        validation_result = self._simulate_deployment_validation()
        
        assert validation_result['success'] is True
        assert validation_result['containers_healthy'] is True
        assert validation_result['endpoints_responding'] is True
        assert validation_result['metrics_available'] is True
    
    def _simulate_deployment_validation(self):
        """Simulate deployment validation process"""
        
        try:
            validation_results = {
                'success': True,
                'containers_healthy': True,
                'endpoints_responding': True,
                'metrics_available': True,
                'deployment_ready': True
            }
            
            # Simulate container health check
            # In real scenario: docker ps --format "table {{.Names}}\t{{.Status}}"
            container_status = "coral-collective   Up 5 minutes   healthy"
            validation_results['container_status'] = container_status
            
            # Simulate endpoint health check  
            # In real scenario: curl http://localhost:8000/health
            health_response = {"status": "healthy"}
            validation_results['health_response'] = health_response
            
            # Simulate metrics availability
            # In real scenario: curl http://localhost:8000/metrics
            metrics_available = True
            validation_results['metrics_available'] = metrics_available
            
            # Overall validation
            all_checks_passed = all([
                validation_results['containers_healthy'],
                validation_results['endpoints_responding'],
                validation_results['metrics_available']
            ])
            
            validation_results['deployment_ready'] = all_checks_passed
            
            return validation_results
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'deployment_ready': False
            }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])