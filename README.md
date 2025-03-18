# What is pyopenet?
PyOpenET is a python library for the OpenET API to ease the process of gathering data from OpenET. The flexibility of this library allows for small tasks to run safely, and this extends to massive jobs that span multiple years of data.

# What is OpenET?
OpenET's slogan is "filling the biggest data gap in water management". Their mission goal is to securely deliver ET and groundwater data using an ensemble of well-established methods in a timely manner.

The documentation for the OpenET API can be found [here](https://etdata.org/api-info/)

# Main Features
## ETRequest
The request module retrieves data from OpenET and performs output validation and timeout handling.

## ETJob
### RasterTimeseries
An implementation of the raster timeseries endpoint for point and polygon inputs. Inputs are structured in a RasterConfigSequence which allows the possibility of having a combination of inputs.

# Installation

With pip
```bash
pip install pyopenet
```
With uv
```bash
uv add pyopenet
```

# Usage
> Currently, only RasterTimeseries is supported. A dedicated documentation page will be made when more features are implemented.

Field input data from OpenET is typically structured as a table containing three columns: field ID, USGS cropland ID, and a JSON string containing the geometric feature.

```py
df = pd.read_csv("PATH/TO/INPUT.csv")
```
| OPENET_ID | CROP_2023 | .geo |
|-----------|-----------|------|
|CA_832174  | 63        | "{""type"": "Point", ""coordinates"": [98.819628, -192.0912796]}"

\
If using input data in this format, the `.geo` column will cause problems since it will be interpreted as a string. The `pyopenet.ETUtil` module has a function `parse_geo` that will convert this column.
```py
df['.geo'] = parse_geo(df['.geo'])
```
| OPENET_ID | CROP_2023 | .geo |
|-----------|-----------|------|
|CA_832174  | 63        | {"type": "Point", "coordinates": [98.819628, -192.0912796]}

Now, the `.geo` column has values that are dicts instead of strings.

A job can be created from this DataFrame.
```py
config = RasterConfigSequence(
    interval="monthly",
    model=["ensemble", "geesebal"],
    reference_et="cimis",
    variable=["eto", "et"],
    file_format="json",
    units="mm"
)
```

`RasterConfigSequence` will generate combinations of query parameters from what was provided. 

The output DataFrame inherits the index from the input. So to pass the field and crop IDs into the output, set those columns as an index. 
```py
df = df.set_index(["OPENET_ID", "CROP_2023"])
```
Optionally, you can set this when you run the job, but currently this only supports one index.
```py
job = ETJob.RasterTimeseries(
    options=config,
    api_key="YOUR_OPENET_API_KEY",
    table=df,   # <-- Your input data to iterate through.
    geometry=".geo", # <-- Geometry column containing values of geometry features
    index="OPENET_ID" # <-- Overwrites input data's index
)

job.run("2016-01-01", "2024-12-31") # <-- Collect data within this date range.
```
|OPENET_ID|CROP_2023|date|model|variable|overpass|reference_et|units|value|
|---------|---------|----|-----|--------|--------|------------|-----|-----|
|CA_0|47|2023-06-01|ensemble|et|False|cimis|mm|0.12|
|CA_1|62|2023-06-01|ensemble|et|False|cimis|mm|0.15|
|CA_2|47|2023-06-01|ensemble|et|False|cimis|mm|0.13|
> This output is not reflective of the inputs. This is just an example.

This output dataframe can be exported through the builtin
```py
job.export("PATH/TO/EXPORT.csv")
```
The output can be accessed directly for more control
```py
job.get_table().to_csv("PATH/TO/EXPORT.csv")
```