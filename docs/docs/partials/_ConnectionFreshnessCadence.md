By default, Dagster polls the source for changes every minute. You can change the cadence in the **Freshness** tab of the connection editor.

Available presets:

- **Every minute** (default)
- **Every 5 minutes**
- **Every 15 minutes**
- **Custom cron** — any standard 5-field cron string (e.g. `0 */2 * * *`)

A timezone selector accompanies the cron, which is useful when you pick a less frequent schedule (for example, "every day at 2 AM in America/New_York"). Slower cadences reduce queries against your source at the cost of longer worst-case detection lag.
