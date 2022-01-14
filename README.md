# Equinor Trading data processing pipeline template

This repository is a template for processing data on a time schedule/change trigger using Azure Machine Learning pipelines.
The pipeline takes an input dataset from the AML workspace and passes it to a Python script step that processes this data.
Following this, a Data Factory job moves the output data from the script to a blob storage defined in `config.json`.

Contents:
```
pipeline.py     - Contains code for setting up the pipeline. In general it's not necessary to edit this file.
aml_wrapper.py  - Wrapper code for the Python script step. In general it's not necessary to edit this file.
process.py      - Python script that will run when the pipeline runs. Edit this file to change how the data is processed.
config.json     - JSON file containing the configuration of the pipeline attributes.
Config.py       - Definition of the config.json values.
```

### How to use

1. Install Poetry package manager
2. Run `poetry install`
3. Configure `config.json` to your liking
4. Run `poetry run python pipeline.py` to create, deploy and schedule the pipeline
5. Done!

Some additional things to be aware of:
- You need to register the output blob storage in Azure ML if it's an external blob storage
- Register the blob storage using managed identity, not SAS/access key
- If your output goes back to the default workspace blob storage, this might not be necessary (not yet tested)
- You need to give the Azure Data Factory compute the role `Blob Storage Data Contributer` role in the blob storage resource before it can save to the blob storage