"""Mock API server for data platform architecture examples."""

import json
import random
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock Data API")


def generate_clickstream_data(limit: int = 500) -> list[dict]:
    """Generate mock clickstream data."""
    base_time = datetime.now()
    data = []
    for i in range(limit):
        data.append(
            {
                "event_id": f"event-{i:04d}",
                "user_id": f"user-{i % 100:03d}",
                "page_url": f"https://example.com/page-{i % 20}",
                "timestamp": (base_time - timedelta(minutes=limit - i)).isoformat(),
                "event_type": ["page_view", "click", "purchase"][i % 3],
                "session_id": f"session-{i % 50:03d}",
                "metadata": json.dumps({"device": "mobile", "browser": "chrome"}),
            }
        )
    return data


def generate_events_data(limit: int = 1000) -> list[dict]:
    """Generate mock events data."""
    base_time = datetime.now()
    event_types = ["user_signup", "purchase", "page_view", "click", "logout"]
    return [
        {
            "id": f"evt-{i:06d}",
            "type": random.choice(event_types),
            "user_id": f"user-{random.randint(1, 1000):04d}",
            "timestamp": (base_time - timedelta(seconds=random.randint(0, 86400))).isoformat(),
            "properties": {"source": random.choice(["web", "mobile", "api"])},
        }
        for i in range(limit)
    ]


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/clickstream")
def get_clickstream(
    limit: int = Query(default=500, le=10000),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get clickstream events."""
    data = generate_clickstream_data(limit)
    return JSONResponse(content={"data": data, "count": len(data)})


@app.get("/data/events")
def get_events(
    limit: int = Query(default=1000, le=10000),
):
    """Get events data."""
    data = generate_events_data(limit)
    return JSONResponse(content={"data": data, "count": len(data)})


@app.get("/sensors")
def get_sensor_data(
    limit: int = Query(default=1000, le=10000),
):
    """Get IoT sensor data."""
    base_time = datetime.now()
    data = [
        {
            "sensor_id": f"sensor-{i % 50:03d}",
            "timestamp": (base_time - timedelta(minutes=limit - i)).isoformat(),
            "temperature": round(20.0 + (i % 30) * 0.5, 2),
            "humidity": round(50.0 + (i % 40) * 0.3, 2),
            "region": ["North", "South", "East", "West"][i % 4],
        }
        for i in range(limit)
    ]
    return JSONResponse(content={"data": data, "count": len(data)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
