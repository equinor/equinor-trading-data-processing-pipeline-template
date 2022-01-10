from typing import List
from pydantic import BaseModel

class OutputDatasetConfig(BaseModel):
    dataset_name: str
    file_name: str
    path: str

class OutputDatastore(BaseModel):
    name: str
    path: str

class Pipeline(BaseModel):
    pipeline_description: str
    experiment_name: str
    input_datastore: str
    output_datastore: OutputDatastore
    script_name: str
    source_directory: str
    input_dataset: List[str]
    output_dataset: OutputDatasetConfig


class Config(BaseModel):
    compute_name: str
    pipeline: Pipeline
    environment: str
    dockerfile: str