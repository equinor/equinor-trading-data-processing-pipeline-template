from src.process import run
from sklearn import datasets
import pandas as pd


def test_process() -> None:
    data = datasets.load_iris()
    df = pd.DataFrame(data=data.data, columns=data.feature_names)
    assert "test" in run({"iris": df})["iris_data_processing_pipeline_template"].columns
