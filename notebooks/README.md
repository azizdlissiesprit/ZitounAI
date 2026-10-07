# Notebooks

One folder per module. Training runs on Google Colab or Kaggle (free GPU) when needed: mount the shared Drive and keep the same relative paths (`data/`, `models/`).

Experiment tracking (MLflow, owned by M3): log params, metrics and the baseline for every run, so the final comparison table (baseline vs final model, per module) can be built from MLflow. `mlruns/` is git-ignored.
