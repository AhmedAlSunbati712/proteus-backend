# Proteus — Technical Specification & Architecture

> **Project Name:** Proteus  
> **Subtitle:** An Event-Driven, Intelligent Orchestration Engine for Real-Time GenAI Virtual Try-On  
> **Target Platform:** Akamai Linode Kubernetes Engine (LKE)

This document serves as the blueprint for development and the pitch deck for hackathon judges. It addresses: **Advanced Kubernetes (KEDA)**, **GPU Acceleration**, **Scalability**, and **Open Source Innovation**.

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
- **The "Sanity Check":** Handles generating presigned upload and download urls for s3 bucket. It also receives job requests from the client and pushes them to the correct queue.
- **WebSocket Delivery:** Subscribes to Redis Pub/Sub; pushes completed job results to the correct client. The websocket runs on an http route
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
- It listens over the `tailorJob` queue for any incoming jobs
- It takes the s3 key of the image to be cleaned, gets the presigned download url, downloads the image and processes it, uploads the result to s3 and publishes over the finishedJobs channel the finished result (job type, the s3 key for the resulting image, whether the job failed or not, which user it corresponds to, the VTON id it corresponds to). The websocket will update the corresponding VTON entry with the s3 key for the transparent png of the outfit only.

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
5. Publishes results (job type, the s3 key for the resulting image, whether the job failed or not, which user it corresponds to, the VTON id it corresponds to) to Redis. Webscoket will the update the corresponding VTON entry with the s3 key for the transformted png of the outfit

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

**Metrics:** Reads `queue_depth` via `LLEN queue:jobs`. Optional: `average_wait_time` computed from job timestamps stored in Redis by the Gateway on enqueue and by the Weaver on completion.

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
        listName: queue:jobs
        listLength: "10"
```

- **Target:** ~1 GPU pod per 10 pending jobs.
- **`listName`:** Must match the Redis key used by Gateway/Weaver (`queue:jobs`).
- **`addressFromEnv`:** Use a Secret or ConfigMap for Redis connection; avoid hardcoding.

> **Note:** KEDA Redis scaler metadata may vary by version. See [KEDA Redis Scaler](https://keda.sh/docs/2.12/scalers/redis/) for your cluster's KEDA version.

### 4.3 Double-Loop Scaling Strategy

| Loop | Component | Reaction Time | Mechanism |
|------|-----------|---------------|-----------|
| **Internal** | Arbitrator | Milliseconds | Increases `BATCH_SIZE` to absorb spikes |
| **External** | KEDA | Seconds | Deploys new GPU pods if batching is insufficient |

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
1. UPLOAD     User uploads outfit.jpg (e.g., product photo)
2. CLEAN      Gateway → Tailor. SegFormer extracts cloth → cloth_clean.png
3. PREVIEW    User sees cloth_clean.png warped onto body in real-time (Three.js)
4. ACTION     User poses, clicks "Snap"
5. QUEUE      Gateway pushes { user_photo_url, cloth_clean_url } to Redis queue:jobs
6. ORCHESTRATE
   • Arbitrator sees queue_depth = 12 → sets BATCH_SIZE = 4
   • KEDA sees queue_depth > 10 → scales Weaver to 2 pods
7. GENERATE   Weaver pops 4 jobs, runs CatVTON, saves to Linode Object Storage
8. DELIVER    Weaver publishes "job_done" to Redis → Gateway → WebSocket → User
```

---

## 7. Redis Schema

| Key | Type | Producer | Consumer | Purpose |
|-----|------|----------|----------|---------|
| `queue:jobs` | List | Gateway (LPUSH) | Weaver (BRPOP) | Job queue |
| `config:batch_size` | String | Arbitrator (SET) | Weaver (GET) | Dynamic batch policy |
| `config:degraded_mode` | String | Arbitrator | Weaver | 0=normal, 1=512px |
| `config:mode` | String | Arbitrator | Admin | VIP / ECONOMY / SURGE |
| `events:job_done` | Pub/Sub | Weaver (PUBLISH) | Gateway (SUBSCRIBE) | Real-time completion |

**Job Payload (in `queue:jobs`):**

```json
{
  "id": "job_<uuid>",
  "user_photo_url": "https://...",
  "cloth_clean_url": "https://...",
  "created_at": 1706956800
}
```

**`events:job_done` payload:**

```json
{
  "job_id": "job_<uuid>",
  "result_url": "https://...",
  "status": "completed"
}
```

---

## 8. API Reference

### Gateway

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/upload/cloth` | Upload cloth image → returns `cloth_clean_url` |
| POST | `/api/snap` | Submit try-on job → returns `job_id` |
| GET | `/api/status/:job_id` | Job status |
| WS | `/updates` | Real-time job completion |

### Tailor

| Method | Path | Description |
|--------|------|-------------|
| POST | `/segment` | Input: image. Output: transparent PNG (cloth only) |

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

**WebSocket Note:** Use session affinity (sticky sessions) so a client's WebSocket stays on the same Gateway pod that enqueued its job, or ensure Gateway uses Redis Pub/Sub so any replica can deliver results.

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
| Tailor | `REDIS_URL` | Optional, if Tailor uses Redis |
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
- **Tailor:** Deployment + Service (CPU)
- **Weaver:** Deployment with GPU node selector; KEDA ScaledObject
- **Arbitrator:** Deployment (1 replica)

---
