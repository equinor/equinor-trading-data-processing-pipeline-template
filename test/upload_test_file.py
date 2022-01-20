# %%
from azureml.core import Workspace, Datastore

ws = Workspace.from_config()

ds = ws.get_default_datastore()

ds.upload_files(["test.txt"], target_path="test-data", overwrite=True)

# %%
