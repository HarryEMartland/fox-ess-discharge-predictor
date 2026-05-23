# Fox ESS Discharge Predictor - CDK Infrastructure Specification

## Project Overview

- **Project Name**: fox-ess-discharge-predictor
- **Project Type**: AWS CDK Infrastructure as Code with Python Lambda
- **Core Functionality**: Deploys a scheduled Python Lambda function that runs daily at 4pm to predict discharge patterns for Fox ESS energy storage systems
- **Target Users**: DevOps engineers and developers working on the Fox ESS integration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS Cloud                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   CDK Stack                          │   │
│  │  ┌────────────────┐  ┌─────────────────────────┐   │   │
│  │  │ EventBridge    │──│  Python Lambda Function  │   │   │
│  │  │ (Daily 4PM UTC)│  │  fox_ess_discharge_logic │   │   │
│  │  └────────────────┘  └─────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Infrastructure Components

### AWS Resources

1. **Lambda Function**
   - Runtime: Python 3.11
   - Handler: `index.handler`
   - Memory: 128MB
   - Timeout: 60 seconds
   - Architecture: x86_64

2. **EventBridge Rule**
   - Schedule: `cron(0 16 * * ? *)` - Daily at 4pm UTC
   - Target: Lambda function

3. **IAM Role**
   - Lambda execution role with CloudWatch logging permissions

## CI/CD Pipeline

### GitHub Actions

- **Lint**: ESLint for TypeScript, Ruff for Python
- **Test**: CDK synth and diff
- **Deploy**: CDK deploy with OIDC authentication

### GitLab CI

- **ODC**: OpenID Connect for AWS authentication
- **Stages**: lint, test, deploy

## Configuration

### Environment Variables

- `AWS_ACCOUNT_ID`: Target AWS account
- `AWS_REGION`: Target AWS region (default: eu-west-1)
- `ENVIRONMENT`: deploy target (dev/staging/prod)

## File Structure

```
fox-ess-discharge-predictor/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Lint and test
│       └── deploy.yml      # Deploy to AWS
├── .gitlab/
│   └── ci.yml              # GitLab CI with OIDC
├── src/
│   ├── index.ts            # CDK entry point
│   ├── lambda/
│   │   └── handler.py      # Lambda function
│   └── stack.ts            # Stack definition
├── bin/
│   └── app.ts              # CDK app bootstrap
├── test/
│   └── stack.test.ts       # Stack unit tests
├── runbook.md              # Operations manual
├── package.json
├── tsconfig.json
├── cdk.json
├── .eslintrc.yml
├── .prettierrc.yml
├── pyproject.toml          # Python config
├── requirements.txt        # Lambda deps
├── requirements-dev.txt    # Dev deps
└── SPEC.md
```

## Acceptance Criteria

1. CDK project synthesizes without errors
2. Python Lambda is deployed with EventBridge trigger
3. GitHub Actions workflow runs lint and test
4. GitLab CI uses OIDC to assume AWS role
5. Runbook documents deployment and operations
6. All linting passes (ESLint, Prettier, Ruff)