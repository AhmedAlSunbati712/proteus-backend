# Proteus — Technical Specification & Architecture

> **Project Name:** Proteus  
> **Subtitle:** An Event-Driven, Intelligent Orchestration Engine for Real-Time GenAI Virtual Try-On  
> **Target Platform:** Akamai Linode Kubernetes Engine (LKE)

This document serves as the blueprint for development and the pitch deck for hackathon judges. It addresses: **Advanced Kubernetes (KEDA)**, **GPU Acceleration**, **Scalability**, and **Open Source Innovation**.

**Demo video:** [https://youtu.be/D6bWGE5YtJ0](https://youtu.be/D6bWGE5YtJ0)

[![Proteus demo video](https://img.youtube.com/vi/D6bWGE5YtJ0/maxresdefault.jpg)](https://youtu.be/D6bWGE5YtJ0)


---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Component Specifications](#3-component-specifications)
4. [Advanced Kubernetes Integration (KEDA)](#4-advanced-kubernetes-integration-keda)
5. [Frontend: Puppet AR Visualization](#5-frontend-puppet-ar-visualization)
6. [Data Flow (User Journey)](#6-data-flow-user-journey)
7. [Redis Schema](#7-redis-schema)
8. [API Reference](#8-api-reference)
9. [Akamai / Linode Resource Mapping](#9-akamai--linode-resource-mapping)
10. [Why This Wins](#10-why-this-wins)
11. [Infrastructure & Deployment](#11-infrastructure--deployment)

---

## 1. Executive Summary

Proteus is not just a virtual try-on application; it is a **distributed system designed to solve the economic viability of Generative AI at scale**.

While traditional AI apps crash under load or burn cash on idle GPUs, Proteus introduces a **"Meta-Scheduler" (The Arbitrator)**. This intelligent control plane continuously monitors traffic and dynamically reconfigures the infrastructure—switching between **"High Fidelity / Low Latency"** modes and **"High Throughput / Batching"** modes in real-time.

Built entirely on **Akamai Linode Kubernetes Engine (LKE)**, it leverages **KEDA** (Kubernetes Event-Driven Autoscaling) and **NVIDIA GPUs** to demonstrate the future of elastic, cost-aware AI infrastructure.

---

## 2. System Architecture

The system is composed of **4 microservices** and **1 frontend client**, a PostgreSQL DB to store users and their images/outfits/...etc, a websocket to notify clients of finished jobs and also a redis db to store job queues.

### 2.1 High-Level Diagram

![Screenshot 2026-02-05 at 2.39.58 PM](https://hackmd.io/_uploads/SkekXdGPZl.png)


### 2.2 Component Overview

| Component | Stack | Role |
|-----------|-------|------|
| **Gateway** | Node.js (Express) + Socket.io | Traffic cop: uploads, routing, real-time delivery |
| **Tailor** | Python + PyTorch (CPU) | Pre-processor: semantic segmentation |
| **Weaver** | Python + PyTorch (GPU) | Inference: high-fidelity virtual try-on |
| **Arbitrator** | Node.js (control loop) | Meta-scheduler: dynamic policy based on queue depth |
| **Frontend** | React + Three.js + MediaPipe | Puppet AR visualization |

---

## 3. Component Specifications

### A. The Gateway (The Traffic Cop)

| Property | Value |
|----------|-------|
| **Stack** | Node.js (Express) + Socket.io |
| **Role** | Handles high-concurrency connections, and real-time notifications |

**Key Logic:**

- **Async Processing:** Never blocks. Offloads all heavy lifting to Redis queues.
- **The "Sanity Check":** Handles generating presigned upload and download URLs for the S3 bucket. Receives job requests from the client: outfit-cleaning jobs are pushed to `queue:tailor_jobs`, try-on jobs to `queue:weaver_jobs`.
- **WebSocket Delivery:** Subscribes to Redis channel `events:job_done`; uses `user_id` in each message to route the result to the correct client's WebSocket. The WebSocket runs on an HTTP route (e.g. `/updates`).
#### Routes
```
User Service Routes
- CRUD
VTON service routes:
- CRUD
Images
- GET /images/presignedUpUrl
- GET /images/presignedDownloadUrl
Jobs
- POST /segformer/segmentOutfitPic
- POST /catvton/transferOutfit
```

---

### B. The Tailor (The Pre-Processor)

| Property | Value |
|----------|-------|
| **Stack** | Python + PyTorch (CPU) |
| **Model** | SegFormer (`mattmdjaga/segformer_b2_clothes`) |
| **Role** | Semantic segmentation of clothing |

**I/O:**

| Stage | Description |
|-------|-------------|
| **Input** | Raw image of a model wearing an outfit |
| **Action** | Detects pixel class 4 (Upper Clothes), creates binary mask, removes background/body |
| **Output** | Transparent PNG of the outfit only |

**Why it wins:** Solves the "dirty data" problem automatically—users can upload product photos, not pre-cleaned assets.
- It listens on the `queue:tailor_jobs` queue for incoming jobs.
- It takes the S3 key of the image to be cleaned, gets a presigned download URL, downloads the image, processes it, uploads the result to S3, and publishes to the `events:job_done` channel with a payload including `job_type: "outfit_clean"`, the result S3 key, status, `user_id`, and `vton_id`. The Gateway subscribes to `events:job_done` and pushes the result to the correct client over WebSocket, updating the corresponding VTON entry with the S3 key for the transparent PNG of the outfit.

---

### C. The Weaver (The GPU Muscle)

| Property | Value |
|----------|-------|
| **Stack** | Python + PyTorch + Diffusers |
| **Hardware** | Linode GPU (NVIDIA RTX 6000 Ada or A100) |
| **Model** | CatVTON (diffusion-based virtual try-on) |
| **Role** | High-fidelity image generation |

**Innovation: Dynamic Batching**

1. Reads `config:batch_size` from Redis (policy set by Arbitrator).
2. Waits up to 500ms to collect up to `batch_size` jobs.
3. Stacks images into a single tensor and runs one inference pass.
4. Generates the results, uploads them to s3 and extracts s3 key for each one.
5. Publishes to the `events:job_done` channel (job type `"try_on"`, result S3 key, status, `user_id`, `vton_id`). The Gateway subscribes and pushes to the client over WebSocket, updating the corresponding VTON entry with the S3 key for the generated try-on image.

**Result:** Up to ~8× throughput increase during spikes (batch=8 vs batch=1).

---

### D. The Arbitrator (The Brain)

| Property | Value |
|----------|-------|
| **Stack** | Node.js (lightweight control loop) |
| **Role** | Meta-scheduler: adjusts policy based on demand |
| **Interval** | 500ms |

**Logic:**

| Scenario | Condition | Action | Optimization |
|----------|-----------|--------|--------------|
| **A. Low Traffic** | `queue_depth ≤ 10` | `BATCH_SIZE = 1` | Latency |
| **B. High Traffic** | `10 < queue_depth ≤ 50` | `BATCH_SIZE = 4` | Throughput |
| **C. Surge** | `queue_depth > 50` | `BATCH_SIZE = 8` | Max throughput |
| **D. Emergency** | `average_wait_time > 10s` | `config:degraded_mode = 1` | Lower resolution (512px) |

**Metrics:** Reads `queue_depth` via `LLEN queue:weaver_jobs`. For Scenario D (emergency degraded mode), the Arbitrator needs `average_wait_time`: the Gateway stores `created_at` when enqueuing (in the job payload); the Weaver (or a post-process step) can record completion time. The Arbitrator computes average wait from these (e.g. from a Redis structure keyed by job id or from completed job metadata).

---

## 4. Advanced Kubernetes Integration (KEDA)

This section addresses the hackathon's **"Advanced Kubernetes"** requirement. We use **Event-Driven Autoscaling**, not just standard HPA.

### 4.1 The Problem

Standard Kubernetes scaling uses **CPU utilization**.

- GPU inference often keeps CPU/GPU near 100% whether processing 1 or 8 users.
- Standard HPA does not scale up effectively when the queue is backing up.

### 4.2 The Solution: KEDA ScaledObject

We scale based on **queue depth (demand)**, not CPU (effort).

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: weaver-scaler
  namespace: proteus
spec:
  scaleTargetRef:
    name: weaver
  minReplicaCount: 1
  maxReplicaCount: 5
  triggers:
    - type: redis
      metadata:
        addressFromEnv: REDIS_HOST
        listName: queue:weaver_jobs
        listLength: "10"
```

- **Target:** ~1 GPU pod per 10 pending jobs.
- **`listName`:** Must match the Redis key used by Gateway/Weaver (`queue:weaver_jobs`).
- **`addressFromEnv`:** Use a Secret or ConfigMap for Redis connection; avoid hardcoding.

> **Note:** KEDA Redis scaler metadata may vary by version. See [KEDA Redis Scaler](https://keda.sh/docs/2.12/scalers/redis/) for your cluster's KEDA version.

### 4.3 Double-Loop Scaling Strategy

| Loop | Component | Reaction Time | Mechanism |
|------|-----------|---------------|-----------|
| **Internal** | Arbitrator | Milliseconds | Increases `BATCH_SIZE` to absorb spikes |
| **External** | KEDA | Seconds | Deploys new GPU pods if batching is insufficient |

### 4.4 Optional: Tailor Autoscaling

If outfit-upload traffic grows, `queue:tailor_jobs` can be scaled with a second KEDA ScaledObject (same pattern as the Weaver, using `listName: queue:tailor_jobs`). By default, Tailor can run as a single replica if throughput is sufficient.

---

## 5. Frontend: Puppet AR Visualization

We cannot run diffusion at 60fps in the browser. Instead we use a **proxy visualization** technique.

### 5.1 Tech Stack

- **Framework:** React + Three.js (React Three Fiber)
- **Tracking:** Google MediaPipe Pose (client-side)

### 5.2 Mesh Warp Algorithm

| Step | Description |
|------|-------------|
| **Texture** | Receives the SegFormer-cleaned transparent PNG from the backend |
| **Geometry** | `PlaneGeometry(10, 10)` — 100 vertices |
| **Rigging** | Four corners mapped to MediaPipe pose landmarks |

**Vertex → Landmark Mapping:**

| Vertex | Position | MediaPipe Landmark |
|--------|----------|--------------------|
| Top-Left | (0, 0) | Landmark[11] — Left Shoulder |
| Top-Right | (10, 0) | Landmark[12] — Right Shoulder |
| Bottom-Left | (0, 10) | Landmark[23] — Left Hip |
| Bottom-Right | (10, 10) | Landmark[24] — Right Hip |

**Interpolation:** Inner vertices use bilinear interpolation between the four anchor points.

**Result:** As the user moves, the cloth texture deforms in 3D, creating a convincing "Magic Mirror" effect.

---

## 6. Data Flow (User Journey)

```
1. UPLOAD     User uploads outfit.jpg → Gateway stores in S3, pushes to queue:tailor_jobs → returns job_id (queued)
2. CLEAN      Tailor pops job, runs SegFormer, uploads cloth_clean.png to S3, publishes to events:job_done
3. DELIVER    Gateway (subscribed to events:job_done) pushes result to client over WebSocket → VTON entry gets cloth_clean_url
4. PREVIEW    User sees cloth_clean.png warped onto body in real-time (Three.js). "Snap" is only enabled after CLEAN completes.
5. ACTION     User poses, clicks "Snap"
6. QUEUE      Gateway validates outfit is ready, then pushes { user_photo_url, cloth_clean_url, user_id, vton_id } to queue:weaver_jobs
7. ORCHESTRATE
   • Arbitrator sees queue_depth = 12 → sets BATCH_SIZE = 4
   • KEDA sees queue_depth > 10 → scales Weaver to 2 pods
8. GENERATE   Weaver pops jobs, runs CatVTON, saves to Linode Object Storage, publishes to events:job_done
9. DELIVER    Gateway pushes try-on result to client over WebSocket (routing by user_id)
```

---

## 7. Redis Schema

| Key | Type | Producer | Consumer | Purpose |
|-----|------|----------|----------|---------|
| `queue:tailor_jobs` | List | Gateway (LPUSH) | Tailor (BRPOP) | Outfit-cleaning job queue |
| `queue:weaver_jobs` | List | Gateway (LPUSH) | Weaver (BRPOP) | Try-on job queue |
| `config:batch_size` | String | Arbitrator (SET) | Weaver (GET) | Dynamic batch policy |
| `config:degraded_mode` | String | Arbitrator | Weaver | 0=normal, 1=512px |
| `config:mode` | String | Arbitrator | Admin / future | VIP / ECONOMY / SURGE (e.g. billing or priority) |
| `events:job_done` | Pub/Sub | Tailor, Weaver (PUBLISH) | Gateway (SUBSCRIBE) | Real-time completion; Gateway routes by `user_id` |

**Job Payload (in `queue:tailor_jobs`):**

```json
{
  "id": "job_<uuid>",
  "s3_key": "uploads/outfit_abc123.jpg",
  "user_id": "user_<uuid>",
  "vton_id": "vton_<uuid>",
  "created_at": 1706956800
}
```

**Job Payload (in `queue:weaver_jobs`):**

```json
{
  "id": "job_<uuid>",
  "user_photo_url": "https://...",
  "cloth_clean_url": "https://...",
  "user_id": "user_<uuid>",
  "vton_id": "vton_<uuid>",
  "created_at": 1706956800
}
```

**`events:job_done` payload (required for WebSocket routing with multiple Gateway replicas):**

```json
{
  "job_id": "job_<uuid>",
  "job_type": "outfit_clean",
  "result_url": "https://...",
  "result_s3_key": "cleaned/outfit_xyz.png",
  "status": "completed",
  "user_id": "user_<uuid>",
  "vton_id": "vton_<uuid>"
}
```

- `job_type` is either `"outfit_clean"` (Tailor) or `"try_on"` (Weaver). The Gateway uses `user_id` (and optionally `connection_id` if stored) to push the event to the correct WebSocket. When using Redis Pub/Sub with multiple Gateway replicas, every pod receives every message; only the pod that holds the WebSocket for that `user_id` forwards the event.

---

## 8. API Reference

### Gateway

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload/cloth` | Enqueue outfit-cleaning job → returns `job_id`, `status: "queued"`. Client receives `cloth_clean_url` asynchronously via WebSocket (or GET /api/status/:job_id). |
| POST | `/api/snap` | Submit try-on job → returns `job_id`. **Requires** a completed outfit for the given `cloth_clean_url` (i.e. the corresponding outfit-cleaning job must have finished). Gateway returns 4xx if the outfit is not ready. |
| GET | `/api/status/:job_id` | Job status (supports both outfit-cleaning and try-on jobs). |
| WS | `/updates` | Real-time job completion; payloads include `job_type`, `result_url`, `user_id`, `vton_id`. |

### Tailor

| Method | Path | Description |
|--------|------|-------------|
| POST | `/segment` | Input: image. Output: transparent PNG (cloth only). Used internally; client flow is via Gateway (upload → queue:tailor_jobs → Tailor → events:job_done → WebSocket). |

### POST /api/snap — Request

```json
{
  "user_photo_url": "https://...",
  "cloth_clean_url": "https://..."
}
```

### POST /api/snap — Response

```json
{
  "job_id": "job_550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

## 9. Akamai / Linode Resource Mapping

| Component | Linode Service | Why |
|-----------|----------------|-----|
| **Cluster** | Linode Kubernetes Engine (LKE) | Managed K8s; KEDA and NVIDIA device plugins |
| **GPU Nodes** | Dedicated GPU Instances | Weaver (CatVTON); Tailor remains CPU |
| **Storage** | Linode Object Storage | S3-compatible; uploads and generated results |
| **Redis** | Managed Redis or self-hosted on LKE | Queues and pub/sub |
| **Load Balancer** | NodeBalancer | Distributes traffic; enable sticky sessions for WebSockets |

**WebSocket delivery:** Every completion is published to `events:job_done` with `user_id` (and `vton_id`). All Gateway replicas subscribe. Each replica maintains a mapping of `user_id` (or connection/session id) to WebSocket; when a message arrives, only the replica that holds that client's WebSocket forwards the event (others ignore). Alternatively, use session affinity (sticky sessions) so the same pod that enqueued the job also holds the WebSocket—still require `user_id` in the payload so that pod can match the message to the correct connection.

---

## 10. Why This Wins

| Criterion | How Proteus Addresses It |
|-----------|---------------------------|
| **Not a wrapper** | Deploys open-source models (SegFormer, CatVTON) on infrastructure, not just API calls |
| **Economic reality** | Arbitrator + KEDA: cost-aware scaling and batching |
| **User experience** | Dual pipeline: Three.js for real-time preview, diffusion for final quality |
| **Open source** | PyTorch, Three.js, Redis, Kubernetes, KEDA |

---

## 11. Infrastructure & Deployment

### 11.1 Suggested File Layout

```
Proteus/
├── gateway/
│   ├── index.js
│   ├── package.json
│   └── Dockerfile
├── tailor/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── weaver/
│   ├── worker.py
│   ├── requirements.txt
│   └── Dockerfile
├── arbitrator/
│   ├── arbitrator.js
│   ├── package.json
│   └── Dockerfile
├── frontend/
│   └── ...
├── k8s/
│   ├── namespace.yaml
│   ├── redis.yaml
│   ├── gateway.yaml
│   ├── tailor.yaml
│   ├── weaver.yaml
│   ├── arbitrator.yaml
│   ├── keda-scaler.yaml
│   └── ingress.yaml
└── docker-compose.yml
```

### 11.2 Environment Variables

| Service | Variable | Description |
|---------|----------|-------------|
| Gateway | `REDIS_URL` | Redis connection string |
| Gateway | `TAILOR_URL` | Tailor service URL |
| Gateway | `OBJECT_STORAGE_*` | Linode Object Storage credentials |
| Tailor | `REDIS_URL` | Redis connection (consumes `queue:tailor_jobs`, publishes to `events:job_done`) |
| Weaver | `REDIS_URL` | Redis connection |
| Weaver | `OBJECT_STORAGE_*` | Upload results |
| Arbitrator | `REDIS_URL` | Redis connection |

### 11.3 Docker Compose (Local Dev)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  gateway:
    build: ./gateway
    ports: ["3000:3000"]
    environment:
      REDIS_URL: redis://redis:6379
      TAILOR_URL: http://tailor:8000
    depends_on: [redis]

  tailor:
    build: ./tailor
    ports: ["8000:8000"]

  weaver:
    build: ./weaver
    runtime: nvidia
    environment:
      REDIS_URL: redis://redis:6379
    depends_on: [redis]

  arbitrator:
    build: ./arbitrator
    environment:
      REDIS_URL: redis://redis:6379
    depends_on: [redis]
```

### 11.4 Kubernetes Deployment (Overview)

- **Namespace:** `proteus`
- **Redis:** StatefulSet or external managed Redis
- **Gateway:** Deployment + Service + Ingress; replicas ≥ 2
- **Tailor:** Deployment + Service (CPU); optional KEDA ScaledObject on `queue:tailor_jobs` if scaling is needed
- **Weaver:** Deployment with GPU node selector; KEDA ScaledObject
- **Arbitrator:** Deployment (1 replica)

---
