import { Stack, StackProps, Duration } from 'aws-cdk-lib';
import { Function, Runtime, Code } from 'aws-cdk-lib/aws-lambda';
import { Rule, Schedule } from 'aws-cdk-lib/aws-events';
import { LambdaFunction } from 'aws-cdk-lib/aws-events-targets';
import { Role, ServicePrincipal, PolicyStatement } from 'aws-cdk-lib/aws-iam';
import { Construct } from 'constructs';

export class FoxEssDischargePredictorStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const lambdaExecutionRole = new Role(this, 'LambdaExecutionRole', {
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
    });

    lambdaExecutionRole.addToPolicy(
      new PolicyStatement({
        actions: ['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
        resources: ['arn:aws:logs:*:*:*'],
      })
    );

    const dischargePredictorLambda = new Function(this, 'DischargePredictorFunction', {
      runtime: Runtime.PYTHON_3_11,
      handler: 'index.handler',
      code: Code.fromAsset('src/lambda'),
      role: lambdaExecutionRole,
      functionName: 'fox-ess-discharge-predictor',
      memorySize: 128,
      timeout: Duration.seconds(60),
    });

    new Rule(this, 'DailyScheduleRule', {
      schedule: Schedule.cron({ minute: '0', hour: '16', day: '*', month: '*', year: '*' }),
      targets: [new LambdaFunction(dischargePredictorLambda)],
    });
  }
}
