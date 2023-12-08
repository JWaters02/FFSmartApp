import * as cdk from "aws-cdk-lib";
import {Construct} from "constructs";
import * as S3 from "aws-cdk-lib/aws-s3";
import * as DynamoDB from "aws-cdk-lib/aws-dynamodb";

export class StorageStack extends cdk.Stack {

    readonly lambdaBucket: S3.IBucket;
    readonly masterDynamoDbTable: DynamoDB.Table;
    readonly sessionsDynamoDbTable: DynamoDB.Table;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        this.masterDynamoDbTable = new DynamoDB.Table(this, 'analysis-and-design-course-work-master-dynamo-db-table', {
            partitionKey: {
                name: 'pk',
                type: DynamoDB.AttributeType.STRING
            },
            sortKey: {
                name: 'type',
                type: DynamoDB.AttributeType.STRING
            },
        });


        this.sessionsDynamoDbTable = new DynamoDB.Table(this, 'analysis-and-design-ecs-session-table', {
            partitionKey: {
                name: 'session_id',
                type: DynamoDB.AttributeType.STRING,
            },
            tableName: 'analysis-and-design-ecs-session-table',
            removalPolicy: cdk.RemovalPolicy.DESTROY,
        });


        this.lambdaBucket = S3.Bucket.fromBucketArn(
            this,
            'analysis-and-design-course-work-lambda-buckets',
            'arn:aws:s3:::analysis-and-design-course-work-lambda-buckets'
        );
    }
}