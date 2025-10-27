# Future Enhancements

Optional improvements to implement later. These were part of the original plan but deferred.

## Not Yet Implemented

### 1. Branch Protection Rules (GitHub Settings)

**What it does:** Prevents direct pushes to main branch, requires PR reviews and CI checks to pass.

**Implementation Steps:**
1. Go to GitHub repo → Settings → Branches
2. Add branch protection rule for `main`:
   - ✅ Require pull request before merging
   - ✅ Require approvals: 1
   - ✅ Require status checks to pass:
     - `quality / Code Quality Checks`
     - `test / Tests`
     - `security / Security Scan`
   - ✅ Require conversation resolution
   - ✅ Do not allow bypassing settings

**Effort:** 5 minutes
**Priority:** High - Do before first PR
**Status:** Not implemented

---

### 2. Codecov Token (Coverage Reporting)

**What it does:** Uploads test coverage to Codecov.io for tracking over time, PR comments, and badges.

**Implementation Steps:**
1. Sign up at https://codecov.io (free for public repos)
2. Connect your GitHub repo to Codecov
3. Get upload token from Codecov dashboard
4. Add to GitHub Secrets:
   - Name: `CODECOV_TOKEN`
   - Value: `<your-token-from-codecov>`
5. Add badge to README:
   ```markdown
   ![Coverage](https://codecov.io/gh/yourusername/org-service/branch/main/graph/badge.svg)
   ```

**Benefits:**
- Coverage trends over time
- PR comments showing coverage changes
- Coverage badge for README
- Coverage visualizations

**Effort:** 10 minutes
**Priority:** Medium - Nice to have for visibility
**Status:** Not implemented
**Note:** CI workflow already configured to upload coverage, just needs token

---

### 3. Environment Configs (Production .env)

**What it does:** Separate configurations for dev/staging/prod environments.

**Implementation Steps:**
1. Create environment-specific files:
   - `.env.development` (for local dev)
   - `.env.staging` (for staging environment)
   - `.env.production` (for production - DO NOT COMMIT)

2. Update `org_service/config.py`:
   ```python
   import os

   class Settings(BaseSettings):
       environment: str = "development"
       log_level: str = "INFO"

       model_config = SettingsConfigDict(
           env_file=f".env.{os.getenv('ENV', 'development')}",
           extra="ignore"
       )
   ```

3. Use in deployment:
   ```bash
   # Development
   ENV=development uvicorn org_service.main:app --reload

   # Production
   ENV=production uvicorn org_service.main:app --host 0.0.0.0
   ```

4. Update Kubernetes deployment to use secrets:
   ```yaml
   env:
     - name: ENV
       value: "production"
     - name: GOOGLE_CLIENT_ID
       valueFrom:
         secretKeyRef:
           name: org-service-secrets
           key: google-client-id
   ```

**Best Practices:**
- Use AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault for production
- Different Google OAuth credentials per environment
- Rotate secrets regularly
- Add `.env.production` to `.gitignore`

**Effort:** 30 minutes
**Priority:** High - Do before first deployment
**Status:** Not implemented
**Note:** Basic structure ready, just needs environment-specific .env files

---

## Already Implemented ✅

These were in the original "optional next steps" but are now complete:

- ✅ **Prometheus Monitoring** - `/metrics` endpoint with comprehensive metrics
- ✅ **Enhanced Health Checks** - `/health`, `/live`, `/ready` endpoints for Kubernetes
- ✅ **Kubernetes Integration** - Full deployment manifests with probes and autoscaling

---

## Summary

| Task | Effort | Priority | Status |
|------|--------|----------|--------|
| Branch Protection Rules | 5 min | High | ⏳ Not implemented |
| Codecov Token | 10 min | Medium | ⏳ Not implemented |
| Environment Configs | 30 min | High | ⏳ Not implemented |

**Next Steps:**
1. Implement branch protection immediately (before first PR)
2. Set up environment configs before first deployment
3. Add Codecov token when you want coverage tracking
