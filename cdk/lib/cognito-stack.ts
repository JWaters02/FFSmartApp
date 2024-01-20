import * as cdk from "aws-cdk-lib";
import {Construct} from "constructs";
import * as cognito from "aws-cdk-lib/aws-cognito";


export class CognitoStack extends cdk.Stack {

    readonly userPool: cdk.aws_cognito.IUserPool;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        this.userPool = cognito.UserPool.fromUserPoolId(this, 'AnalysisAndDesignImportedUserPool', 'eu-west-1_BGeP1szQM');
    }
}