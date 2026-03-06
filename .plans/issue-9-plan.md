# Implementation Plan: Kubernetes Deployment Configuration for Python Backend

## Approach

We will create three artifacts:
1. A `Dockerfile` in the `backend/` directory using a slim Python base image
2. A Kubernetes `Deployment` manifest in `infra/k8s/`
3. A Kubernetes `Service` manifest in `infra/k8s/`

Since the backend has no `main.py` or application entrypoint yet, we will write the Dockerfile with a sensible default entrypoint (e.g., `uvicorn` for a FastAPI/ASGI app or `gunicorn`) and leave it easy to override. We will inspect `backend/requirements.txt` to infer the framework in use.

---

## Files to Create

### 1. `backend/Dockerfile`
- Use `python:3.11-slim` as the base image
- Set a non-root user for security
- Copy and install `requirements.txt` first (layer caching)
- Copy application source
- Expose port `8000`
- Default `CMD` using `uvicorn` (adjust if requirements indicate a different framework)

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. `infra/k8s/deployment.yaml`
- `apiVersion: apps/v1`, `kind: Deployment`
- Namespace: `default` (can be parameterised later)
- 2 replicas for basic availability
- Container image: placeholder `<ACR_NAME>.azurecr.io/backend:latest` (to be substituted by CI/CD)
- Resource requests/limits set conservatively
- Liveness and readiness probes on `/health` (HTTP GET, port 8000)
- `imagePullPolicy: Always`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: default
  labels:
    app: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: <ACR_NAME>.azurecr.io/backend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
```

### 3. `infra/k8s/service.yaml`
- `kind: Service`, type `ClusterIP` (internal cluster exposure as required by AC)
- Selects pods with label `app: backend`
- Maps port 80 → targetPort 8000

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: default
  labels:
    app: backend
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
```

### 4. `infra/k8s/README.md`
- Brief documentation explaining the manifests, how to substitute the ACR image name, and how to apply them with `kubectl`

---

## Files to Modify

### `infra/README.md`
- Add a section referencing the new `k8s/` directory and how it relates to the AKS cluster provisioned via Bicep

### `tests/test_project_structure.py`
- Add assertions that `backend/Dockerfile`, `infra/k8s/deployment.yaml`, and `infra/k8s/service.yaml` exist

---

## Implementation Steps

1. **Inspect `backend/requirements.txt`** — confirm the web framework (FastAPI, Flask, Django, etc.) to set the correct `CMD` in the Dockerfile.
2. **Create `backend/Dockerfile`** — use `python:3.11-slim`, non-root user, install deps, copy source, expose 8000.
3. **Create `infra/k8s/` directory** with `deployment.yaml` and `service.yaml` as specified above.
4. **Create `infra/k8s/README.md`** with usage instructions.
5. **Update `infra/README.md`** to reference the k8s manifests.
6. **Update `tests/test_project_structure.py`** to assert the new files exist.
7. **Validate YAML** — run `kubectl apply --dry-run=client -f infra/k8s/` locally or in CI to confirm manifest validity.

---

## Test Strategy

- **Structural tests**: Extend `tests/test_project_structure.py` to assert `backend/Dockerfile`, `infra/k8s/deployment.yaml`, and `infra/k8s/service.yaml` exist.
- **Dockerfile lint**: Run `hadolint backend/Dockerfile` in CI to catch best-practice violations.
- **YAML validation**: `kubectl apply --dry-run=client -f infra/k8s/` against a kubeconfig (or use `kubeval`/`kubeconform` in CI without a live cluster).
- **Docker build test**: `docker build -t backend-test ./backend` in CI to confirm the image builds without errors.
- **Integration (manual/AKS)**: Deploy to the AKS cluster from Story 1.3 and confirm pods reach `Running` state and the Service is reachable within the cluster.

---

## Edge Cases to Handle

- If `requirements.txt` does not include `uvicorn`, adjust `CMD` to match the actual server (e.g., `gunicorn`, `flask run`).
- The `api.main:app` module path in `CMD` assumes a `main.py` in `backend/api/`. If the entrypoint differs, update accordingly.
- The `<ACR_NAME>` placeholder must be documented clearly so CI/CD pipelines know to substitute it.
- The `/health` probe endpoint must exist in the application; if it does not yet, note this as a dependency.
