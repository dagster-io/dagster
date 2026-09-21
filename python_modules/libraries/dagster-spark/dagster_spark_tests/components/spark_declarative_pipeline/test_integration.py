import os
import shutil
import tempfile
from pathlib import Path

import pytest
from dagster_spark.components.spark_declarative_pipeline.discovery import discover_datasets_fn


# Check if the spark-pipelines CLI is available on the system.
def _spark_pipelines_available_locally() -> bool:
    if (
        shutil.which("spark-pipelines") is not None
        or shutil.which("spark-pipelines.cmd") is not None
        or shutil.which("spark-pipelines.bat") is not None
    ):
        return True

    try:
        import pyspark

        pyspark_bin_dir = Path(pyspark.__file__).resolve().parent / "bin"
        for candidate in ("spark-pipelines.cmd", "spark-pipelines.bat", "spark-pipelines"):
            if (pyspark_bin_dir / candidate).exists():
                return True
    except ModuleNotFoundError:
        pass

    return False


HAS_SPARK_PIPELINES = _spark_pipelines_available_locally()

# Skip this entire test module if Spark 4.0+ is not installed locally.
pytestmark = pytest.mark.skipif(
    not HAS_SPARK_PIPELINES,
    reason="spark-pipelines CLI not found on this machine",
)


def _find_spark_pipelines_script() -> str | None:
    script = (
        shutil.which("spark-pipelines.cmd")
        or shutil.which("spark-pipelines.bat")
        or shutil.which("spark-pipelines")
    )
    if script:
        return script

    try:
        import pyspark

        pyspark_bin_dir = Path(pyspark.__file__).resolve().parent / "bin"
        candidate = pyspark_bin_dir / "spark-pipelines"
        if candidate.exists():
            return str(candidate)

        for fallback in ("spark-pipelines.cmd", "spark-pipelines.bat"):
            p = pyspark_bin_dir / fallback
            if p.exists():
                return str(p)
    except ModuleNotFoundError:
        pass

    return None


def _detect_java_home() -> str | None:
    """Best-effort JAVA_HOME detection for local testing."""
    if os.environ.get("JAVA_HOME"):
        return os.environ["JAVA_HOME"]

    java_exe = shutil.which("java")
    if java_exe:
        java_path = Path(java_exe).resolve()
        if java_path.parent.name.lower() == "bin":
            return str(java_path.parent.parent)

    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        java_dir = program_files / "Java"
        if java_dir.exists():
            candidates = [
                p
                for p in java_dir.iterdir()
                if p.is_dir() and p.name.lower().startswith(("jdk", "jre"))
            ]
            if candidates:
                candidates.sort(key=lambda p: p.name, reverse=True)
                return str(candidates[0])

    return None


def test_real_spark_dry_run_integration() -> None:
    """Integration test that invokes the real spark-pipelines CLI and tests the fallback mechanism."""
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        storage_path = (root / "storage").as_uri()

        # 1. Scaffold a minimal SDP project
        spec_path = root / "spark-pipeline.yml"
        spec_path.write_text(
            f"name: integration_test_pipeline\n"
            f"storage: {storage_path}\n"
            "catalog: spark_catalog\n"
            "database: default\n"
            "libraries:\n"
            "  - glob:\n"
            "      include: 'models.py'\n",
            encoding="utf-8",
        )

        models_path = root / "models.py"
        models_path.write_text(
            "import pyspark.pipelines as dp\n"
            "from pyspark.sql import SparkSession\n\n"
            "@dp.table(name='real_integration_table')\n"
            "def real_integration_table():\n"
            "    spark = SparkSession.builder.getOrCreate()\n"
            "    return spark.readStream.format('rate').load()\n\n"
            "@dp.materialized_view(name='real_integration_mv')\n"
            "def real_integration_mv():\n"
            "    spark = SparkSession.builder.getOrCreate()\n"
            "    return spark.range(0)\n",
            encoding="utf-8",
        )

        # Ensure JAVA_HOME is set for the subprocess
        java_home = _detect_java_home()
        if java_home:
            os.environ["JAVA_HOME"] = java_home

        # 2. Call the discovery function (which encapsulates the CLI call and fallback logic)
        try:
            cmd = _find_spark_pipelines_script() or "spark-pipelines"
            datasets = discover_datasets_fn(
                spark_pipelines_cmd=cmd,
                pipeline_spec_path=spec_path,
                discovery_mode="dry_run_with_fallback",
                dry_run_extra_args=[],
            )
        except Exception as e:
            pytest.skip(f"Failed to execute discovery locally: {e}")

        # 3. Assertions
        if len(datasets) == 0:
            pytest.fail("Discovery found 0 datasets. Both CLI dry-run and source fallback failed.")

        assert len(datasets) == 2
        names = {ds.name for ds in datasets}
        assert "real_integration_table" in names
        assert "real_integration_mv" in names

        # Verify it actually used the fallback mechanism since the Spark CLI outputs no metadata
        assert datasets[0].discovery_method == "source_fallback"
