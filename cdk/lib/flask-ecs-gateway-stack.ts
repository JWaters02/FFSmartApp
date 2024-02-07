import {Construct} from "constructs";
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as cdk from 'aws-cdk-lib';
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as iam from "aws-cdk-lib/aws-iam";
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2'; // Import ELBv2 for Application Load Balancer


interface FlaskEcsGatewayStackProps extends cdk.StackProps {
    environVars: { [key: string]: string };
    lambda_resources: lambda.Function[];
    userPoolArn: string;
}

export class FlaskEcsGatewayStack extends cdk.Stack {

    constructor(scope: Construct, id: string, props: FlaskEcsGatewayStackProps) {
        super(scope, id, props);

        // VPC created here since it will not be used by any other stack (for now)
        const vpc = new ec2.Vpc(this, 'AnalysisAndDesignVpc', {
            maxAzs: 2,
            subnetConfiguration: [
                {
                    name: 'public',
                    subnetType: ec2.SubnetType.PUBLIC,
                }
            ],
        });

        // Create an ECS cluster
        const cluster = new ecs.Cluster(this, 'AnalysisAndDesignEcsCluster', {
            vpc: vpc,
        });

        // Set the compute capacity
        cluster.addCapacity('AnalysisAndDesignAutoScalingGroupCapacity', {
            instanceType: new ec2.InstanceType("t4g.nano"),
            machineImage: ecs.EcsOptimizedImage.amazonLinux2(ecs.AmiHardwareType.ARM),
            maxCapacity: 2,
            minCapacity: 1,
            desiredCapacity: 1,
        });

        const repo = ecr.Repository.fromRepositoryName(
            this,
            'MyRepository',
            'analysis-and-design-coursework-private-ecr'
        );

        // Define task
        const taskDef = new ecs.Ec2TaskDefinition(this, 'AnalysisAndDesignTaskDef');

        // Grant permissions to cognito
        const cognitoAccessStatement = new iam.PolicyStatement({
            actions: ['cognito-idp:*'],
            resources: [props.userPoolArn],
            effect: iam.Effect.ALLOW
        });
        const cognitoAccessPolicy = new iam.Policy(this, 'CognitoAccessPolicy', {
            statements: [cognitoAccessStatement]
        });

        taskDef.taskRole.attachInlinePolicy(cognitoAccessPolicy);

        // Create a list of env vars
        const environVars: Record<string, string> = {};
        for (const [key, url] of Object.entries(props.environVars)) {
            environVars[key] = url;
        }

        // Define container
        const containerDef = taskDef.addContainer('AnalysisAndDesignContainer', {
            image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
            memoryLimitMiB: 256,
            environment: environVars,
        });

        containerDef.addPortMappings({
            containerPort: 80,
            hostPort: 80,
            protocol: ecs.Protocol.TCP
        });

        // Instantiate an Amazon ECS Service
        const ECSService = new ecs.Ec2Service(this, 'AnalysisAndDesignService', { cluster, taskDefinition: taskDef });

        // Add a load balancer and expose the service on port 80
        const loadBalancer = new elbv2.ApplicationLoadBalancer(this, 'AnalysisAndDesignLoadBalancer', {
            vpc: vpc,
            internetFacing: true
        });
        const listener = loadBalancer.addListener('AnalysisAndDesignListener', {port: 80});
        const TargetGroup = listener.addTargets('AnalysisAndDesignECSServiceTargetGroup', {
            port: 80,
            targets: [ECSService.loadBalancerTarget({
                containerName: 'AnalysisAndDesignContainer',
                containerPort: 80
            })]
        });

        // Grant permissions
        for (const lambda_function of props.lambda_resources) {
            lambda_function.grantInvoke(taskDef.taskRole);
        }
    }
}
