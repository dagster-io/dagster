   SELECT FORMAT_DATETIME("%F %H:00:00", DATETIME(TIMESTAMP_SECONDS(CAST(timestamp AS INT64)))) AS ts,
          COUNT(1) AS num_visits
     FROM events.events
    WHERE url = '/explore'
 GROUP BY ts
 ORDER BY ts ASC