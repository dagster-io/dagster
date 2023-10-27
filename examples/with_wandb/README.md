# Using Dagster with Weights & Biases Examples

This directory contains examples showcasing the integration with Weights & Biases (W&B).

For a complete set of documentation, see [Dagster integration](https://docs.wandb.ai/guides/integrations/dagster) on the W&B website.

## Getting started

Bootstrap your own Dagster project with this example:

```bash
dagster project from-example --name my-dagster-project --example with_wandb
```

To install this example and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

Once you've done this, you can run:

```
dagster-webserver
```

## Set up wandb

To communicate with the W&B servers you need an API Key.

1. [Log in](https://wandb.ai/login) to W&B. Note: if you are using W&B Server ask your admin for the host name.
2. Collect you API Key by navigating to the [authorize page](https://wandb.ai/authorize) or in your user settings.
3. Set an environment variable with that API key `export WANDB_API_KEY=YOUR_KEY`.
4. Set an environment variable with your W&B entity `export WANDB_ENTITY=john_doe`.
5. Set an environment variable with your W&B project `export WANDB_PROJECT=my_project`.
