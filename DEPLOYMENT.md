# Full step-by-step: Deploy Proteus on LKE

Deploy Proteus to **Akamai Linode Kubernetes Engine (LKE)** with in-cluster Redis and PostgreSQL. Local development stays on Docker Compose.

All commands assume you are in `proteus-backend` unless noted.

---

## Step 1: Create the LKE cluster

1. In **Akamai Cloud Manager**, create a Kubernetes cluster (region and version of your choice).
2. Add at least one **general-purpose node pool** (for Gateway, Arbitrator, Tailor).
3. If you need **Weaver on GPU**: add a **GPU node pool** (NVIDIA RTX 4000 Ada). Use **standard LKE** (not LKE Enterprise). Enable **node pool autoscaling** (min/max nodes) for the GPU pool so KEDA can scale Weaver pods and the cluster can add nodes.

---

## Step 2: Connect to the cluster

1. Install **kubectl** if needed.
2. From LKE, download the kubeconfig (e.g. “Download kubeconfig”).
3. Set `KUBECONFIG` or merge the file into `~/.kube/config`.
4. Verify:

   ```bash
   kubectl get nodes
   ```

---

## Step 3: Install KEDA

KEDA is not pre-installed on LKE.

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda -n keda --create-namespace
```

---

## Step 4: (GPU only) Install NVIDIA device plugin or GPU Operator

Only if you run Weaver on GPU:

- Install the [NVIDIA Kubernetes device plugin](https://techdocs.akamai.com/cloud-computing/docs/gpus-on-lke), or  
- Install the NVIDIA GPU Operator with `driver.enabled=false` and `toolkit.enabled=false` (drivers are pre-installed on LKE GPU nodes).

---

## Step 5: Create the `proteus` namespace

```bash
kubectl apply -f namespace.yaml
```

---

## Step 6: Create bootstrap secrets for Redis and PostgreSQL

Create the credentials that the Redis and Postgres pods will use. **Use the same values** in Step 8 when creating `proteus-secrets`. Replace `YOUR_REDIS_PASSWORD` and `YOUR_PG_PASSWORD` with strong values.

```bash
# Redis
kubectl create secret generic redis-credentials -n proteus \
  --from-literal=redis-password='YOUR_REDIS_PASSWORD'

# PostgreSQL
kubectl create secret generic postgres-credentials -n proteus \
  --from-literal=postgres-user=proteus \
  --from-literal=postgres-password='YOUR_PG_PASSWORD' \
  --from-literal=postgres-db=proteus
```

---

## Step 7: Deploy Redis and PostgreSQL

Apply the in-cluster database manifests in this order:

```bash
# Redis
kubectl apply -f k8s/redis-pvc.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# PostgreSQL (Service before StatefulSet)
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
```

Wait until Redis and Postgres pods are ready:

```bash
kubectl get pods -n proteus -w
```

Press Ctrl+C when `redis-*` and `postgres-0` show `Running` and ready.

---

## Step 8: Create the `proteus-secrets` Secret

Create the app secret using the **same** Redis password and Postgres user/password/db as in Step 6. Replace placeholders and add any extra keys your app needs (e.g. S3, JWT).

```bash
kubectl create secret generic proteus-secrets -n proteus \
  --from-literal=DATABASE_URL='postgresql://proteus:YOUR_PG_PASSWORD@postgres.proteus.svc.cluster.local:5432/proteus' \
  --from-literal=REDIS_URL='redis://:YOUR_REDIS_PASSWORD@redis.proteus.svc.cluster.local:6379/0' \
  --from-literal=REDIS_HOST='redis.proteus.svc.cluster.local:6379' \
  --from-literal=REDIS_PASSWORD='YOUR_REDIS_PASSWORD' \
  --from-literal=JWT_SECRET='your-jwt-secret'
```

Add S3/Object Storage and other vars as needed (see `.env.example`), for example:

```bash
kubectl create secret generic proteus-secrets -n proteus \
  --from-literal=DATABASE_URL='postgresql://proteus:YOUR_PG_PASSWORD@postgres.proteus.svc.cluster.local:5432/proteus' \
  --from-literal=REDIS_URL='redis://:YOUR_REDIS_PASSWORD@redis.proteus.svc.cluster.local:6379/0' \
  --from-literal=REDIS_HOST='redis.proteus.svc.cluster.local:6379' \
  --from-literal=REDIS_PASSWORD='YOUR_REDIS_PASSWORD' \
  --from-literal=JWT_SECRET='your-jwt-secret' \
  --from-literal=AWS_ACCESS_KEY_ID='...' \
  --from-literal=AWS_SECRET_ACCESS_KEY='...' \
  --from-literal=AWS_REGION='us-east-1' \
  --from-literal=S3_BUCKET='your-bucket'
