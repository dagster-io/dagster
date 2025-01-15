data "aws_vpc" "dagster_vpc" {
  # get from var.vpc_id
  id = var.vpc_id
}

locals {
  task_role_arn      = var.create_iam_roles ? aws_iam_role.task[0].arn : var.task_role_arn
  execution_role_arn = var.create_iam_roles ? aws_iam_role.execution[0].arn : var.execution_role_arn
}

resource "aws_security_group" "dagster" {
  name_prefix = "dagster-sg-"
  vpc_id      = var.vpc_id

  # Allow traffic for webserver (HTTP)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow traffic for gRPC services (from other containers)
  ingress {
    from_port   = 4000
    to_port     = 4000
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.dagster_vpc.cidr_block]
  }

  # Egress allows all outbound traffic (common default)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_task_definition" "dagster_daemon" {
  family                   = "dagster-daemon"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = local.task_role_arn
  execution_role_arn       = local.execution_role_arn

  container_definitions = jsonencode([
    {
      name      = "dagster-daemon"
      image     = var.dagster_image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "dagster-daemon"
        }
      }
      command = ["dagster-daemon", "run", "-w", "${var.dagster_home}/workspace.yaml"]
      environment = concat(
        [
          { name = "DAGSTER_HOME", value = var.dagster_home },
          { name = "DAGSTER_POSTGRES_HOST", value = var.postgres_host },
          { name = "DAGSTER_POSTGRES_PASSWORD", value = var.postgres_password }
        ],
        var.environment
      )
      secrets = var.secrets
    }
  ])
}

resource "aws_ecs_service" "dagster_daemon" {
  name            = "dagster-daemon"
  cluster         = var.ecs_cluster_id
  desired_count   = 1
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.dagster_daemon.arn

  network_configuration {
    subnets          = var.daemon_subnet_ids
    security_groups  = [aws_security_group.dagster.id]
    # when running in public subnet, consider setting assign_public_ip = true
    # however, this is not recommended for production as it exposes the container to the internet
    assign_public_ip = var.create_lb ? true : var.assign_public_ip
  }

  force_new_deployment = true
}


resource "aws_ecs_task_definition" "dagster_webserver" {
  family                   = "dagster-webserver"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = local.task_role_arn
  execution_role_arn       = local.execution_role_arn

  container_definitions = jsonencode([
    {
      name      = "dagster-webserver"
      image     = var.dagster_image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "dagster-webserver"
        }
      }
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
          name          = "http"
        }
      ]
      command = ["dagster-webserver", "--host", "0.0.0.0", "--port", "80", "-w", "${var.dagster_home}/workspace.yaml"]
      environment = concat(
        [
          { name = "DAGSTER_HOME", value = var.dagster_home },
          { name = "DAGSTER_POSTGRES_HOST", value = var.postgres_host },
          { name = "DAGSTER_POSTGRES_PASSWORD", value = var.postgres_password }
        ],
        var.environment
      )
      secrets = var.secrets
    }
  ])
}


resource "aws_ecs_service" "dagster-webserver" {
  name            = "dagster-webserver"
  cluster         = var.ecs_cluster_id
  desired_count   = 1
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.dagster_webserver.arn

  network_configuration {
    subnets          = var.webserver_subnet_ids
    security_groups  = [aws_security_group.dagster.id]
    # when running in public subnet, consider setting assign_public_ip = true
    # however, this is not recommended for production as it exposes the container to the internet
    assign_public_ip = var.create_lb ? true : var.assign_public_ip
  }

  dynamic "load_balancer" {
    for_each = var.create_lb ? [1] : []
    content {
      target_group_arn = local.lb_target_group_arn
      container_name   = "dagster-webserver"
      container_port   = 80
    }
  }

  force_new_deployment = true
}
