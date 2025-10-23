# GitHub Actions & Security Workflows

This directory contains automated workflows for code quality, security scanning, and dependency management.

## 🔒 Security Workflows

> **Note**: All workflows use `github/codeql-action@v4` for security scanning and SARIF uploads.

### 1. CodeQL Security Scan (`codeql.yml`)
- **Purpose**: Static code analysis for security vulnerabilities
- **When it runs**: 
  - Push to `master`/`main` branches
  - Pull requests
  - Weekly on Mondays at 6:00 AM UTC
- **What it does**: Scans Python code for security vulnerabilities and uploads results to GitHub Security tab
- **Actions**: Uses CodeQL v4 for init, autobuild, and analyze steps

### 2. Build and Scan (`build-and-scan.yml`)
- **Purpose**: Build Docker image, push to registry, and scan for vulnerabilities
- **When it runs**: 
  - Push to `master`/`main` branches
  - Pull requests
- **What it does**:
  - Builds Docker image for the octofree application
  - Pushes to GitHub Container Registry (only from master branch, not PRs)
  - Tags images with branch name, PR number, SHA, and 'latest'
  - Scans built image with Trivy for CRITICAL and HIGH vulnerabilities
  - Uploads SARIF results to GitHub Security tab using CodeQL v4
- **Registry**: `ghcr.io/dopeytree/octofree`

### 3. Docker Security Scan (`docker-security-scan.yml`)
- **Purpose**: Dedicated security scanning of Docker images
- **When it runs**: 
  - Push/PR when Dockerfile or requirements.txt changes
  - Weekly on Mondays at 9:00 AM UTC
- **Tools used**:
  - **Trivy**: Comprehensive vulnerability scanner
- **What it does**: 
  - Builds the Docker image (without pushing)
  - Scans for CRITICAL and HIGH severity CVEs
  - Uploads results to GitHub Security tab using CodeQL v4
  - Provides detailed table output for PRs (CRITICAL, HIGH, MEDIUM)

### 4. Python Security Scan (`python-security-scan.yml`)
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

### 5. Dependency Review (`dependency-review.yml`)
- **Purpose**: Review dependency changes in pull requests
- **When it runs**: On all pull requests
- **What it does**:
  - Identifies new dependencies and their licenses
  - Fails if vulnerabilities with moderate+ severity are found
  - Blocks GPL-3.0 and AGPL-3.0 licenses
  - Comments results on PRs

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

### Auto-approve Dependabot PRs (`auto-merge.yml`) ⚠️ DISABLED
- **Purpose**: Automatically approve Dependabot PRs after security checks
- **Status**: ⚠️ **Currently disabled/failing by design for safety**
- **When it runs**: On Dependabot pull requests (if enabled)
- **What it does**:
  - Builds Docker image to verify it works
  - Runs Trivy security scan
  - Checks for CRITICAL or HIGH vulnerabilities
  - Auto-approves PR if all checks pass (requires manual merge)
- **Note**: This workflow is configured to fail as a safety measure - all PRs require manual review and approval before merging

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