```

If the secret already exists, delete it first or use `kubectl create secret generic ... --dry-run=client -o yaml | kubectl apply -f -` and merge keys manually.

---

## Step 9: Build and push images

Build and push the Gateway, Weaver, and Arbitrator images to a registry your cluster can pull from (e.g. Docker Hub, Linode Container Registry). Update the image fields in the deployment YAMLs if you use a different registry or tag.

Example from `proteus-backend` (replace with your registry and tags):

```bash
# Gateway (adjust path to Dockerfile if your layout differs)
docker build -t your-registry/proteus-gateway:latest -f gateway/Dockerfile .
docker push your-registry/proteus-gateway:latest

# Weaver
docker build -t your-registry/weaver:latest -f weaver_service/Dockerfile .
docker push your-registry/weaver:latest

# Arbitrator
docker build -t your-registry/arbitrator:latest -f arbitrator/Dockerfile .
docker push your-registry/arbitrator:latest
```

Update `gateway-deployment.yaml`, `weaver_service/weaver-deployment.yaml`, and `arbitrator/arbitrator-deployment.yaml` with the correct image names if they differ from the defaults.

---

## Step 10: Deploy the Gateway

```bash
kubectl apply -f gateway-deployment.yaml
kubectl apply -f gateway-service.yaml
kubectl apply -f gateway-hpa.yaml
```

---

## Step 11: Deploy the Weaver

```bash
kubectl apply -f weaver_service/weaver-deployment.yaml
kubectl apply -f weaver_service/keda-redis-trigger-auth.yaml
kubectl apply -f weaver_service/weaver-keda-scaledobject.yaml
```

---

## Step 12: (Optional) Pin Weaver to GPU nodes

If you have a dedicated GPU node pool, edit `weaver_service/weaver-deployment.yaml` and set the `nodeSelector` to match your GPU pool (e.g. uncomment and set `lke.linode.com/pool-id` to your GPU pool ID).

---

## Step 13: Deploy the Arbitrator

The Arbitrator is the meta-scheduler control loop: it reads `queue:weaver_jobs` depth from Redis and sets `config:batch_size`. It runs as a single replica and uses `proteus-secrets` for `REDIS_URL`.

```bash
kubectl apply -f arbitrator/arbitrator-deployment.yaml
```

No Service is needed (nothing connects to the Arbitrator). If you have manifests for **Tailor**, apply them here as well and ensure they use `proteus-secrets`.

---

## Step 14: Verify

Check that pods are running:

```bash
kubectl get pods -n proteus
kubectl get hpa -n proteus
kubectl get scaledobject -n proteus
```

---

## Step 15: Get the Gateway URL

LKE provisions a NodeBalancer for the Gateway Service. Get the external IP:

```bash
kubectl get svc proteus-gateway -n proteus
```

Open **http://&lt;EXTERNAL-IP&gt;** (port 80) in a browser to reach the gateway.

---

## Quick reference: deployment order

| Step | What |
|------|------|
| 1 | Create LKE cluster and node pools (enable GPU pool autoscaling if using GPU) |
| 2 | Connect kubectl to the cluster |
| 3 | Install KEDA (Helm) |
| 4 | (GPU only) Install NVIDIA device plugin or GPU Operator |
| 5 | Create namespace `proteus` |
| 6 | Create `redis-credentials` and `postgres-credentials` secrets |
| 7 | Deploy Redis (PVC, Deployment, Service) and PostgreSQL (Service, StatefulSet) from `k8s/` |
| 8 | Create `proteus-secrets` with in-cluster DATABASE_URL, REDIS_URL, REDIS_HOST, REDIS_PASSWORD, and app vars |
| 9 | Build and push Gateway, Weaver, and Arbitrator images; update deployment image fields if needed |
| 10 | Deploy Gateway (Deployment, Service, HPA) |
| 11 | Deploy Weaver (Deployment, KEDA TriggerAuthentication, ScaledObject) |
| 12 | (Optional) Set Weaver nodeSelector for GPU pool |
| 13 | Deploy Arbitrator (`arbitrator/arbitrator-deployment.yaml`); Tailor if you have manifests |
| 14 | Verify pods, HPA, and ScaledObject |
| 15 | Get Gateway external IP and open in browser |

---

## Production notes

- **Backups:** Back up Redis and PostgreSQL data (PVCs). Use your storage class and backup tooling (e.g. snapshots, backup jobs).
- **Secrets:** Prefer a secret manager or GitOps (e.g. sealed-secrets, external-secrets) for production instead of one-off `kubectl create secret`.
- **Redis/Postgres:** For higher availability, consider managed Redis/PostgreSQL or multi-replica setups; the manifests in `k8s/` are single-replica for simplicity.
