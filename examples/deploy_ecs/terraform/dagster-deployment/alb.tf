locals {
  dagster_webserver_lb_dns_name = var.create_lb ? aws_lb.dagster_webserver[0].dns_name : null
  lb_target_group_arn = var.create_lb ? aws_lb_target_group.dagster_webserver[0].arn : var.lb_target_group_arn
}

resource "aws_lb" "dagster_webserver" {
  count = var.create_lb ? 1 : 0
  # no longer than 6 characters
  name_prefix        = "dgweb-"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.dagster.id]
  subnets            = var.webserver_subnet_ids
}

resource "aws_lb_target_group" "dagster_webserver" {
  count       = var.create_lb ? 1 : 0
  # no longer than 6 characters
  name_prefix = "dgweb-"
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
  count             = var.create_lb ? 1 : 0
  load_balancer_arn = aws_lb.dagster_webserver[0].arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = local.lb_target_group_arn
  }
}
