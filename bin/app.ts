#!/usr/bin/env node
import 'source-map-support/register';
import { App } from 'aws-cdk-lib';
import { FoxEssDischargePredictorStack } from '../src/stack';

const app = new App();

new FoxEssDischargePredictorStack(app, 'FoxEssDischargePredictorStack', {
  env: {
    account: process.env.AWS_ACCOUNT_ID,
    region: process.env.AWS_REGION || 'eu-west-2',
  },
});
