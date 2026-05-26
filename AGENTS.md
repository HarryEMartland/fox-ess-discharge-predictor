# AGENTS.md

## Project
- **Name**: fox-ess-discharge-predictor
- **Type**: AWS CDK (TypeScript) + Python Lambda
- **Stack**: `FoxEssDischargePredictorStack` in `src/stack.ts`
- **Entry**: `bin/app.ts`
- **Lambda**: Python 3.11 in `src/lambda/`
- **API Docs**: https://www.foxesscloud.com/public/i18n/en/OpenApiDocument.html
- **Octopus API**: https://api.octopus.energy/v1/schema?namespaces=default

## Commands

| Command | Action |
|---------|--------|
| `npm run build` | TypeScript compile (`tsc`) |
| `npm run watch` | TypeScript watch compile |
| `npm run lint:fix` | ESLint + Prettier fix |
| `npm test` | Jest tests |
| `npm run synth` | CDK synth |
| `npm run cdk ...` | CDK CLI passthrough |
| `cd src/lambda && ruff check .` | Python lint |
| `cd src/lambda && ruff format --check .` | Python format check |
| `cd src/lambda && python -m pytest` | Python tests |

## Conventions

### TypeScript (CDK)
- Strict mode, ES2020, commonjs modules
- No explicit `any` (error), unused vars warn (ignore `_` prefix)
- Tests: Jest with ts-jest, file `test/stack.test.ts`
- Stack class extends `aws-cdk-lib` Stack

### Python (Lambda)
- Ruff for linting and formatting
- pytest for unit tests
- Test files prefixed `test_` alongside source

## CI/CD
- GitHub Actions: `.github/workflows/`
- OIDC for AWS auth
