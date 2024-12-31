import dagster as dg
from . import jobs

goodreads_pinecone_schedule = dg.ScheduleDefinition(
    name="pinecone_schedule",
    target=jobs.goodreads_pinecone,
    cron_schedule="0 12 * * *",
)
