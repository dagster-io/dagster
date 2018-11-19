import * as pulumi from "@pulumi/pulumi";
import * as aws from '@pulumi/aws';
import * as awsInfra from "@pulumi/aws-infra";
import { AmazonRoute53DomainsFullAccess } from "@pulumi/aws/iam";


// This assumes the existence of the hosted zone
let zone = aws.route53.getZone({'name': 'dagster.io'});

let network = new awsInfra.Network('airline_demo_vpc', {
    numberOfAvailabilityZones: 3,
    usePrivateSubnets: true,
});

let redshift_subnet_group = new aws.redshift.SubnetGroup(
    'airline_demo_redshift_subnet_group', {
        subnetIds: network.publicSubnetIds,
        name: 'airline-demo-redshift-subnet-group',
        description: 'Managed by Pulumi'
    });

let redshift_security_group = new aws.ec2.SecurityGroup(
    'airline_demo_redshift_security_group', {
        name: 'airline_demo_redshift_security_group',
        description: 'Managed by Pulumi',
        vpcId: network.vpcId,
        ingress: [{
            cidrBlocks: ['0.0.0.0/0'],
            fromPort: 0,
            toPort: 65535,
            protocol: 'tcp',
        }],
    });

    // let redshift_iam_role = 

let redshift = new aws.redshift.Cluster('airline_demo_redshift', {
    allowVersionUpgrade: false,
    automatedSnapshotRetentionPeriod: 0,
    clusterIdentifier: 'airline-demo-redshift',
    // clusterSecurityGroups: [],
    clusterSubnetGroupName: redshift_subnet_group.name,
    clusterType: 'single-node',
    databaseName: 'airline_demo',
    // iamRoles: [],
    logging: {
        enable: false,
    },
    masterPassword: 'A1rline_demo_password',
    masterUsername: 'airline_demo_username',
    nodeType: 'dc1.large',
    numberOfNodes: 1,
    publiclyAccessible: true,
    skipFinalSnapshot: true,
    vpcSecurityGroupIds: [redshift_security_group.id]
});

zone.then((zone) => {
    let dbRecord = new aws.route53.Record('db.airline-demo.dagster.io.', {
        'name': 'db.airline-demo.dagster.io.',
        'type': 'CNAME',
        'zoneId': zone.zoneId,
        'records': [redshift.dnsName],
        'ttl': 300,
    })
});

let emrServiceRoleAssumeRolePolicy = `{
    "Version": "2008-10-17",
    "Statement": [
      {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
          "Service": "elasticmapreduce.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
`;

let emr_iam_service_role = new aws.iam.Role('airline_demo_emr_service_role', {
    assumeRolePolicy: emrServiceRoleAssumeRolePolicy,
});

let emr_managed_master_security_group = new aws.ec2.SecurityGroup(
    'airline_demo_emr_managed_master_security_group', {
        name: 'airline_demo_emr_managed_master_security_group',
        description: 'Managed by Pulumi',
        vpcId: network.vpcId,
        ingress: [{
            cidrBlocks: ['0.0.0.0/0'],
            fromPort: 0,
            toPort: 0,
            protocol: '-1',
        }],
        egress: [{
            cidrBlocks: ['0.0.0.0/0'],
            fromPort: 0,
            toPort: 0,
            protocol: '-1'
        }],
    }
);

let emr_managed_slave_security_group = new aws.ec2.SecurityGroup(
    'airline_demo_emr_managed_slave_security_group', {
        name: 'airline_demo_emr_managed_slave_security_group',
        description: 'Managed by Pulumi',
        vpcId: network.vpcId,
        ingress: [{
            cidrBlocks: ['0.0.0.0/0'],
            fromPort: 0,
            toPort: 65535,
            protocol: 'tcp',
        }],
    }
);

let emrIamProfileRoleAssumeRolePolicy = `{
    "Version": "2008-10-17",
    "Statement": [
      {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
`

let emr_iam_profile_role = new aws.iam.Role(
    'airline_demo_emr_iam_profile_role', {
        assumeRolePolicy: emrIamProfileRoleAssumeRolePolicy
})

let emrIamProfileRolePolicyPolicy = `{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Resource": "*",
        "Action": [
            "cloudwatch:*",
            "dynamodb:*",
            "ec2:Describe*",
            "elasticmapreduce:Describe*",
            "elasticmapreduce:ListBootstrapActions",
            "elasticmapreduce:ListClusters",
            "elasticmapreduce:ListInstanceGroups",
            "elasticmapreduce:ListInstances",
            "elasticmapreduce:ListSteps",
            "kinesis:CreateStream",
            "kinesis:DeleteStream",
            "kinesis:DescribeStream",
            "kinesis:GetRecords",
            "kinesis:GetShardIterator",
            "kinesis:MergeShards",
            "kinesis:PutRecord",
            "kinesis:SplitShard",
            "rds:Describe*",
            "s3:*",
            "sdb:*",
            "sns:*",
            "sqs:*"
        ]
    }]
}
`;

