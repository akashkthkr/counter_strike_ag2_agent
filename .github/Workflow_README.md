# GitHub Workflows - Counter-Strike AG2 Agent System

This directory contains GitHub Actions workflows for automated testing, building, and deployment of the Counter-Strike AG2 Agent System.

## 🚀 Workflows Overview

### 1. Test Suite (`test.yml`)
**Triggers:** Push to main/develop/ak_game_design branches, PRs to main/develop

**Features:**
- **Multi-Python Testing:** Tests on Python 3.10 and 3.11
- **Service Dependencies:** PostgreSQL, Redis, ChromaDB containers
- **Comprehensive Testing:** Core, RAG, agents, integration tests
- **Coverage Reporting:** Codecov integration with XML reports
- **Test Categories:** Streamlined test runner execution
- **Environment Isolation:** Temporary directories and unique collections

**Services Started:**
- PostgreSQL 15 (port 5432)
- Redis 7 (port 6379)  
- ChromaDB (port 8000)

**Test Execution:**
```bash
# Core functionality tests
pytest tests/test_core.py -v --cov=counter_strike_ag2_agent

# RAG system tests
pytest tests/test_rag.py -v --cov=counter_strike_ag2_agent

# Agent system tests (essential)
pytest tests/test_agents_essential.py -v --cov=counter_strike_ag2_agent

# Integration tests (essential)
pytest tests/test_integration_essential.py -v --cov=counter_strike_ag2_agent

# Docker integration tests
pytest tests/test_docker_integration.py -v --cov=counter_strike_ag2_agent
```

### 2. Docker Build & Test (`docker.yml`)
**Triggers:** Push to main/develop/ak_game_design branches, PRs to main/develop

**Features:**
- **Multi-Service Build:** API, Agents, Web UI containers
- **Health Checks:** Comprehensive service connectivity testing
- **Container Registry:** GitHub Container Registry (ghcr.io) publishing
- **Production Images:** Tagged with commit SHA and branch
- **Security Scanning:** Trivy vulnerability scanning
- **Docker Compose Testing:** Full stack integration testing

**Build Process:**
1. **Build Images:** All Docker services in parallel
2. **Start Infrastructure:** PostgreSQL, Redis, ChromaDB
3. **Test Connectivity:** Database and service health checks
4. **Start Application:** API and Agent services
5. **Run Tests:** In-container test execution
6. **Push Images:** To GitHub Container Registry (on push)

**Generated Images:**
- `ghcr.io/[repo]-api:[sha]` - FastAPI backend service
- `ghcr.io/[repo]-agents:[sha]` - AG2 agent processing service  
- `ghcr.io/[repo]-web-ui:[sha]` - Browser-based UI service

### 3. Preview Deployment (`preview.yml`)
**Triggers:** Push to main/develop/ak_game_design branches, PRs to main/develop

**Features:**
- **Static Preview UI:** Cloudflare Pages deployment
- **Live Demo:** Interactive web interface
- **Backend Integration:** Configurable backend URL connection
- **Real-time Updates:** WebSocket communication support
- **PR Previews:** Automatic preview URLs in PR comments
- **Production Deployment:** Main branch auto-deployment

**Preview Features:**
- **Agent Panels:** 3 Terrorist + 1 CT interactive interfaces
- **Demo Controls:** Pre-configured actions for testing
- **Connection Management:** Dynamic backend URL configuration
- **Game State Display:** Real-time status monitoring
- **WebSocket Support:** Live bidirectional communication

## 🔧 Setup Requirements

### GitHub Secrets
Configure these secrets in your repository settings:

```bash
# Cloudflare Pages (for preview deployment)
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id

# Optional: External API keys for testing
ANTHROPIC_API_KEY=your-anthropic-key  # For live API tests
OPENAI_API_KEY=your-openai-key        # For live API tests
```

### Repository Settings
1. **Actions Permissions:** Enable GitHub Actions
2. **Package Permissions:** Allow GitHub Container Registry access
3. **Pages Settings:** Configure Cloudflare Pages integration
4. **Branch Protection:** Configure main/develop branch rules

## 📊 Workflow Status Badges

Add these badges to your main README:

```markdown
![Tests](https://github.com/[username]/counter_strike_ag2_agent/workflows/Test%20Suite/badge.svg)
![Docker](https://github.com/[username]/counter_strike_ag2_agent/workflows/Docker%20Build%20&%20Test/badge.svg)
![Preview](https://github.com/[username]/counter_strike_ag2_agent/workflows/Deploy%20Preview%20UI/badge.svg)
```

## 🚀 Deployment Workflows

### Development Workflow
1. **Create Feature Branch:** `git checkout -b feature/your-feature`
2. **Push Changes:** Triggers test workflow
3. **Create PR:** Triggers all workflows + preview deployment
4. **Review:** Check workflow status and preview URL
5. **Merge:** Triggers production deployment

### Production Deployment
1. **Merge to Main:** Triggers production workflows
2. **Docker Images:** Built and pushed to registry
3. **Preview UI:** Deployed to production Cloudflare Pages
4. **Artifacts:** Production docker-compose.yml generated

## 🔍 Monitoring and Debugging

### Workflow Logs
- **Test Results:** JUnit XML reports in workflow artifacts
- **Coverage Reports:** Codecov integration with detailed reports
- **Docker Logs:** Service logs captured for debugging
- **Build Artifacts:** Production compose files available

### Common Issues

#### Test Failures
```bash
# Check service connectivity
docker compose exec postgres pg_isready -U cs_user -d counter_strike_db_test

# Verify ChromaDB
curl -f http://localhost:8000/api/v1/heartbeat

# Check test environment
pytest tests/test_core.py -v -s --tb=long
```

#### Docker Build Issues
```bash
# Local testing
docker compose build --parallel
docker compose up -d postgres redis chromadb
sleep 30
docker compose up -d api agent_service
```

#### Preview Deployment Issues
```bash
# Check Cloudflare Pages status
npx wrangler pages deployment list --project-name=counter-strike-ag2-preview

# Test preview build locally
cd preview-ui
npm run build
npx serve dist
```

## 🔄 Workflow Customization

### Adding New Tests
1. **Create Test File:** Add to `tests/` directory
2. **Update Workflow:** Add test execution step in `test.yml`
3. **Update Categories:** Modify `tests/run_tests.py` if needed

### Adding New Services
1. **Create Dockerfile:** Add to `docker/` directory
2. **Update Compose:** Add service to `docker-compose.yml`
3. **Update Workflow:** Add build step in `docker.yml`

### Modifying Preview UI
1. **Update Template:** Modify preview HTML generation in `preview.yml`
2. **Add Assets:** Update asset copying steps
3. **Test Locally:** Use `preview-ui/` directory for development

## 📈 Performance Optimization

### Workflow Speed
- **Parallel Execution:** Tests run across multiple Python versions
- **Docker Layer Caching:** Buildx cache optimization
- **Service Dependencies:** Proper health checks prevent race conditions
- **Artifact Management:** Selective artifact upload/download

### Resource Usage
- **Service Isolation:** Each workflow uses fresh containers
- **Cleanup:** Automatic resource cleanup after workflows
- **Caching:** pip and Docker layer caching for faster builds

This workflow setup provides a comprehensive CI/CD pipeline for the Counter-Strike AG2 system, ensuring code quality, automated testing, and seamless deployment of both backend services and preview interfaces.
