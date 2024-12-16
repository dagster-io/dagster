data "aws_vpc" "current" {
  # get from var.vpc_id
  id = var.vpc_id
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

resource "aws_ecs_task_definition" "dagster_daemon" {
  family                   = "dagster-daemon"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.execution_role_arn

  container_definitions = jsonencode([
    {
      name      = "dagster-daemon"
      image     = var.dagster_image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group
          "awslogs-region"        = var.region
          "awslogs-stream-prefix" = "dagster-daemon"
        }
      }
      command = ["dagster-daemon", "run", "-w", "${var.dagster_home}/workspace.yaml"]
      environment = [
        { name = "DAGSTER_HOME", value = var.dagster_home },
        { name = "DAGSTER_POSTGRES_HOST", value = var.postgres_host },
        { name = "DAGSTER_POSTGRES_PASSWORD", value = var.postgres_password }
      ]
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
    subnets          = var.subnets
    security_groups  = [aws_security_group.dagster.id]
    assign_public_ip = true
  }
}

resource "aws_ecs_task_definition" "dagster_webserver" {
  family                   = "dagster-webserver"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.execution_role_arn

  container_definitions = jsonencode([
    {
      name      = "dagster-webserver"
      image     = var.dagster_image
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.log_group
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
      environment = [
        { name = "DAGSTER_HOME", value = var.dagster_home },
        { name = "DAGSTER_S3_BUCKET", value = var.s3_bucket },
        { name = "DAGSTER_POSTGRES_HOST", value = var.postgres_host },
        { name = "DAGSTER_POSTGRES_PASSWORD", value = var.postgres_password }
      ]
    }
  ])
}

resource "aws_lb" "dagster_webserver" {
  name               = "dagster-webserver-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.dagster.id]
  subnets            = var.subnets
}

resource "aws_lb_target_group" "dagster_webserver" {
  name        = "dagster-webserver-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id
  health_check {
    path                = "/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200-399"
  }
}

resource "aws_lb_listener" "dagster_webserver" {
  load_balancer_arn = aws_lb.dagster_webserver.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.dagster_webserver.arn
  }
}

resource "aws_ecs_service" "dagster-webserver" {
  name            = "dagster-webserver"
  cluster         = var.ecs_cluster_id
  desired_count   = 1
  launch_type     = "FARGATE"
  task_definition = aws_ecs_task_definition.dagster_webserver.arn

  network_configuration {
    subnets          = var.subnets
    security_groups  = [aws_security_group.dagster.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.dagster_webserver.arn
    container_name   = "dagster-webserver"
    container_port   = 80
  }
}
