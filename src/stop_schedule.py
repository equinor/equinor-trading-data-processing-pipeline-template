# %%
from azureml.core import Workspace
from azureml.pipeline.core import Schedule

ws = Workspace.from_config()

ss = Schedule.list(ws)
for s in ss:
    print(s)


# %%
def stop_by_schedule_id(ws, schedule_id):
    s = next(s for s in Schedule.list(ws) if s.id == schedule_id)
    s.disable()
    return s

stop_by_schedule_id(ws, "PIPELINE_ID")
# %%
