# COMPSs Kubernetes Deployment

This repository provides infrastructure for deploying COMPSs (COMP Superscalar) applications on Kubernetes using Helm charts and building multi-architecture Docker images.

## Overview

- **Helm Chart**: Deploy COMPSs applications with master/worker architecture
- **Multi-arch Support**: Build images for AMD64 and ARM64 architectures
- **Kubernetes Integration**: Automated builder setup using Kubernetes driver
- **Monitoring**: Optional Prometheus integration for performance metrics

## Prerequisites

- Kubernetes cluster with kubectl configured
- Docker with buildx plugin
- Helm 3.x
- Access to a Docker registry

## Quick Start

### 1. Prepare Build Environment

```bash
make prepare
```

This will:
- Create buildkit namespace if needed
- Set up multi-architecture Docker builders for available node types
- Configure Kubernetes container driver for builds

### 2. Deploy COMPSs Application

```bash
cd helm-compss
helm install my-compss-app . -f values.yaml
```

## Configuration

### Helm Values (`helm-compss/values.yaml`)

#### Application Settings
```yaml
image:
  repository: oriolmac/build-test
  tag: latest
  pullPolicy: IfNotPresent

app:
  context:
    folderPath: /home/omartinez/compss-matmul/matmul-extract
    file: matmul.py
  params:
    num_blocks: "3"
    elems_per_block: "1024"
    number_iterations: "1"
```

#### COMPSs Cluster Configuration
```yaml
compss:
  master:
    volume: 
      localPath: /home/minikube
      node: minikube
    prometheusClient: 
      enabled: false
      containerPort: 15000

  worker:
    number: 2
    resources:
      cpu: 1
      memory: 2  # in gigabytes
```

#### Optional MQTT Integration
```yaml
mqtt:
  enabled: false
  port: 1883
  nodePort: 31883
```

#### Monitoring (Prometheus)
```yaml
monitoring:
  enabled: true
  port: 15000
  prometheusUrl: http://prometheus-kube-prometheus-prometheus.monitoring.svc:9090
```

## Building Custom Images

### Image Tags Configuration

Edit the Makefile variables to customize your build:

```makefile
PREFIX           := oriolmac
COMPSS_VERSION   := 3.3
MIN_BASE_TAG     := min_base
FULL_BASE_TAG    := full_base
COMPSS_TAG       := compss_heuristics
DEBUG_TAG        := compss_debug
```

### Multi-Architecture Builds

The build system automatically detects available Kubernetes node architectures:
- **AMD64**: Creates builder for x86_64 nodes
- **ARM64**: Creates builder for ARM-based nodes

## Architecture

### Components

1. **Master Node**: Coordinates task execution and manages workers
2. **Worker Nodes**: Execute COMPSs tasks in parallel
3. **MQTT Broker** (optional): Message queuing for distributed communication
4. **Monitoring API**: Prometheus metrics collection

### Kubernetes Resources

- **Deployments**: Master and worker pod management
- **Services**: Internal communication and external access
- **ServiceAccount/RBAC**: Permissions for cluster operations
- **PVC/PV**: Persistent storage for master node
- **ServiceMonitor**: Prometheus scraping configuration

## Commands

### Environment Management
```bash
# Show available targets and environment info
make help

# Prepare build environment
make prepare

# Clean up builders and resources
make clean
```

### Helm Operations
```bash
# Install COMPSs application
helm install <release-name> ./helm-compss

# Upgrade existing deployment
helm upgrade <release-name> ./helm-compss

# Uninstall
helm uninstall <release-name>

# Check status
helm status <release-name>
```

## Development

### Adding New Applications

1. Build your application Docker image with COMPSs runtime
2. Update `values.yaml` with your image repository and tag
3. Configure application context and parameters
4. Deploy using Helm

### Custom Schedulers

Configure vertical scalability in `values.yaml`:

```yaml
compss:
  master:
    scheduler_config:
      vertical_scalability: "true"
      vertical_increasing_cpus: 2
      vertical_scaling_up_taskThreshold: "115"
```

## Troubleshooting

### Builder Issues
- Ensure Kubernetes nodes are Ready and accessible
- Check namespace permissions: `kubectl get pods -n buildkit`
- Verify Docker buildx installation

### Deployment Issues
- Check pod logs: `kubectl logs <pod-name>`
- Verify persistent volume mounting
- Confirm image pull policies and registry access

### Monitoring
- Ensure Prometheus is deployed in the monitoring namespace
- Check ServiceMonitor configuration
- Verify port accessibility between components

## Version

- **Chart Version**: 0.0.4
- **COMPSs Version**: 3.3.1