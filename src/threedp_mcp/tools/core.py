"""Core tools — create, export, measure, analyze, list, get code."""

import json
import os
import traceback

from threedp_mcp.helpers import run_build123d_code


def register(mcp, models: dict, output_dir: str):
    """Register core tools with the MCP server."""

    @mcp.tool()
    def create_model(name: str, code: str) -> str:
        """Create a 3D model by executing build123d Python code.

        The code MUST assign the final shape to a variable called `result`.
        All build123d imports are available automatically.

        Args:
            name: A short name for the model (used for file naming)
            code: build123d Python code that creates a shape and assigns it to `result`

        Returns:
            JSON with success status, geometry info (bounding box, volume), and output paths.
        """
        try:
            if "from build123d" not in code and "import build123d" not in code:
                code = "from build123d import *\n" + code

            result = run_build123d_code(code)
            models[name] = result

            model_dir = os.path.join(output_dir, name)
            os.makedirs(model_dir, exist_ok=True)

            from build123d import export_step, export_stl

            stl_path = os.path.join(model_dir, f"{name}.stl")
            step_path = os.path.join(model_dir, f"{name}.step")
            export_stl(result["shape"], stl_path)
            export_step(result["shape"], step_path)

            return json.dumps(
                {
                    "success": True,
                    "name": name,
                    "bbox": result["bbox"],
                    "volume": result["volume"],
                    "outputs": {"stl": stl_path, "step": step_path},
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                },
                indent=2,
            )

    @mcp.tool()
    def export_model(name: str, format: str = "stl") -> str:
        """Export a model to STL, STEP, 3MF, or GLB format.

        Args:
            name: Name of a previously created model
            format: Export format - "stl", "step", "3mf", or "glb"
        """
        if name not in models:
            return json.dumps(
                {"success": False, "error": f"Model '{name}' not found. Available: {list(models.keys())}"}
            )

        model = models[name]
        model_dir = os.path.join(output_dir, name)
        os.makedirs(model_dir, exist_ok=True)

        fmt = format.lower().strip(".")
        out_path = os.path.join(model_dir, f"{name}.{fmt}")

        try:
            if fmt == "stl":
                from build123d import export_stl

                export_stl(model["shape"], out_path)
            elif fmt == "step":
                from build123d import export_step

                export_step(model["shape"], out_path)
            elif fmt == "3mf":
                try:
                    from build123d import Mesher

                    with Mesher() as mesher:
                        mesher.add_shape(model["shape"])
                        mesher.write(out_path)
                except Exception as e:
                    # Fallback to trimesh for 3MF export
                    import tempfile
                    import trimesh
                    from build123d import export_stl

                    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_stl:
                        export_stl(model["shape"], tmp_stl.name)
                        mesh = trimesh.load(tmp_stl.name)
                        mesh.export(out_path)
                    os.unlink(tmp_stl.name)
            elif fmt == "glb":
                import tempfile
                import trimesh
                from build123d import export_stl

                with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp_stl:
                    export_stl(model["shape"], tmp_stl.name)
                    mesh = trimesh.load(tmp_stl.name)
                    mesh.export(out_path)
                os.unlink(tmp_stl.name)
            else:
                return json.dumps({"success": False, "error": f"Unsupported format: {fmt}"})

            return json.dumps({"success": True, "path": out_path})

        except Exception as e:
            return json.dumps({"success": False, "error": str(e), "traceback": traceback.format_exc()})

    @mcp.tool()
    def measure_model(name: str) -> str:
        """Measure a model's geometry: bounding box, volume, surface area, and face/edge counts.

        Args:
            name: Name of a previously created model
        """
        if name not in models:
            return json.dumps(
                {"success": False, "error": f"Model '{name}' not found. Available: {list(models.keys())}"}
            )

        shape = models[name]["shape"]
        bb = models[name]["bbox"]
        measurements = {"name": name, "bbox": bb}

        try:
            measurements["volume_mm3"] = round(shape.volume, 3)
        except Exception:
            measurements["volume_mm3"] = None

        try:
            measurements["area_mm2"] = round(shape.area, 3)
        except Exception:
            measurements["area_mm2"] = None

        try:
            measurements["faces"] = len(shape.faces())
        except Exception:
            measurements["faces"] = None

        try:
            measurements["edges"] = len(shape.edges())
        except Exception:
            measurements["edges"] = None

        return json.dumps(measurements, indent=2)

    @mcp.tool()
    def list_models() -> str:
        """List all models currently loaded in this session."""
        if not models:
            return json.dumps({"models": [], "message": "No models yet. Use create_model to make one."})

        return json.dumps(
            {"models": [{"name": n, "bbox": d["bbox"], "volume": d["volume"]} for n, d in models.items()]}, indent=2
        )

    @mcp.tool()
    def get_model_code(name: str) -> str:
        """Retrieve the build123d code used to create a model.

        Args:
            name: Name of a previously created model
        """
        if name not in models:
            return json.dumps(
                {"success": False, "error": f"Model '{name}' not found. Available: {list(models.keys())}"}
            )

        return json.dumps({"name": name, "code": models[name]["code"]})
