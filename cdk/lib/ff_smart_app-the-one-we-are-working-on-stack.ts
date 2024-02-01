import * as cdk from 'aws-cdk-lib';
import {Construct} from 'constructs';
import {StorageStack} from "./storage-stack";
import {BasicLambdaToDynamodbStack} from "./basic-lambda-to-dynamodb-stack";
import {EventBridgeTriggeredLambdaToDynamoDbStack} from "./event-bridge-triggered-lambda-to-dynamodb";
import {FlaskEcsGatewayStack} from "./flask-ecs-gateway-stack";
import {CognitoStack} from "./cognito-stack";

export class FfSmartAppTheOneWeAreWorkingOnStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        const cognitoStack = new CognitoStack(this, 'AnalysisAndDesignCognitoStack', {});

        const storageStack = new StorageStack(this, 'AnalysisAndDesignStorageStack', {});

        const fridgeMgr = new BasicLambdaToDynamodbStack(
            this,
            'AnalysisAndDesignFridgeMgrLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignFridgeMgrLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'fridge_mgr.zip',
                masterDb: storageStack.masterDynamoDbTable,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                }
            },
        );

        const ordersMgr = new BasicLambdaToDynamodbStack(
            this,
            'AnalysisAndDesignOrdersMgrLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignOrdersMgrLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'orders_mgr.zip',
                masterDb: storageStack.masterDynamoDbTable,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                }
            },
        );

        const usersMgr = new BasicLambdaToDynamodbStack(
            this,
            'AnalysisAndDesignUsersMgrLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignUsersMgrLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'users_mgr.zip',
                masterDb: storageStack.masterDynamoDbTable,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                }
            }
        );

        const healthReportMgr = new BasicLambdaToDynamodbStack(this,
            'AnalysisAndDesignHealthReportMgrLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignHealthReportMgrLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'health_report_mgr.zip',
                masterDb: storageStack.masterDynamoDbTable,
                sendEmail: true,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                }
            }
        );

        const tokenMgr = new BasicLambdaToDynamodbStack(
            this,
            'AnalysisAndDesignTokenMgrLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignTokenMgrLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'token_mgr.zip',
                masterDb: storageStack.masterDynamoDbTable,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                }
            }
        );

        // Method to get around circular dependency, (even though it's not circular, likely an issue with CDK).
        // This does mean that you will have to deploy the stack twice, once to push the TokenMgrFunctionArn
        // and then again to deploy the updateOrders stack with the lambda function ARN as an environment variable.
        new cdk.CfnOutput(this, 'TokenMgrFunctionArn', {
            value: tokenMgr.lambdaFunction.functionArn,
            exportName: 'TokenMgrFunctionArn',
        });
        const tokenMgrFunctionArn = cdk.Fn.importValue('TokenMgrFunctionArn');

        new cdk.CfnOutput(this, 'OrdersMgrFunctionArn', {
            value: ordersMgr.lambdaFunction.functionArn,
            exportName: 'OrdersMgrFunctionArn',
        });
        const ordersMgrFunctionArn = cdk.Fn.importValue('OrdersMgrFunctionArn');

        new cdk.CfnOutput(this, 'FridgeMgrFunctionArn', {
            value: fridgeMgr.lambdaFunction.functionArn,
            exportName: 'FridgeMgrFunctionArn',
        });
        const fridgeMgrFunctionArn = cdk.Fn.importValue('FridgeMgrFunctionArn');

        const updateOrders = new EventBridgeTriggeredLambdaToDynamoDbStack(
            this,
            'AnalysisAndDesignUpdateOrdersLambdaStack',
            {
                lambdaName: 'AnalysisAndDesignUpdateOrdersLambda',
                s3BucketWithSourceCode: storageStack.lambdaBucket,
                s3KeyToZipFile: 'update_orders.zip',
                masterDb: storageStack.masterDynamoDbTable,
                lambda_resources: [
                    tokenMgr.lambdaFunction,
                    ordersMgr.lambdaFunction,
                    fridgeMgr.lambdaFunction
                ],
                sendEmail: true,
                environment: {
                    'MASTER_DB': storageStack.masterDynamoDbTable.tableName,
                    'TOKEN_MGR_ARN': tokenMgrFunctionArn,
                    'ORDERS_MGR_ARN': ordersMgrFunctionArn,
                    'FRIDGE_MGR_ARN': fridgeMgrFunctionArn,
                    'USER_POOL_ID': cognitoStack.userPool.userPoolId,
                },
                userPoolArn: cognitoStack.userPool.userPoolArn,
            }
        );

        const ecs = new FlaskEcsGatewayStack(this, 'AnalysisAndDesignEcsStack', {
            environmentVariables: {
                'DYNAMODB_TABLE': storageStack.sessionsDynamoDbTable.tableName,
                'FRIDGE_MGR_NAME': fridgeMgr.lambdaFunction.functionName,
                'ORDERS_MGR_NAME': ordersMgr.lambdaFunction.functionName,
                'USERS_MGR_NAME': usersMgr.lambdaFunction.functionName,
                'HEALTH_REPORT_MGR_NAME': healthReportMgr.lambdaFunction.functionName,
                'TOKEN_MGR_NAME': tokenMgr.lambdaFunction.functionName,
            },
            lambda_resources: [
                fridgeMgr.lambdaFunction,
                ordersMgr.lambdaFunction,
                usersMgr.lambdaFunction,
                healthReportMgr.lambdaFunction,
                tokenMgr.lambdaFunction,
            ]
        });
    }
}
