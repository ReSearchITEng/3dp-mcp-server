# 3dp-mcp-server Multi-Agent Guidelines

This file provides guidelines for interacting with `3dp-mcp-server`, focusing on how AI agents can discover skills, select tools, provide parameters, and execute headless/non-interactive workflows.

## Skill Discovery (`skills/`)
The repository contains modular skill folders in `skills/` designed to handle distinct domains of the 3D CAD modeling process:
- `design-model`: Core build123d generative modeling.
- `mechanical-parts`: Mechanical parts generation (screws, gears, bearings).
- `modify-model`: Advanced part modifiers, such as text wrapping or splitting.
- `parametric-components`: Parametric components like boxes and joints.
- `print-prep`: Pre-print verification and preparation.
- `publish-model`: Exporting and uploading to external repos like Thingiverse.

## Tool Selection
- **`create_model`**: Use for initiating design via build123d scripts. Always assign the final shape to a variable named `result`.
- **`export_model`**: Support formats are `.stl`, `.step`, `.3mf`, and `.glb`.
- **`analyze_printability`**: Use to analyze a model for printability against a target `printer_profile` (e.g. `x1c`, `a1_mini`, or `generic`).

## Parameter Definitions
- Always define parametric parameters in `parameters.py` separate from the modeling script in a clean module.
- Provide descriptive variable names for geometry parameters (e.g. `housing_length`, `wall_thickness`).

## Non-Interactive CLI/Python Invocation
- Agents must operate in a non-interactive manner. Generate build scripts directly using `create_model` with `result = ...` rather than prompting the user for manual confirmations within loops.
- Evaluate the state of models using `measure_model` and `analyze_printability` to autonomously iterate.
