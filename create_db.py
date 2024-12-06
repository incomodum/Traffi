import polars as pl
from rich import print
import json

import sqlite3

with sqlite3.connect("./database.db") as db:
    str

decoder = json.decoder.JSONDecoder()

data = pl.read_json("./data.json")

id_column = "itemId"
json_column = "detectorsState"
plan_column = "plan"
signals = "signalGroupsState"

travel_to_controllers = {
    "6544f37c6290fa000100b478": "654e207e6290fa00011230ac",
    "6544f3586290fa000100b458": "654e207e6290fa00011230b2",
    "6544f3376290fa000100b43c": "654e207e6290fa00011230b0",
    "6544f8aa6290fa000100be6f": "654e207e6290fa00011230b4", # Hospodárska - Kollárová
    "6544f88d6290fa000100be50": "654e207e6290fa00011230b8",
    "6544f8726290fa000100be3d": "654e207e6290fa00011230ba", # Hospodárska - Študentská
    "6544f79e6290fa000100bd80": "654e207e6290fa00011230b6",
    "6544f7b56290fa000100bd96": "654e207e6290fa00011230c0",
    "6544f91e6290fa000100c13c": "654e207e6290fa00011230ae",
    "6544f99f6290fa000100c1b4": "654e207d6290fa00011230aa",
    "6544f2be6290fa000100b3d6": "654e207e6290fa00011230bc",
    "6544f6196290fa000100b972": "654e207e6290fa00011230be"
}

counter_to_controllers = {
    # "6544b8556290fa0001000271": "654e207e6290fa00011230ac",
    # "6544b8556290fa0001000281": "654e207e6290fa00011230ac",
    # "6544b8556290fa0001000275": "654e207e6290fa00011230ac",
    # "6544b8556290fa0001000279": "654e207e6290fa00011230ac",
    # "6565b787d8d78d00013c4fcf": "654e207e6290fa00011230b8",
    "6565b761d8d78d00013c4d6f": "654e207e6290fa00011230ba", # Hospodárska - Študentská
    "656eed1a01033a000144164b": "654e207e6290fa00011230b4" # Hospodárska - Kollárová
}

def travelToControl(x: str):
    try:
        return travel_to_controllers[x]
    except KeyError:
        return

def counterToControl(x: str):
    try:
        return counter_to_controllers[x]
    except KeyError:
        return

detectors = (
    data
    .select([id_column, json_column, "timestamp"])
    .explode(json_column)
    .unnest(json_column)
    .with_columns(pl.col("occupancies").list.first().struct.field("occupied").alias("active"))
    .with_columns(pl.col("active").fill_null(False))
    .drop(pl.col("occupancies"), pl.col("no"))
)

signals = (
    data
    .select([id_column, "timestamp", signals])
    .explode(signals)
    .unnest(signals)
    .drop("no")
)

plans = (
    data.select([plan_column]).unnest(plan_column).unique(pl.col("id"))
)

data = (
    data
    .drop(pl.col("controllerOperatingState"), pl.col("time"), pl.col("id"))
    .with_columns(pl.col("plan").struct.field("id").alias("planId"))
    .drop(pl.col(json_column), pl.col(plan_column), pl.col("signalGroupsState"))
)

print(data)
print(detectors)
print(signals)
print(plans)
data.write_database(table_name="controllers", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")
detectors.write_database(table_name="detectors", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")
plans.write_database(table_name="plans", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")
signals.write_database(table_name="signals", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")

traveltime = pl.read_json("./data/traveltime.json")
traveltime = (
    traveltime
    .drop("_id")
    .with_columns(pl.col("route").struct.field("from").struct.field("$oid").map_elements(travelToControl, pl.String()).alias(id_column))
    .with_columns(pl.col("route").struct.field("to").struct.field("$oid").map_elements(travelToControl, pl.String()).alias("routeTo"))
    .with_columns(pl.col("interval").struct.field("from").struct.field("$date").alias("startTime"))
    .with_columns(pl.col("interval").struct.field("to").struct.field("$date").alias("endTime"))
    .with_columns(pl.col("startTime").str.slice(11, 8).alias("startTimeTime"))
    .filter((pl.col("startTimeTime") >= "07:00:00") & (pl.col("startTimeTime") <= "07:05:00"))
    .with_columns(pl.col("endTime").str.slice(11, 8).alias("endTimeTime"))
    .filter((pl.col("endTimeTime") >= "07:00:00") & (pl.col("endTimeTime") <= "07:05:00"))
    .drop("calculation", "route", "trafficLevel", "interval", "startTimeTime", "endTimeTime")
    .drop_nulls()
)

print(traveltime)
traveltime.write_database(table_name="traveltime", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")

counter = pl.read_json("./data/traffic-counters_volumes.json")
counter = (
    counter
    .drop("_id", "level", "from", "to", "volumes", "averageLength", "averageGap")
    .with_columns(pl.col("itemId").struct.field("$oid").alias("itemId"))
    .with_columns(pl.col("itemId").map_elements(counterToControl, pl.String()).alias("controllerId"))
    .sort(pl.col("timestamp"))
    .with_columns(pl.col("timestamp").str.slice(11, 8).alias("time"))
    .filter((pl.col("time") >= "07:00:00") & (pl.col("time") <= "07:30:00"))
    .drop("time")
    .drop_nulls()
)

print(counter)
counter.write_database(table_name="counters", connection="sqlite://./database.db", if_table_exists="replace", engine="adbc")
