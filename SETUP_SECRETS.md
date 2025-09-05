# GitHub Repository Secrets Setup

This document explains how to configure required secrets for CI/CD pipelines in the BMI-App_2025_clean repository.

## Required Secrets

### CODECOV_TOKEN

The `CODECOV_TOKEN` is required for uploading code coverage reports to Codecov from GitHub Actions workflows.

#### How to Set Up CODECOV_TOKEN

1. **Get your Codecov token:**
   - Go to [codecov.io](https://codecov.io/)
   - Sign in with your GitHub account
   - Navigate to your repository: `https://codecov.io/gh/Katsiarynakavaleuskaya/BMI-App_2025_clean`
   - Go to Settings → General → Repository Upload Token
   - Copy the token value

2. **Add the secret to GitHub repository:**
   - Go to your GitHub repository: `https://github.com/Katsiarynakavaleuskaya/BMI-App_2025_clean`
   - Click on **Settings** tab
   - In the left sidebar, click **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `CODECOV_TOKEN`
   - Secret: paste the token from step 1
   - Click **Add secret**

#### Verification

After adding the secret, your GitHub Actions workflows will automatically start uploading coverage reports to Codecov. You can verify this by:

1. Running a build or creating a pull request
2. Checking the workflow logs for successful codecov upload steps
3. Visiting your Codecov dashboard to see coverage reports

## Workflows Using CODECOV_TOKEN

The following GitHub Actions workflows use this secret:

- `.github/workflows/python-tests.yml` - Main test workflow with coverage
- `.github/workflows/ci.yml` - Continuous integration workflow

Both workflows are configured with `continue-on-error: true` for codecov uploads, so builds won't fail if the token is missing, but you won't get coverage reports.

## Local Development

For local development, you don't need the CODECOV_TOKEN. The token is only used in CI/CD environments. You can run tests locally with coverage using:

```bash
pytest --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=96
```

## Troubleshooting

If you're experiencing issues with codecov uploads:

1. Verify the token is correctly set in GitHub repository secrets
2. Check that the token hasn't expired
3. Ensure your repository is properly connected to Codecov
4. Review workflow logs for specific error messages

For more information, see the [Codecov documentation](https://docs.codecov.com/).