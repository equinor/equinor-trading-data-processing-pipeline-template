# %%
from azureml.core import Workspace, Datastore, Experiment, datastore
from azureml.core import Dataset
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.experiment import Experiment
from azureml.data import OutputFileDatasetConfig
from azureml.data.datapath import DataPath
from azureml.core.runconfig import RunConfiguration
from azureml.core import Environment
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline, PipelineData

from src.models.Config import Config

config = Config.parse_file("config.json")

# %%
ws = Workspace.from_config()

# %%
if config.compute_name in ws.compute_targets:
    compute_target = ws.compute_targets[config.compute_name]
    if compute_target and type(compute_target) is AmlCompute:
        print('Found compute target: ' + config.compute_name)
    else:
        raise Exception("Compute does not exist")
else:
    raise Exception("Compute does not exist")

# %%
aml_run_config = RunConfiguration()
aml_run_config.target = compute_target
environment = Environment(name=config.environment)
environment.docker.base_image = None
environment.docker.base_dockerfile = config.dockerfile
environment.python.user_managed_dependencies=True
aml_run_config.environment = environment


# %%
input_datastore = Datastore(ws, config.pipeline.output_datastore.name)
output_datastore = Datastore(ws, config.pipeline.output_datastore.name)

# %%
# dataset = PipelineData(config.pipeline.input_dataset.dataset_name, datastore=input_datastore)
# dataset = Dataset.get_by_name(ws, name=config.pipeline.input_dataset.dataset_name)
# dataset = Dataset.Tabular.from_parquet_files([DataPath(datastore, '/iris.parquet')])


# %%
output = OutputFileDatasetConfig(
    destination=(output_datastore, config.pipeline.output_datastore.path)
).read_parquet_files().register_on_complete(name=config.pipeline.output_dataset.dataset_name)

# %%
data_prep_step = PythonScriptStep(
    script_name=config.pipeline.script_name,
    source_directory=config.pipeline.source_directory,
    arguments=["--output", output],
    outputs=[output],
    compute_target=compute_target,
    runconfig=aml_run_config,
    allow_reuse=True
)


# %%
pipeline = Pipeline(
    workspace=ws,
    description=config.pipeline.pipeline_description,
    steps=[data_prep_step]
)

pipeline.validate()

# %%
pipeline_run = Experiment(ws, config.pipeline.experiment_name).submit(pipeline)
pipeline_run.wait_for_completion()
# %%
