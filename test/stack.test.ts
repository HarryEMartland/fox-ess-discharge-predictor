import { App } from 'aws-cdk-lib';
import { Template } from 'aws-cdk-lib/assertions';
import { FoxEssDischargePredictorStack } from '../src/stack';

describe('FoxEssDischargePredictorStack', () => {
  test('synthesizes correctly', () => {
    const app = new App();
    const stack = new FoxEssDischargePredictorStack(app, 'TestStack', {
      env: {
        account: '123456789012',
        region: 'eu-west-1',
      },
    });

    const template = Template.fromStack(stack);

    template.hasResourceProperties('AWS::Lambda::Function', {
      Runtime: 'python3.11',
      Handler: 'index.handler',
      MemorySize: 128,
      Timeout: 60,
    });

    template.hasResourceProperties('AWS::Events::Rule', {
      ScheduleExpression: 'cron(0 16 * * ? *)',
    });

    template.resourceCountIs('AWS::Lambda::Function', 1);
    template.resourceCountIs('AWS::Events::Rule', 1);
    template.resourceCountIs('AWS::IAM::Role', 1);
  });
});