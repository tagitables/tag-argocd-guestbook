# ArgoCD Guestbook — ARM64 GitOps Deployment

## Project Overview

This repository demonstrates GitOps deployment of a lightweight Guestbook application to AWS EKS using ArgoCD.

### Technology Stack

- AWS EKS — Kubernetes cluster with ARM64 worker nodes
- ArgoCD — GitOps continuous reconciliation
- Docker Buildx — ARM64 container image building
- GitHub Container Registry — Container image distribution
- Python 3.12 — Lightweight HTTP Guestbook application
- Kubernetes Deployment and Service — Application orchestration

## Architecture

GitHub Repository
    |
    v
ArgoCD Application (tag-guestbook)
    |
    v
Kubernetes Deployment (tag-ns)
    |
    v
ARM64 EKS Worker Node
    |
    v
Guestbook Container (Port 80)

## Technical Incident: Container Architecture Incompatibility

### Initial Failure

The original Guestbook Pod failed with:

    exec /usr/local/bin/docker-php-entrypoint: exec format error

ArgoCD reported Synced / Progressing, while the Kubernetes Deployment had 0/1 ready replicas.

### Root Cause Analysis

Inspected EKS worker node architecture:

    kubectl get nodes -L kubernetes.io/arch

All three nodes were ARM64.

Inspected the original image:

    docker manifest inspect --verbose gcr.io/google-samples/gb-frontend:v5

The original image supported linux/amd64, which was incompatible with the ARM64 worker nodes.

### Technical Remediation

Implemented a lightweight Python Guestbook and created a Dockerfile using python:3.12-slim.

Built an ARM64-compatible image:

    docker buildx build --platform linux/arm64 \
      --tag tag-guestbook:arm64-test --load .

Verified image architecture:

    docker image inspect tag-guestbook:arm64-test \
      --format 'OS={{.Os}} Architecture={{.Architecture}}'

Result:

    OS=linux Architecture=arm64

## Local Application Validation

Started the container:

    docker run -d --name tag-guestbook-local \
      --platform linux/arm64 -p 8083:80 \
      tag-guestbook:arm64-test

Verified HTTP GET:

    curl -i http://127.0.0.1:8083/

Result: HTTP 200 OK.

Verified HTTP POST:

    curl -i -d 'message=Hello+from+GitOps' \
      http://127.0.0.1:8083/

Result: HTTP 303 See Other.

Verified message retrieval:

    curl -s http://127.0.0.1:8083/ | grep 'Hello from GitOps'

Result: Message displayed successfully.

## Container Registry Publication

Authenticated Docker with GHCR:

    gh auth token | docker login ghcr.io \
      --username tagitables --password-stdin

Tagged and pushed the image:

    docker tag tag-guestbook:arm64-test \
      ghcr.io/tagitables/tag-argocd-guestbook:v1

    docker push ghcr.io/tagitables/tag-argocd-guestbook:v1

Published image:

    ghcr.io/tagitables/tag-argocd-guestbook:v1

## GitOps Configuration and Reconciliation

Updated manifests/deployment.yaml to use the ARM64-compatible GHCR image.

Committed the remediation:

    fix(gitops): resolve ARM64 image incompatibility in ArgoCD Guestbook

Commit: ae0f194

ArgoCD initially continued tracking the older Git revision:

    868c8d28e633fb9176cf0b004840be64a1fd6eea

Requested an Application refresh:

    kubectl annotate application tag-guestbook \
      -n argocd argocd.argoproj.io/refresh=normal \
      --overwrite

ArgoCD subsequently tracked:

    ae0f19434b7ad8634015e975099467f3ff9257b5

The Kubernetes Deployment then referenced the updated GHCR image.

## Secondary Incident: GHCR Authentication

The replacement Pod initially entered ImagePullBackOff.

Inspected Kubernetes Events:

    kubectl describe pod tag-guestbook-68d8b99c67-qbjgd \
      -n tag-ns

Observed error:

    failed to fetch anonymous token: 401 Unauthorized

Root cause: GHCR was not authorising anonymous image pulls.

Remediation: Configured the package for public access.

Verified the anonymous token endpoint returned HTTP 200.

## Kubernetes Recovery

Checked Guestbook Pods:

    kubectl get pods -n tag-ns -l app=tag-guestbook -o wide

Verified result:

    tag-guestbook-68d8b99c67-qbjgd   1/1   Running   0

The replacement ARM64 container started successfully on the EKS worker node.

## Final Verification — Pending

Confirm ArgoCD health:

    kubectl get application tag-guestbook -n argocd

Confirm Deployment readiness:

    kubectl get deployment tag-guestbook -n tag-ns

Test the Kubernetes Service:

    kubectl port-forward -n tag-ns service/tag-guestbook 8084:80

In another terminal:

    curl -i http://127.0.0.1:8084/

## Technical Lessons Learned

1. Container images must support the CPU architecture of their Kubernetes worker nodes.
2. ArgoCD Synced does not necessarily mean an application is Healthy.
3. GitOps reconciliation should be verified against the actual Git commit SHA.
4. Successful container image publication does not guarantee anonymous pull access.
5. Kubernetes Pod Events provide critical diagnostic evidence.
6. Troubleshooting should distinguish application, runtime, registry, and reconciliation failures.
7. Changes should remain scoped to the affected workload in shared environments.

## Implementation Limitations

The replacement Guestbook uses in-memory message storage rather than the original PHP/Redis architecture.

Messages do not persist across container restarts.

Further improvements include non-root container execution, resource limits, health probes, persistent storage, and immutable image digest references.

## Outcome

The ARM64 image was built, tested, published, and successfully deployed to an EKS Pod.

Final ArgoCD Healthy status and end-to-end Service HTTP validation remain pending.
