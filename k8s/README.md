# In-cluster Redis and PostgreSQL

Deploy Redis and PostgreSQL into the `proteus` namespace before the rest of the stack.

## 1. Create bootstrap secrets

Create the credentials that Redis and PostgreSQL will use. Use the **same** values later in `proteus-secrets` so the app and KEDA can connect.

```bash
# Redis (use a strong password; set the same value as REDIS_PASSWORD in proteus-secrets)
kubectl create secret generic redis-credentials -n proteus \
  --from-literal=redis-password='YOUR_REDIS_PASSWORD'

# PostgreSQL
kubectl create secret generic postgres-credentials -n proteus \
  --from-literal=postgres-user=proteus \
  --from-literal=postgres-password='YOUR_PG_PASSWORD' \
  --from-literal=postgres-db=proteus
```

## 2. Deploy Redis and PostgreSQL

From `proteus-backend`:

```bash
# Namespace first if not already created
kubectl apply -f namespace.yaml

# Redis
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# PostgreSQL (Service must exist before StatefulSet for headless DNS)
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
```

Wait until pods are ready: `kubectl get pods -n proteus -w`

## 3. Create proteus-secrets with in-cluster URLs

Use the **same** Redis password and Postgres user/password/db as in step 1:

```bash
kubectl create secret generic proteus-secrets -n proteus \
  --from-literal=DATABASE_URL='postgresql://proteus:YOUR_PG_PASSWORD@postgres.proteus.svc.cluster.local:5432/proteus' \
  --from-literal=REDIS_URL='redis://:YOUR_REDIS_PASSWORD@redis.proteus.svc.cluster.local:6379/0' \
  --from-literal=REDIS_HOST='redis.proteus.svc.cluster.local:6379' \
  --from-literal=REDIS_PASSWORD='YOUR_REDIS_PASSWORD' \
  --from-literal=JWT_SECRET='your-jwt-secret' \
  # Add S3/Object Storage, etc.
```

Then deploy Gateway, Weaver, HPA, and KEDA as in the main deployment runbook.
