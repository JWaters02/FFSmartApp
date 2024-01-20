import * as cdk from 'aws-cdk-lib';
import {Construct} from "constructs";
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as elbv2 from 'aws-cdk-lib/aws-elasticloadbalancingv2'; // Import ELBv2 for Application Load Balancer
import * as lambda from "aws-cdk-lib/aws-lambda";

interface FlaskEcsGatewayStackProps extends cdk.StackProps {
    environmentVariables: { [key: string]: string };
    lambda_resources: lambda.Function[];
}

export class FlaskEcsGatewayStack extends cdk.Stack {

    constructor(scope: Construct, id: string, props: FlaskEcsGatewayStackProps) {
        super(scope, id, props);

        // TODO: needs permissions for cognito

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

        // Add capacity to it
        cluster.addCapacity('AnalysisAndDesignAutoScalingGroupCapacity', {
            instanceType: new ec2.InstanceType("t4g.nano"),
            machineImage: ecs.EcsOptimizedImage.amazonLinux2(ecs.AmiHardwareType.ARM),
            desiredCapacity: 1,
            minCapacity: 1,
            maxCapacity: 2,
        });

        const repository = ecr.Repository.fromRepositoryName(
            this,
            'MyRepository',
            'analysis-and-design-coursework-private-ecr'
        );

        // Create a task definition and expose port 80
        const taskDefinition = new ecs.Ec2TaskDefinition(this, 'AnalysisAndDesignTaskDef');

        // Create environment variables from props
        const environmentVariables: Record<string, string> = {};
        for (const [key, url] of Object.entries(props.environmentVariables)) {
            environmentVariables[key] = url;
        }

        // Add container to task definition
        const container = taskDefinition.addContainer('AnalysisAndDesignContainer', {
            image: ecs.ContainerImage.fromEcrRepository(repository, 'latest'),
            memoryLimitMiB: 256,
            environment: environmentVariables,
        });

        container.addPortMappings({
            containerPort: 80,
            hostPort: 80,
            protocol: ecs.Protocol.TCP
        });

        // Instantiate an Amazon ECS Service
        const ECSService = new ecs.Ec2Service(this, 'AnalysisAndDesignService', { cluster, taskDefinition });

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
            lambda_function.grantInvoke(taskDefinition.taskRole);
        }
    }
}
