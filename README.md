# DSS_CMR

This repository is organized for a notebook-first development workflow for the BVC portfolio decision support system.

## Structure

- notebooks/: Jupyter notebooks for each pipeline stage
- data/: raw and processed data files
- src/: reserved for future Python module migration after notebook validation

## Workflow

1. Prototype each stage in a dedicated notebook.
2. Validate the logic.
3. Migrate the validated logic into reusable Python modules under src/.
