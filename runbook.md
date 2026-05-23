# Fox ESS Discharge Predictor - Operations Runbook

## Overview

This document contains operational procedures for the Fox ESS Discharge Predictor infrastructure, which consists of an AWS Lambda function scheduled to run daily at 4pm UTC via EventBridge.

## Architecture

- **Lambda Function**: `fox-ess-discharge-predictor`
- **Runtime**: Python 3.11
- **Trigger**: EventBridge Rule (Daily 4pm UTC)
- **Region**: eu-west-1 (configurable)

## Deployment

### Prerequisites

- AWS CLI configured with appropriate credentials
- Node.js 20+
- npm dependencies installed

### Deploy via GitHub Actions

1. Ensure `AWS_OIDC_ROLE_ARN` secret is configured in GitHub repository
2. Ensure `AWS_ACCOUNT_ID` variable is set in repository variables
3. Merge code to `main` branch to trigger deployment

### Manual Deployment

```bash
# Install dependencies
npm ci

# Build TypeScript
npm run build

# Synthesize CloudFormation
npx cdk synth

# Deploy to AWS
AWS_ACCOUNT_ID=123456789012 npx cdk deploy --require-approval never
```

### GitLab CI Deployment

1. Configure `AWS_OIDC_ROLE_ARN` variable in GitLab CI/CD settings
2. Ensure OIDC identity provider is configured in AWS IAM
3. Pipeline automatically deploys on merge to `main`

## Monitoring

### CloudWatch Logs

```bash
# Get latest log streams
aws logs describe-log-groups --log-group-name /aws/lambda/fox-ess-discharge-predictor

# Tail recent logs
aws logs tail /aws/lambda/fox-ess-discharge-predictor --follow
```

### Lambda Invocation

Check EventBridge triggers Lambda correctly:

```bash
aws events describe-rule --name FoxEssDischargePredictorStack-DailyScheduleRule
```

## Troubleshooting

### Lambda Not Invoking

1. Verify EventBridge rule is enabled:
   ```bash
   aws events describe-rule --name DailyScheduleRule
   ```

2. Check Lambda permissions:
   ```bash
   aws lambda get-policy --function-name fox-ess-discharge-predictor
   ```

3. Verify CloudWatch event target:
   ```bash
   aws events list-targets-by-rule --rule DailyScheduleRule
   ```

### Deployment Failures

1. Check CDK bootstrap status:
   ```bash
   aws cloudformation describe-stacks --stack-name CDKToolkit
   ```

2. Verify IAM role exists with correct trust policy

3. Review CloudFormation events in AWS Console

## Rollback

To rollback to a previous version:

```bash
# List Lambda versions
aws lambda list-versions-by-function --function-name fox-ess-discharge-predictor

# Update EventBridge to point to specific version
aws events put-targets --rule DailyScheduleRule --targets Id=1,Arn=arn:aws:lambda:eu-west-1:123456789012:function:fox-ess-discharge-predictor:VERSION
```

## Security

### IAM Role Permissions

The Lambda execution role has the following permissions:
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### OIDC Authentication (GitLab CI)

The GitLab CI pipeline assumes an IAM role using OIDC federation:
1. GitLab presents JWT to AWS STS
2. STS returns temporary credentials
3. Credentials used for CDK deployment

## Maintenance

### Update Lambda Code

1. Modify `src/lambda/index.py`
2. Commit and push to trigger deployment
3. Verify new version in CloudWatch logs

### Update CDK Infrastructure

1. Modify CDK files in `src/`
2. Run `npx cdk diff` to preview changes
3. Commit and push to trigger deployment

## Useful Commands

```bash
# Synthesize template
npx cdk synth

# List stacks
npx cdk list

# Destroy stack
npx cdk destroy

# View deployed resources
npx cdk bootstrap --info
```