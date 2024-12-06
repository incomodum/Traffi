import polars as pl

bar = pl.read_json('./invipo/data/traffic-controllers_bardiagram.json')
filtered_df = (
    bar
    .with_columns(pl.col("timestamp").struct.field("$date").alias("timestamp"))  # Extract $date field
    .with_columns(pl.col("timestamp").str.slice(11, 8).alias("time"))  # Extract the time part (HH:MM:SS)
    .filter((pl.col("time") >= "07:00:00") & (pl.col("time") <= "07:05:00"))  # Filter rows by time range
    .with_columns(pl.col("_id").struct.field("$oid").alias("id"))
    .with_columns(pl.col("itemId").struct.field("$oid").alias("itemId"))
    .drop(pl.col("_id"))
)

filtered_df.write_json("./data.json")