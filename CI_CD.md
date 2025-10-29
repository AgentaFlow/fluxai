# FluxAI - CI/CD Documentation

This document describes the continuous integration and continuous deployment (CI/CD) pipelines for FluxAI.

## 📋 Table of Contents

- [Overview](#overview)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Security Scanning](#security-scanning)
- [Docker Image Publishing](#docker-image-publishing)
- [Badge Status](#badge-status)
- [Secrets Configuration](#secrets-configuration)
- [Local Testing](#local-testing)

---

## 🎯 Overview

FluxAI uses GitHub Actions for automated CI/CD pipelines with two main workflows:

1. **Security Scan** - Vulnerability scanning with Trivy, Safety, and Bandit
2. **Docker Publish** - Build and publish Docker images to GitHub Container Registry

### Workflow Triggers

| Workflow | Triggers |
|----------|----------|
| Security Scan | Push to main/develop, PRs, Daily at 2 AM UTC, Manual |
| Docker Publish | Push to main, Tags (v*.*.*), PRs, Manual |

---

## 🔒 Security Scanning

### Workflow: `.github/workflows/security-scan.yml`

**Purpose:** Comprehensive security scanning of code, dependencies, and configurations.

### Jobs

#### 1. Trivy Filesystem Scan
- **Scanner:** [Trivy](https://github.com/aquasecurity/trivy)
- **Scan Type:** Filesystem (`fs`)
- **Target:** Entire repository
- **Severity:** CRITICAL, HIGH, MEDIUM
- **Output:** SARIF format uploaded to GitHub Security tab

**What it checks:**
- Python dependencies in `requirements.txt`
- Configuration files (YAML, JSON, etc.)
- Infrastructure as Code (Docker, docker-compose)
- Known vulnerabilities in third-party packages

#### 2. Trivy Configuration Scan
- **Scanner:** Trivy
- **Scan Type:** Configuration (`config`)
- **Target:** All config files
- **Output:** Table format in workflow logs

**What it checks:**
- Dockerfile best practices
- docker-compose.yml security issues
- Misconfigurations in YAML/JSON files
- Secrets exposure risks

#### 3. Python Security Check
- **Tools:** Safety + Bandit
- **Target:** Python code and dependencies

**Safety:**
- Checks `requirements.txt` for known vulnerabilities
- Uses Python Package Index vulnerability database
- Reports CVEs and security advisories

**Bandit:**
- Static code analysis for Python security issues
- Detects common security flaws:
  - Hardcoded credentials
  - SQL injection vulnerabilities
  - Use of insecure functions
  - Weak cryptography
- Generates JSON report artifact

### Security Results

View security findings in:
- **GitHub Security Tab:** `https://github.com/AgentaFlow/fluxai/security`
- **Workflow Artifacts:** Bandit JSON reports
- **Workflow Logs:** Table format scan results

### Security Scan Schedule

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

This ensures regular vulnerability scanning even when code isn't being changed.

---

## 🐳 Docker Image Publishing

### Workflow: `.github/workflows/docker-publish.yml`

**Purpose:** Build multi-architecture Docker images and publish to GitHub Container Registry.

### Jobs

#### 1. Build and Push API Image

**Image:** `ghcr.io/agentaflow/fluxai:latest`

**Process:**
1. Checkout code
2. Set up Docker Buildx (multi-arch support)
3. Login to GitHub Container Registry
4. Extract metadata (tags, labels)
5. Build and push image
6. Scan image with Trivy
7. Upload scan results to Security tab

**Platforms Built:**
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

**Tags Generated:**
- `main` - Latest from main branch
- `v1.2.3` - Semantic version tags
- `v1.2` - Minor version
- `v1` - Major version
- `latest` - Latest release
- `main-abc1234` - Branch with commit SHA

#### 2. Build and Push Dashboard Image

**Image:** `ghcr.io/agentaflow/fluxai-dashboard:latest`

**Process:** Same as API image but uses `Dockerfile.dashboard`

#### 3. Build Summary

**Purpose:** Aggregate build results and report status

**Outputs:**
- ✅ Success if both images built
- ❌ Failure if any image failed

### Docker Image Tags

Images are tagged automatically based on:

| Event | Tag Example | Description |
|-------|-------------|-------------|
| Push to main | `main`, `latest` | Latest development build |
| Tag v1.2.3 | `1.2.3`, `1.2`, `1` | Semantic versioning |
| Pull Request | `pr-123` | PR number |
| Commit | `main-abc1234` | Branch + SHA |

### Image Scanning

After building, images are scanned with Trivy for:
- OS package vulnerabilities
- Language-specific dependencies (Python, etc.)
- CRITICAL and HIGH severity issues

Results are uploaded to GitHub Security tab with category tags:
- `docker-api` - API image scan results
- `docker-dashboard` - Dashboard image scan results

### Build Caching

Uses GitHub Actions cache for faster builds:

```yaml
cache-from: type=gha
cache-to: type=gha,mode=max
```

**Benefits:**
- Faster builds (layer caching)
- Reduced build times for unchanged layers
- Lower bandwidth usage

---

## 📊 Badge Status

### Current Badges

The README displays the following status badges:

```markdown
[![Build and Publish](https://github.com/AgentaFlow/fluxai/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/AgentaFlow/fluxai/actions/workflows/docker-publish.yml)
[![Security Scan](https://github.com/AgentaFlow/fluxai/actions/workflows/security-scan.yml/badge.svg)](https://github.com/AgentaFlow/fluxai/actions/workflows/security-scan.yml)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Available-2496ED?logo=docker&logoColor=white)](https://github.com/AgentaFlow/fluxai/pkgs/container/fluxai)
```

### Badge Meanings

| Badge | Status | Link |
|-------|--------|------|
| Build and Publish | Shows if Docker builds are passing | Workflow runs |
| Security Scan | Shows if security scans are passing | Security findings |
| Python | Python version requirement | Python downloads |
| FastAPI | Framework used | FastAPI docs |
| Docker | Docker images available | GitHub Packages |

---

## 🔐 Secrets Configuration

### Required Secrets

No additional secrets needed! The workflows use:

**GITHUB_TOKEN** (automatically provided)
- Permissions: `contents: read`, `packages: write`, `security-events: write`
- Used for: GHCR login, uploading SARIF results

### Optional Secrets

For production deployments, you may want:

**AWS_ACCESS_KEY_ID** - AWS credentials for Bedrock access
**AWS_SECRET_ACCESS_KEY** - AWS secret key
**SLACK_WEBHOOK** - Notifications on build failures
**DOCKER_HUB_TOKEN** - If publishing to Docker Hub

Add secrets at: `https://github.com/AgentaFlow/fluxai/settings/secrets/actions`

---

## 🧪 Local Testing

### Test Security Scan Locally

#### Trivy Filesystem Scan
```bash
# Install Trivy
brew install trivy  # macOS
# or
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Run filesystem scan
trivy fs . --severity CRITICAL,HIGH,MEDIUM --ignore-unfixed

# Generate SARIF report
trivy fs . --format sarif --output trivy-results.sarif
```

#### Trivy Config Scan
```bash
trivy config . --severity CRITICAL,HIGH,MEDIUM
```

#### Safety (Python Dependencies)
```bash
pip install safety
safety check --json
```

#### Bandit (Python Code)
```bash
pip install bandit
bandit -r app/ -f screen
bandit -r app/ -f json -o bandit-report.json
```

### Test Docker Build Locally

#### Build API Image
```bash
# Build for current platform
docker build -t fluxai-api:local -f Dockerfile .

# Build multi-arch (requires buildx)
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t fluxai-api:local -f Dockerfile .

# Scan built image
trivy image fluxai-api:local --severity CRITICAL,HIGH
```

#### Build Dashboard Image
```bash
docker build -t fluxai-dashboard:local -f Dockerfile.dashboard .
trivy image fluxai-dashboard:local --severity CRITICAL,HIGH
```

### Test Complete Stack
```bash
# Build all images locally
docker-compose build

# Run security scan on all images
docker images --format "{{.Repository}}:{{.Tag}}" | grep fluxai | xargs -I {} trivy image {}

# Start stack
docker-compose up -d

# Verify health
docker-compose ps
```

---

## 🚀 Workflow Usage

### Manual Trigger

Both workflows can be triggered manually:

1. Go to **Actions** tab
2. Select workflow (Security Scan or Docker Publish)
3. Click **Run workflow**
4. Select branch
5. Click **Run workflow** button

### On Pull Request

Both workflows run automatically on PRs to:
- Verify security
- Test Docker builds
- Prevent merging vulnerable code

**Note:** Images are built but not pushed on PRs.

### On Release

To publish a new version:

1. **Tag a release:**
   ```bash
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

2. **Workflow automatically:**
   - Builds images
   - Tags with `1.2.3`, `1.2`, `1`, `latest`
   - Pushes to GitHub Container Registry
   - Scans for vulnerabilities

3. **Pull published images:**
   ```bash
   docker pull ghcr.io/agentaflow/fluxai:1.2.3
   docker pull ghcr.io/agentaflow/fluxai-dashboard:1.2.3
   ```

---

## 📦 Using Published Images

### Pull from GitHub Container Registry

```bash
# Login (if repository is private)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull API image
docker pull ghcr.io/agentaflow/fluxai:latest

# Pull Dashboard image
docker pull ghcr.io/agentaflow/fluxai-dashboard:latest

# Pull specific version
docker pull ghcr.io/agentaflow/fluxai:1.2.3
```

### Use in docker-compose

```yaml
services:
  api:
    image: ghcr.io/agentaflow/fluxai:latest
    # ... rest of config

  dashboard:
    image: ghcr.io/agentaflow/fluxai-dashboard:latest
    # ... rest of config
```

### Use in Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fluxai-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: ghcr.io/agentaflow/fluxai:1.2.3
        imagePullPolicy: IfNotPresent
```

---

## 🔄 Continuous Improvement

### Monitoring Workflow Health

Check workflow status:
- **Actions tab:** All workflow runs
- **README badges:** Quick status overview
- **Security tab:** Vulnerability findings

### Best Practices

1. **Keep dependencies updated:** Regularly update `requirements.txt`
2. **Review security findings:** Check Security tab weekly
3. **Test before merging:** Ensure workflows pass on PRs
4. **Use semantic versioning:** Tag releases properly (v1.2.3)
5. **Monitor image sizes:** Keep Docker images lean

### Troubleshooting

**Workflow fails with permission error:**
- Check repository settings → Actions → General → Workflow permissions
- Enable "Read and write permissions"

**Security scan finds vulnerabilities:**
- Review findings in Security tab
- Update vulnerable dependencies
- Add exceptions for false positives (create `.trivyignore`)

**Docker build fails:**
- Check Dockerfile syntax
- Verify all COPY paths exist
- Test build locally first

**Image push fails:**
- Verify GITHUB_TOKEN has packages:write permission
- Check if repository allows package publishing

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [SARIF Format](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning)

---

**Need Help?**

- Check workflow logs in Actions tab
- Review Security tab for vulnerability details
- Test workflows locally before pushing
- Consult [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for Docker-specific issues
