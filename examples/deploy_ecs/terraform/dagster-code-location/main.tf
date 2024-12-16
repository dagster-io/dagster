data "aws_vpc" "current" {
  id = var.vpc_id
}

resource "aws_security_group" "code_location" {
  name_prefix = "code-location-sg-"
  vpc_id      = var.vpc_id

  # Allow traffic on port 4000 (from dagster services or internal network)
  ingress {
    from_port   = 4000
    to_port     = 4000
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.current.cidr_block]
  }

  # Egress allows all outbound traffic (common default)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "code_location" {
  family                   = var.service_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = var.task_role_arn
  execution_role_arn = var.execution_role_arn

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = var.image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group" = var.log_group
          "awslogs-region" = var.region
          "awslogs-stream-prefix" = var.service_name
        }
      }
      command   = ["dagster", "api", "grpc", "--module-name", var.module_name, "--host", "0.0.0.0", "--port", "4000"]
      portMappings = [
        {
          containerPort = 4000
          hostPort      = 4000
          protocol      = "tcp"
          name         = "grpc"
        }
      ]
      environment = [
        { name = "DAGSTER_CURRENT_IMAGE", value = var.image },
        { name = "DAGSTER_HOME", value = var.dagster_home },
        { name = "DAGSTER_POSTGRES_HOST", value = var.postgres_host },
        { name = "DAGSTER_POSTGRES_PASSWORD", value = var.postgres_password },
        { name = "DAGSTER_S3_BUCKET", value = var.s3_bucket },
      ]
    }
  ])
}

# Create a service discovery service
resource "aws_service_discovery_service" "dagster-code-location" {
  name = var.service_name

  dns_config {
    namespace_id = var.namespace_id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_ecs_service" "code_location" {
  name          = var.service_name
  cluster        = var.ecs_cluster_id
  desired_count  = 1
  launch_type    = "FARGATE"
  task_definition = aws_ecs_task_definition.code_location.arn

  network_configuration {
    subnets         = var.subnets
    security_groups = [aws_security_group.code_location.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.dagster-code-location.arn
  }
}
