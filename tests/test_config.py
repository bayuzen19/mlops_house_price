import pytest

from house_price.config import TrainingConfig, load_config


@pytest.mark.parametrize(
    "options",
    [
        {"test_size": 0},
        {"test_size": 1},
        {"cv": 1},
        {"n_jobs": 0},
        {"param_grid": {}},
        {"param_grid": {"unsupported": [1]}},
        {"param_grid": {"n_estimators": []}},
    ],
)
def test_bad_configuration_fails_early(options):
    with pytest.raises(ValueError):
        TrainingConfig(**options)


def test_load_config(tmp_path):
    path = tmp_path / "params.yaml"
    path.write_text("training:\n  cv: 2\nmlflow:\n  experiment_name: example\n")
    config = load_config(path)
    assert config.cv == 2
    assert config.experiment_name == "example"
