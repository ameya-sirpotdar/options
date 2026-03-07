# Kubernetes Manifests

This directory contains the Kubernetes manifests for deploying the Python backend service to a Kubernetes cluster.

## Files

- `deployment.yaml` — Kubernetes `Deployment` resource for the Python backend service
- `service.yaml` — Kubernetes `ClusterIP` `Service` resource that exposes the backend pods internally within the cluster

## Prerequisites

- A running Kubernetes cluster (e.g. minikube, kind, GKE, EKS, AKS)
- `kubectl` configured to point at your target cluster
- The backend Docker image built and pushed to a container registry accessible by the cluster

## Deployment

### 1. Build and push the Docker image

From the repository root:

```bash
docker build -t your-registry/backend:latest ./backend
docker push your-registry/backend:latest
```

Replace `your-registry/backend:latest` with your actual image name and tag.

### 2. Update the image reference

Edit `deployment.yaml` and set the `image` field under `spec.template.spec.containers` to match the image you pushed:

```yaml
image: your-registry/backend:latest
```

### 3. Apply the manifests

```bash
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
```

Or apply the entire directory at once:

```bash
kubectl apply -f infra/k8s/
```

### 4. Verify the deployment

Check that the pods are running:

```bash
kubectl get pods -l app=backend
```

Check the service:

```bash
kubectl get svc backend
```

## Configuration

### Replicas

The deployment is configured with **2 replicas** by default for high availability. To scale the deployment:

```bash
kubectl scale deployment backend --replicas=<desired-count>
```

### Resource Limits

The following resource requests and limits are configured per container:

| Resource | Request | Limit  |
|----------|---------|--------|
| CPU      | 100m    | 500m   |
| Memory   | 128Mi   | 512Mi  |

Adjust these values in `deployment.yaml` to suit your workload requirements.

### Health Checks

The deployment includes both liveness and readiness probes targeting the `/health` endpoint on port `8000`:

- **Readiness probe** — determines when the pod is ready to receive traffic
- **Liveness probe** — determines when the pod should be restarted

### Environment Variables

Add any required environment variables to the `env` section of the container spec in `deployment.yaml`, or reference them from a `ConfigMap` or `Secret`.

## Teardown

To remove the deployed resources:

```bash
kubectl delete -f infra/k8s/
```