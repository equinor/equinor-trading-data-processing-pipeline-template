# %%
from azureml.core import Workspace, Datastore, Experiment
from azureml.core import Dataset
from azureml.core import experiment
from azureml.core.conda_dependencies import CondaDependencies
from azureml.core.experiment import Experiment
from azureml.core.run import Run
from azureml.core.runconfig import RunConfiguration
from azureml.core import Environment
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline, PipelineData
from azureml.data.data_reference import DataReference
from azureml.pipeline.core.schedule import ScheduleRecurrence, Schedule

from azureml.pipeline.steps import DataTransferStep
from azureml.core.compute import ComputeTarget, DataFactoryCompute
from azureml.exceptions import ComputeTargetException

from src.models.Config import Config

print("Creating pipeline...")

config = Config.parse_file("config.json")
ws = Workspace.from_config()

if config.compute_name in ws.compute_targets:
    compute_target = ws.compute_targets[config.compute_name]
    if compute_target and type(compute_target) is AmlCompute:
        print('Found compute target: ' + config.compute_name)
    else:
        raise Exception("Compute does not exist")
else:
    raise Exception("Compute does not exist")

aml_run_config = RunConfiguration()
aml_run_config.target = compute_target

environment = Environment(name=config.environment_name)
conda_dep = CondaDependencies()
for package in config.pipeline.pip_packages:
    conda_dep.add_pip_package(package)
environment.python.conda_dependencies = conda_dep

aml_run_config.environment = environment

output = PipelineData("datadir", is_directory=True)

data_prep_step = PythonScriptStep(
    script_name=config.pipeline.script_name,
    source_directory=config.pipeline.source_directory,
    arguments=["--output", output],
    inputs=[Dataset.get_by_name(ws, ds_name).as_named_input(ds_name) for ds_name in config.pipeline.input_datasets],
    outputs=[output],
    compute_target=compute_target,
    runconfig=aml_run_config,
    allow_reuse=True
)

try:
    data_factory_compute = DataFactoryCompute(ws, config.data_factory_compute_name)
except ComputeTargetException as e:
    if 'ComputeTargetNotFound' in e.message:
        print('Data factory not found, creating...')
        provisioning_config = DataFactoryCompute.provisioning_configuration()
        data_factory_compute = ComputeTarget.create(ws, config.data_factory_compute_name, provisioning_config)
        data_factory_compute.wait_for_completion()
    else:
        raise e

blob_data_ref = DataReference(
    datastore=Datastore(ws, config.pipeline.output_datastore.name),
    data_reference_name=config.pipeline.output_datastore.name,
    path_on_datastore=""
)

transfer = DataTransferStep(
    name="transfer_output_to_blob",
    source_data_reference=output,
    destination_data_reference=blob_data_ref,
    compute_target=data_factory_compute,
    source_reference_type='directory',
    destination_reference_type='directory',
    allow_reuse=False
)

pipeline = Pipeline(
    workspace=ws,
    description=config.pipeline.pipeline_description,
    steps=[data_prep_step, transfer],
)

print("Validating pipeline...")
pipeline.validate()

print("Submitting run...")
experiment = Experiment(ws, config.pipeline.experiment_name)
pipeline_run: Run = experiment.submit(pipeline)

pipeline_run.wait_for_completion()

# %%
pipeline_run = pipeline.publish(
    name=config.endpoint.name,
    description=config.endpoint.description,
    version=config.endpoint.version
)
print(pipeline_run)

# %%
if config.trigger.type == "schedule":
    recurrence = ScheduleRecurrence(frequency=config.trigger.frequency, interval=config.trigger.interval)
    recurring_schedule = Schedule.create(
        ws,
        name=config.trigger.trigger_name, 
        description=config.trigger.description,
        pipeline_id=pipeline_run.id, 
        experiment_name=experiment.name, 
        recurrence=recurrence
    )
    print(recurring_schedule)
else:
    reactive_schedule = Schedule.create(
        ws,
        name=config.trigger.trigger_name,
        description=config.trigger.description,
        pipeline_id=pipeline_run.id,
        experiment_name=experiment.name,
        polling_interval=config.trigger.polling_interval,
        datastore=Datastore(ws, config.trigger.datastore_name),
        path_on_datastore=config.trigger.change_file_path
    )
    print(reactive_schedule)

# %%
