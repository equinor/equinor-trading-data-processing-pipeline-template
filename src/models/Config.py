from typing import List, Union
from pydantic import BaseModel

class OutputDatastore(BaseModel):
    name: str                           # Name of the datastore (blob storage) that you want to output files to
    path: str                           # Path to where files should be stored on datastore

class TriggerConfig(BaseModel):
    type: str                           # Choose whether to run pipeline on a schedule or file change, options: schedule or change
    trigger_name: str                   # Name of the trigger
    description: str                    # Description of the trigger
    frequency: str                      # Frequency of a schedule, options: Minute", "Hour", "Day", "Week", or "Month"
    interval: int                       # Interval number for a schedule
    polling_interval: int               # Polling interval in minutes for a change trigger
    change_file_path: str               # File to watch for changes when a change trigger is running

class PipelineConfig(BaseModel):
    pipeline_description: str           # Description of pipeline
    experiment_name: str                # Name of experiment
    output_datastore: OutputDatastore
    script_name: str                    # Name of processing script that the pipeline should run
    source_directory: str               # Directory that will be uploaded and available to pipeline scripts
    input_datasets: List[str]           # Names of input datasets registered in default workspace
    pip_packages: List[str]             # Names of pip packages that will be installed when running the pipeline

class EndpointConfig(BaseModel):
    name: str                           # Name of the deployed pipeline endpoint
    description: str                    # Description of the deployed pipeline endpoint
    version: str                        # Version of the deployed pipeline endpoint

class Config(BaseModel):
    compute_name: str                   # Name of existing compute instance
    pipeline: PipelineConfig
    environment_name: str               # Name of environment
    data_factory_compute_name: str      # Name of new or existing ADF compute instance
    trigger: TriggerConfig
    endpoint: EndpointConfig