# Data Ingestion Patterns - Dagster Example Project

A Dagster project demonstrating three fundamental data ingestion patterns: **Push**, **Pull**, and **Poll**.

## Project Structure

```
ingestion-patterns/
├── src/ingestion_patterns/           # Main Python package
│   ├── definitions.py                # Autoloading definitions with Definitions.merge
│   ├── defs/                         # Assets, jobs, sensors, schedules
│   │   ├── jobs.py                   # Jobs, schedules, and sensors
│   │   ├── push_webhook_ingestion.py # Push pattern (webhooks)
│   │   ├── pull_api_ingestion.py     # Pull pattern (scheduled API)
│   │   └── poll_kafka_ingestion.py   # Poll pattern (Kafka)
│   └── resources/
│       └── mock_apis.py              # Mock API clients and webhook storage
├── scripts/
│   ├── kafka_producer.py             # Produce events to Kafka
│   ├── webhook_server.py             # Flask webhook receiver server
│   └── webhook_simulator.py          # Simulate webhooks (in-memory)
├── tests/
│   ├── test_definitions.py           # Definition loading tests
│   └── test_assets.py                # Asset materialization tests
├── docker-compose.yml                # Kafka + Kafka UI
└── pyproject.toml                    # Project configuration
```

## Quick Start

### 1. Install Dependencies

```bash
cd examples/ingestion-patterns

# Install with uv (recommended)
uv sync --all-groups

# Or install manually
uv pip install -e .
```

### 2. Start Dagster

```bash
dg dev
```

Open http://localhost:3000 to view the Dagster UI.

### 3. Materialize Assets

In the Dagster UI:

1. Navigate to the **Assets** page
2. Select assets to materialize
3. Click **Materialize** to run

## Ingestion Patterns

### Push Pattern (Webhooks)

External systems push data to your platform via webhooks.

**Asset:** `process_webhook_data`
**Sensor:** `webhook_pending_sensor` (checks for pending payloads every 10s)

#### Demo: Simulate Webhooks

**Option A: Use the simulator script (in-memory)**

```bash
python scripts/webhook_simulator.py --count 10
```

Then materialize `process_webhook_data` in the Dagster UI.

**Option B: Run the webhook server**

```bash
# Terminal 1: Start the webhook server
python scripts/webhook_server.py

# Terminal 2: Send webhooks via curl
curl -X POST http://localhost:5050/webhook/my-source \
  -H "Content-Type: application/json" \
  -d '{"id": "event-001", "data": {"type": "order", "amount": 99.99}}'

# Check pending payloads
curl http://localhost:5050/webhook/my-source/pending
```

### Pull Pattern (Scheduled API)

Your platform initiates data extraction from source systems on a schedule.

**Assets:**

- `extract_source_data` - Pulls data from API with incremental checkpointing
- `load_to_storage` - Loads data to DuckDB

**Asset Check:** `validate_extracted_data` - Validates data quality

**Schedule:** `daily_pull_schedule` (runs daily at midnight)

#### Demo: Pull Data

1. In Dagster UI, materialize `extract_source_data`
2. The asset check `validate_extracted_data` runs automatically
3. Materialize `load_to_storage` to complete the pipeline

### Poll Pattern (Kafka)

Continuously poll event streams for new data.

**Assets:**

- `poll_kafka_events` - Polls Kafka topic for new events
- `process_kafka_events` - Processes and stores events in DuckDB

**Sensor:** `kafka_polling_sensor` (triggers every 60s)

#### Demo: Poll Kafka Events

**Step 1: Start Kafka**

```bash
docker compose up -d
```

Wait for Kafka to be healthy (check with `docker compose ps`).

**Step 2: Install Kafka dependencies**

```bash
uv pip install -e ".[kafka]"
```

**Step 3: Produce sample events**

```bash
python scripts/kafka_producer.py --count 20
```

**Step 4: Materialize in Dagster**

In the Dagster UI, materialize `poll_kafka_events` with config:

```yaml
bootstrap_servers: "localhost:9094"
kafka_topic: "transactions"
```

Or leave `bootstrap_servers` empty to use the mock consumer.

**Step 5: View Kafka UI**

Open http://localhost:8080 to monitor topics and messages.

**Step 6: Stop Kafka**

```bash
docker compose down      # Stop containers
docker compose down -v   # Stop and remove data
```

## Running Tests

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_definitions.py -v
```

## Data Storage

All patterns store data in DuckDB (`ingestion_patterns.duckdb`). Tables created:

| Pattern | Table                                           |
| ------- | ----------------------------------------------- |
| Push    | `ingestion.webhook_data`                        |
| Pull    | `ingestion.raw_extract`, `ingestion.final_data` |
| Poll    | `ingestion.kafka_events`                        |

Query the data:

```bash
python -c "import duckdb; conn = duckdb.connect('ingestion_patterns.duckdb'); print(conn.execute('SHOW TABLES').fetchall())"
```

## Configuration

### Kafka Producer Options

```bash
python scripts/kafka_producer.py \
  --count 50 \
  --interval 1.0 \
  --topic my-events \
  --bootstrap-servers localhost:9094
```

### Webhook Server Options

```bash
python scripts/webhook_server.py \
  --port 5050 \
  --host 0.0.0.0
```

### Asset Configuration

Assets can be configured at runtime in the Dagster UI:

**poll_kafka_events:**

- `bootstrap_servers`: Kafka servers (empty = mock)
- `kafka_topic`: Topic name (default: `transactions`)
- `max_records_per_poll`: Max messages per poll (default: 100)

**process_webhook_data:**

- `source_id`: Filter by source (default: `default`)
- `validate_schema`: Enable schema validation (default: true)

## Project Files

| File                                            | Description                                                |
| ----------------------------------------------- | ---------------------------------------------------------- |
| `src/ingestion_patterns/definitions.py`         | Main definitions using `Definitions.merge` and `load_defs` |
| `src/ingestion_patterns/defs/jobs.py`           | Jobs, schedules, and sensors                               |
| `src/ingestion_patterns/resources/mock_apis.py` | Mock API client, Kafka consumer, webhook storage           |
| `scripts/kafka_producer.py`                     | Produces events to real Kafka                              |
| `scripts/webhook_server.py`                     | Flask server that receives webhooks                        |
| `scripts/webhook_simulator.py`                  | Simulates webhooks to in-memory storage                    |

## Key Concepts Demonstrated

- **Autoloading definitions** with `dg.components.load_defs()`
- **Merging definitions** with `dg.Definitions.merge()`
- **Asset checks** for data quality validation
- **Sensors** for event-driven triggering
- **Schedules** for time-based execution
- **DuckDB resource** for data storage
- **Incremental processing** with materialization metadata
