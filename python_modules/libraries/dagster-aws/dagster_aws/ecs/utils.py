import re


def sanitize_family(family):
    # Trim the location name and remove special characters
    return re.sub(r"[^\w^\-]", "", family)[:255]


def should_assign_public_ip(ec2, subnet_ids):
    # https://docs.aws.amazon.com/AmazonECS/latest/userguide/fargate-task-networking.html
    # Assign a public IP if any of the subnets are public
    route_tables = ec2.route_tables.filter(
        Filters=[
            {"Name": "association.subnet-id", "Values": subnet_ids},
        ]
    )

    # Consider a subnet to be public if it has a route that targets
    # an internet gateway; private subnets have routes that target NAT gateways
    for route_table in route_tables:
        if any(route.nat_gateway_id for route in route_table.routes):
            return "DISABLED"
    return "ENABLED"
