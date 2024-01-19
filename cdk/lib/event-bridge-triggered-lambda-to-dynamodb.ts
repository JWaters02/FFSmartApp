import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {BasicLambdaToDynamodbStack} from "./basic-lambda-to-dynamodb-stack";
import {IBucket} from "aws-cdk-lib/aws-s3";
import * as DynamoDB from "aws-cdk-lib/aws-dynamodb";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from 'aws-cdk-lib/aws-events-targets';

interface eventBridgeTriggeredLambdaToDynamoDbStackProps extends cdk.StackProps {
    lambdaName: string;
    s3BucketWithSourceCode: IBucket;
    s3KeyToZipFile: string;
    masterDb: DynamoDB.Table;
    lambdaToBeInvoked: lambda.Function;
    sendEmail: boolean;
    environment?: { [key: string]: string };
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

        props.lambdaToBeInvoked.grantInvoke(this.lambdaFunction);
    }
}