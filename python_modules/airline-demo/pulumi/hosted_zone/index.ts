import * as pulumi from "@pulumi/pulumi";
import * as aws from '@pulumi/aws';

console.log(`
Note that if you destroy the dagster.io. Route53 Hosted Zone, nameservers
may change and may need to be updated at Godaddy. The current nameservers are:

    ns-1737.awsdns-25.co.uk
    ns-1421.awsdns-49.org
    ns-898.awsdns-48.net
    ns-481.awsdns-60.com

and the current Hosted Zone id is Z147QD9GP23Q35.
`)

let zone = new aws.route53.Zone('dagster.io.', {
    'forceDestroy': true,
    'name': 'dagster.io',
});