let emr_iam_profile_role_policy = new aws.iam.RolePolicy(
    'airline_demo_emr_iam_profile_role_policy', {
        role: emr_iam_profile_role,
        policy: emrIamProfileRolePolicyPolicy,
    }
)

let emrIamServiceRolePolicyPolicy = `{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Resource": "*",
        "Action": [
            "ec2:AuthorizeSecurityGroupEgress",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:CancelSpotInstanceRequests",
            "ec2:CreateNetworkInterface",
            "ec2:CreateSecurityGroup",
            "ec2:CreateTags",
            "ec2:DeleteNetworkInterface",
            "ec2:DeleteSecurityGroup",
            "ec2:DeleteTags",
            "ec2:DescribeAvailabilityZones",
            "ec2:DescribeAccountAttributes",
            "ec2:DescribeDhcpOptions",
            "ec2:DescribeInstanceStatus",
            "ec2:DescribeInstances",
            "ec2:DescribeKeyPairs",
            "ec2:DescribeNetworkAcls",
            "ec2:DescribeNetworkInterfaces",
            "ec2:DescribePrefixLists",
            "ec2:DescribeRouteTables",
            "ec2:DescribeSecurityGroups",
            "ec2:DescribeSpotInstanceRequests",
            "ec2:DescribeSpotPriceHistory",
            "ec2:DescribeSubnets",
            "ec2:DescribeVpcAttribute",
            "ec2:DescribeVpcEndpoints",
            "ec2:DescribeVpcEndpointServices",
            "ec2:DescribeVpcs",
            "ec2:DetachNetworkInterface",
            "ec2:ModifyImageAttribute",
            "ec2:ModifyInstanceAttribute",
            "ec2:RequestSpotInstances",
            "ec2:RevokeSecurityGroupEgress",
            "ec2:RunInstances",
            "ec2:TerminateInstances",
            "ec2:DeleteVolume",
            "ec2:DescribeVolumeStatus",
            "ec2:DescribeVolumes",
            "ec2:DetachVolume",
            "iam:GetRole",
            "iam:GetRolePolicy",
            "iam:ListInstanceProfiles",
            "iam:ListRolePolicies",
            "iam:PassRole",
            "s3:CreateBucket",
            "s3:Get*",
            "s3:List*",
            "sdb:BatchPutAttributes",
            "sdb:Select",
            "sqs:CreateQueue",
            "sqs:Delete*",
            "sqs:GetQueue*",
            "sqs:PurgeQueue",
            "sqs:ReceiveMessage"
        ]
    }]
}
`;

let emr_iam_service_policy = new aws.iam.RolePolicy(
    'airline_demo_emr_iam_service_policy', {
        role: emr_iam_service_role,
        policy: emrIamServiceRolePolicyPolicy,
    }
)
let emr_iam_instance_profile = new aws.iam.InstanceProfile(
    'airline_demo_emr_iam_instance_profile', {
        role: emr_iam_profile_role
    }
)

let configurationsJson = `[
    {
      "Classification": "hadoop-env",
      "Configurations": [
        {
          "Classification": "export",
          "Properties": {
            "JAVA_HOME": "/usr/lib/jvm/java-1.8.0"
          }
        }
      ],
      "Properties": {}
    },
    {
      "Classification": "spark-env",
      "Configurations": [
        {
          "Classification": "export",
          "Properties": {
            "JAVA_HOME": "/usr/lib/jvm/java-1.8.0"
          }
        }
      ],
      "Properties": {}
    }
]
`
let spark_cluster = new aws.emr.Cluster('airline_demo_spark_cluster', {
    releaseLabel: 'emr-5.19.0',
    applications: ['Spark'],
    terminationProtection: false,
    keepJobFlowAliveWhenNoSteps: true,
    serviceRole: emr_iam_service_role.arn,
    ec2Attributes: {
        subnetId: network.publicSubnetIds[0],
        // emrManagedMasterSecurityGroup: emr_managed_master_security_group.id,
        // emrManagedSlaveSecurityGroup: emr_managed_slave_security_group.id,
        instanceProfile: emr_iam_instance_profile.arn
    },
    masterInstanceType: 'm5.xlarge',
    coreInstanceType: 'm5.xlarge',
    coreInstanceCount: 1,
    // bootstrapActions: [{
    //     path: 's3://elasticmapreduce/bootstrap-actions/run-if',
    //     name: 'runif',
    //     args: ['instance.isMaster=true', 'echo running on master node']
    // }],
    configurationsJson: configurationsJson
});

zone.then((zone) => {
    let dbRecord = new aws.route53.Record('spark.airline-demo.dagster.io.', {
        'name': 'spark.airline-demo.dagster.io.',
        'type': 'CNAME',
        'zoneId': zone.zoneId,
        'records': [spark_cluster.masterPublicDns],
        'ttl': 300,
    })
});
