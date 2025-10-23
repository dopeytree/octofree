# GitHub Actions & Security Workflows

This directory contains automated workflows for code quality, security scanning, and dependency management.

**Note**: All workflows use `github/codeql-action@v4` for security scanning and SARIF uploads.

## 🔒 Security Workflows

### 1. CodeQL Security Scan (`codeql.yml`)
- **Purpose**: Static code analysis for security vulnerabilities
- **When it runs**: 
  - Push to `master`/`main` branches
  - Pull requests
  - Weekly on Mondays at 6:00 AM UTC
- **What it does**: Scans Python code for security vulnerabilities and uploads results to GitHub Security tab

### 2. Docker Security Scan (`docker-security-scan.yml`)
- **Purpose**: Scan Docker images for vulnerabilities
- **When it runs**: 
  - Push/PR when Dockerfile or requirements.txt changes
  - Weekly on Mondays at 9:00 AM UTC
- **Tools used**:
  - **Trivy**: Comprehensive vulnerability scanner
  - **Docker Scout**: Docker's native security scanner
- **What it does**: 
  - Builds the Docker image
  - Scans for CRITICAL and HIGH severity CVEs
  - Uploads results to GitHub Security tab
  - Comments on PRs with findings

### 3. Python Security Scan (`python-security-scan.yml`)
- **Purpose**: Scan Python dependencies and code for security issues
- **When it runs**: 
  - Push to `master`/`main` branches
  - Pull requests
  - Weekly on Mondays at 10:00 AM UTC
- **Tools used**:
  - **Safety**: Checks dependencies against vulnerability database
  - **Bandit**: Python security linter
  - **pip-audit**: Audits Python packages for known vulnerabilities
- **What it does**: Identifies vulnerable dependencies and insecure code patterns

### 4. Dependency Review (`dependency-review.yml`)
- **Purpose**: Review dependency changes in pull requests
- **When it runs**: On all pull requests
- **What it does**:
  - Identifies new dependencies and their licenses
  - Fails if vulnerabilities with moderate+ severity are found
  - Blocks GPL-3.0 and AGPL-3.0 licenses
  - Comments results on PRs

## 🏗️ Build & Deploy

### Build and Scan (`build-and-scan.yml`)
- **Purpose**: Build Docker images and scan for vulnerabilities before publishing
- **When it runs**: 
  - Push to `master`/`main` branches
  - Pull requests
- **What it does**:
  - Builds Docker image with proper tags (branch, PR, SHA, latest)
  - Runs Trivy vulnerability scan on the built image
  - Pushes to GitHub Container Registry (ghcr.io) only from master branch (not from PRs)
  - Uploads scan results to GitHub Security tab
- **Registry**: `ghcr.io/dopeytree/octofree`

## 🤖 Code Review

### CodeRabbit AI Review (`coderabbit.yml`)
- **Purpose**: Automated AI-powered code review
- **When it runs**: On pull requests
- **What it does**:
  - Reviews code changes for bugs, security issues, and best practices
  - Provides inline comments and suggestions
  - Responds to review comments

**Setup Required**: Add `OPENAI_API_KEY` to your repository secrets
- Go to Settings → Secrets and variables → Actions
- Add new repository secret: `OPENAI_API_KEY`
- Get API key from: https://platform.openai.com/api-keys

## 📦 Dependency Management

### Dependabot (`../dependabot.yml`)
- **Purpose**: Automatic dependency updates
- **When it runs**: 
  - Docker: Daily
  - Python: Daily
  - GitHub Actions: Weekly on Mondays
- **What it does**:
  - Creates PRs to update dependencies
  - Labels PRs appropriately
  - Assigns reviewers automatically

### Auto-approve Dependabot PRs (`auto-merge.yml`) ⚠️
- **Purpose**: Automatically approve Dependabot PRs after security validation
- **Status**: ⚠️ **Currently disabled for manual review safety**
- **When it runs**: On pull requests from Dependabot
- **What it does**:
  - Builds Docker image and tests
  - Runs Trivy security scan
  - Auto-approves PR if no CRITICAL/HIGH vulnerabilities found
  - **Note**: Does NOT auto-merge (requires manual merge for safety)
- **Security**: Will NOT approve if critical or high severity vulnerabilities are detected

**Recommendation**: Keep this workflow disabled or remove it entirely if you prefer manual review of all dependency updates.

## 🔐 Required Permissions

These workflows require the following GitHub repository settings:

1. **Settings → Code security and analysis**:
   - ✅ Enable Dependency graph
   - ✅ Enable Dependabot alerts
   - ✅ Enable Dependabot security updates
   - ✅ Enable Code scanning (CodeQL)

2. **Settings → Actions → General**:
   - Workflow permissions: "Read and write permissions"
   - ✅ Allow GitHub Actions to create and approve pull requests

## 📊 Viewing Results

- **Security alerts**: Repository → Security tab → Vulnerability alerts
- **Code scanning**: Repository → Security tab → Code scanning
- **Workflow runs**: Repository → Actions tab
- **Dependabot PRs**: Repository → Pull requests (filter by label: `dependencies`)

## 🚀 Getting Started

1. Push these workflows to your repository
2. Add `OPENAI_API_KEY` secret (for CodeRabbit)
3. Enable required GitHub settings (see above)
4. Create a pull request to see the workflows in action!

## 🛠️ Customization

### Adjusting Security Thresholds

**Docker Security Scan**: Edit severity levels in `docker-security-scan.yml`:
```yaml
severity: 'CRITICAL,HIGH'  # Add MEDIUM for stricter scanning
```

**Dependency Review**: Change failure threshold in `dependency-review.yml`:
```yaml
fail-on-severity: moderate  # Options: critical, high, moderate, low
```

### Changing Schedule

Edit the `cron` expressions in each workflow. Examples:
- Daily at midnight: `'0 0 * * *'`
- Every Monday at 9 AM: `'0 9 * * 1'`
- Twice weekly: `'0 9 * * 1,4'`

## 📝 Notes

- CodeQL results appear in the Security tab after first run
- First-time workflows may take longer to complete
- Trivy and Scout findings will appear in different Security tab sections
- Dependabot PRs will be created automatically based on schedule
