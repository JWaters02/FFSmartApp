import * as cdk from 'aws-cdk-lib';
import {BasicLambdaToDynamodbStack} from "./basic-lambda-to-dynamodb-stack";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as DynamoDB from "aws-cdk-lib/aws-dynamodb";
import * as events from "aws-cdk-lib/aws-events";
import { Construct } from 'constructs';
import {IBucket} from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as targets from 'aws-cdk-lib/aws-events-targets';

interface eventBridgeTriggeredLambdaToDynamoDbStackProps extends cdk.StackProps {
    lambdaName: string;
    s3BucketWithSourceCode: IBucket;
    s3KeyToZipFile: string;
    masterDb: DynamoDB.Table;
    lambda_resources: lambda.Function[];
    sendEmail: boolean;
    environment?: { [key: string]: string };
    userPoolArn?: string;
}

export class EventBridgeTriggeredLambdaToDynamoDbStack extends cdk.Stack {

    readonly lambdaFunction: lambda.Function;
    readonly eventBridgeRule: events.Rule;

    constructor(scope: Construct, id: string, props: eventBridgeTriggeredLambdaToDynamoDbStackProps) {
        super(scope, id, props);

        // define lambda
        const basicLambdaToDynamodbStackName = props.lambdaName + 'Stack';

        const basicLambdaToDynamodbStack = new BasicLambdaToDynamodbStack(
            this,
            basicLambdaToDynamodbStackName,
            {
                lambdaName: props.lambdaName,
                s3BucketWithSourceCode: props.s3BucketWithSourceCode,
                s3KeyToZipFile: props.s3KeyToZipFile,
                masterDb: props.masterDb,
                environment: props.environment,
                sendEmail: props.sendEmail,
            },
        );

        this.lambdaFunction = basicLambdaToDynamodbStack.lambdaFunction;

        // define event bridge rule
        const ruleName = props.lambdaName + 'DailyRunRule';

        this.eventBridgeRule = new events.Rule(this, ruleName, {
            schedule: events.Schedule.rate(cdk.Duration.days(1)),
        })

        this.eventBridgeRule.addTarget(new targets.LambdaFunction(this.lambdaFunction));

        for (const lambda_function of props.lambda_resources) {
            lambda_function.grantInvoke(this.lambdaFunction);
        }

        if (props.userPoolArn && this.lambdaFunction.role) {
            const cognitoAccessStatement = new iam.PolicyStatement({
                actions: ['cognito-idp:*'],
                resources: [props.userPoolArn],
                effect: iam.Effect.ALLOW
            });

            const cognitoAccessPolicy = new iam.Policy(this, 'CognitoAccessPolicy', {
                statements: [cognitoAccessStatement]
            });

            this.lambdaFunction.role.attachInlinePolicy(cognitoAccessPolicy);
        }
    }
}