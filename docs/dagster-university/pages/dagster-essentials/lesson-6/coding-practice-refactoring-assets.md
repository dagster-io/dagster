---
title: "Lesson 6: Practice: Refactoring assets to use resources"
module: "dagster_essentials"
lesson: "6"
---

# Practice: Refactoring assets to use resources

The `taxi_zones`, `manhattan_stats`, and `trips_by_week` assets also use the DuckDB database. Update these assets to use the `DuckDBResource`.  

---

## Check your work

The refactored assets should look similar to the code contained in the **View answer** toggle. Click to open it.

We’ll assume your code looks like the following for the rest of the module. If your solution and the code provided have differences, update your code to match the answers and re-materialize these assets to prepare for the next part of this lesson.

- **In `assets/trips.py`:**
    - **Asset**: `taxi_zones`:
        
        ```python
        # assets/trips.py
        
        @asset(
           deps=["taxi_zones_file"],
        )
        def taxi_zones(database: DuckDBResource):
          """
            The raw taxi zones dataset, loaded into a DuckDB database.
          """
      
          query = f"""
            create or replace table zones as (
              select
                LocationID as zone_id,
                zone,
                borough,
                the_geom as geometry
              from '{constants.TAXI_ZONES_FILE_PATH}'
            );
          """
      
          with database.get_connection() as conn:
              conn.execute(query)
        ```
        
    
- **In `assets/metrics.py`:**
    - **Imports:**

      Update the imports in `assets/metrics.py` to the following:

      ```python
      import requests 
      from dagster_duckdb import DuckDBResource 
      from . import constants 
      from dagster import asset
      ```

    - **Asset**: `manhattan_stats`:
        
        ```python
        # assets/metrics.py
        
        @asset(
            deps=["taxi_trips", "taxi_zones"]
        )
        def manhattan_stats(database: DuckDBResource):
          """
            Metrics on taxi trips in Manhattan
          """
      
          query = """
            select
              zones.zone,
              zones.borough,
              zones.geometry,
              count(1) as num_trips,
            from trips
            left join zones on trips.pickup_zone_id = zones.zone_id
            where geometry is not null
            group by zone, borough, geometry
          """
      
          with database.get_connection() as conn:
            trips_by_zone = conn.execute(query).fetch_df()
      
          trips_by_zone["geometry"] = gpd.GeoSeries.from_wkt(trips_by_zone["geometry"])
          trips_by_zone = gpd.GeoDataFrame(trips_by_zone)
      
          with open(constants.MANHATTAN_STATS_FILE_PATH, 'w') as output_file:
            output_file.write(trips_by_zone.to_json())
        ```
        
    - **Asset**: `trips_by_week`:
        
        ```python
        # assets/metrics.py
        
        @asset(
        	deps = ["taxi_trips"]
        )
        def trips_by_week(database: DuckDBResource):
            
          current_date = datetime.strptime("2023-01-01", constants.DATE_FORMAT)
          end_date = datetime.now()
      
          result = pd.DataFrame()
      
          while current_date < end_date:
            current_date_str = current_date.strftime(constants.DATE_FORMAT)
            query = f"""
              select
                vendor_id, total_amount, trip_distance, passenger_count
              from trips
              where pickup_datetime >= '{current_date_str}' and pickup_datetime < '{current_date_str}'::date + interval '1 week'
            """

    				with database.get_connection() as conn:
  		        data_for_week = conn.execute(query).fetch_df()
    
            aggregate = data_for_week.agg({
              "vendor_id": "count",
              "total_amount": "sum",
              "trip_distance": "sum",
              "passenger_count": "sum"
            }).rename({"vendor_id": "num_trips"}).to_frame().T # type: ignore
    
            aggregate["period"] = current_date
    
            result = pd.concat([result, aggregate])
    
            current_date += timedelta(days=7)
          
          # clean up the formatting of the dataframe
          result['num_trips'] = result['num_trips'].astype(int)
          result['passenger_count'] = result['passenger_count'].astype(int)
          result['total_amount'] = result['total_amount'].round(2).astype(float)
          result['trip_distance'] = result['trip_distance'].round(2).astype(float)
          result = result[["period", "num_trips", "total_amount", "trip_distance", "passenger_count"]]
          result = result.sort_values(by="period")
      
          result.to_csv(constants.TRIPS_BY_WEEK_FILE_PATH, index=False)
        ```

**If there are differences**, compare what you wrote to the answer code and make updates, as these assets will be used as-is in future lessons.