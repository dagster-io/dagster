resource "aws_iam_role" "task" {
  count       = var.create_iam_roles ? 1 : 0
  name_prefix = "dagster-ecs-task-"
  description = "Role for Dagster ECS tasks"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "task" {
  count       = var.create_iam_roles ? 1 : 0
  name_prefix = "dagster-ecs-task-"
  description = "Policy for Dagster ECS tasks"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      # full access to specific s3 bucket
      {
        Effect = "Allow",
        Action = "s3:*",
        Resource = "*"
      },
      # actions for the ECS Run Launcher and ECS Executor
      {
        Effect = "Allow",
        Action = [
          "iam:PassRole",
          "ecs:RunTask",
          "ecs:DescribeTasks",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "ecs:ListTasks",
          "ecs:StopTask",
          "ecs:TagResource",
          "ec2:DescribeNetworkInterfaces",
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:ListSecrets",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:DescribeLogStreams",
        ],
        Resource = "*"
      }
    ],
  })
}


resource "aws_iam_role_policy_attachment" "task" {
  count      = var.create_iam_roles ? 1 : 0
  role       = aws_iam_role.task[0].name
  policy_arn = aws_iam_policy.task[0].arn
}

resource "aws_iam_policy_attachment" "task-AmazonECSTaskExecutionRolePolicy" {
  count      = var.create_iam_roles ? 1 : 0
  name       = "${aws_iam_role.task[0].name}-AmazonECSTaskExecutionRolePolicy"
  roles      = [aws_iam_role.task[0].name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "execution" {
  count       = var.create_iam_roles ? 1 : 0
  name_prefix = "dagster-ecs-execution-"
  description = "Role for ECS task execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "execution-AmazonECSTaskExecutionRolePolicy" {
  count      = var.create_iam_roles ? 1 : 0
  role       = aws_iam_role.execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "execution" {
  count       = var.create_iam_roles ? 1 : 0
  name_prefix = "dagster-ecs-execution-"
  description = "Policy for ECS execution role with ECR permissions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:DescribeLogStreams",
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "dagster-ecs-execution-role-policy-attachment" {
  count      = var.create_iam_roles ? 1 : 0
  role       = aws_iam_role.execution[0].name
  policy_arn = aws_iam_policy.execution[0].arn
}
