# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying the Python backend service to a Kubernetes cluster.

## Files

- `deployment.yaml` — Kubernetes Deployment for the backend service (2 replicas, resource limits, health probes)
- `service.yaml` — Kubernetes ClusterIP Service exposing the backend on port 80 → 8000

## Prerequisites

- A running Kubernetes cluster (e.g. minikube, kind, GKE, EKS, AKS)
- `kubectl` configured to point at your target cluster
- The backend Docker image built and pushed to a registry accessible by your cluster

## Building and Pushing the Docker Image

From the repository root:

```bash
docker build -t your-registry/backend:latest ./backend
docker push your-registry/backend:latest
```

Update the `image` field in `deployment.yaml` to match the image you pushed:

```yaml
image: your-registry/backend:latest
```

## Deploying to Kubernetes

Apply both manifests with `kubectl`:

```bash
kubectl apply -f infra/k8s/deployment.yaml
kubectl apply -f infra/k8s/service.yaml
```

Or apply the entire directory at once:

```bash
kubectl apply -f infra/k8s/
```

## Verifying the Deployment

Check that the Deployment and Pods are running:

```bash
kubectl get deployments
kubectl get pods
```

Check that the Service is created:

```bash
kubectl get services
```

View logs for a running pod:

```bash
kubectl logs -l app=backend
```

## Health Checks

The Deployment is configured with the following probes targeting the `/health` endpoint on port `8000`:

| Probe     | Path      | Initial Delay | Period |
|-----------|-----------|---------------|--------|
| Liveness  | `/health` | 15s           | 20s    |
| Readiness | `/health` | 5s            | 10s    |

Ensure your backend service exposes a `GET /health` endpoint that returns HTTP `200` for the probes to succeed.

## Resource Limits

Each container is configured with the following resource requests and limits:

| Resource | Request | Limit |
|----------|---------|-------|
| CPU      | 250m    | 500m  |
| Memory   | 256Mi   | 512Mi |

Adjust these values in `deployment.yaml` to suit your workload requirements.

## Tearing Down

To remove the deployed resources:

```bash
kubectl delete -f infra/k8s/
```