import * as lambda from "aws-cdk-lib/aws-lambda";
import * as cdk from "aws-cdk-lib";
import {Construct} from "constructs";
import * as DynamoDB from "aws-cdk-lib/aws-dynamodb";
import {IBucket} from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";

interface LambdaStackProps extends cdk.StackProps {
    lambdaName: string;
    s3BucketWithSourceCode: IBucket;
    s3KeyToZipFile: string;
    masterDb: DynamoDB.Table;
    environment?: { [key: string]: string };
    sendEmail?: boolean;
}

export class BasicLambdaToDynamodbStack extends cdk.Stack {

    readonly lambdaFunction: lambda.Function;

    constructor(scope: Construct, id: string, props: LambdaStackProps) {
        super(scope, id, props);

        this.lambdaFunction = new lambda.Function(this, props.lambdaName, {
            runtime: lambda.Runtime.PYTHON_3_9,
            handler: 'src/index.handler',
            code: lambda.Code.fromBucket(props.s3BucketWithSourceCode, props.s3KeyToZipFile),
            timeout: cdk.Duration.seconds(10),
            environment: props.environment,
        })

        if (props.sendEmail) {
            this.lambdaFunction.addToRolePolicy(new iam.PolicyStatement({
                actions: ['ses:SendEmail', 'ses:SendRawEmail'],
                resources: ['*'],
                effect: iam.Effect.ALLOW,
            }));
        }

        props.masterDb.grantReadWriteData(this.lambdaFunction);
    }
}