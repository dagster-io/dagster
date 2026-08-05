"""Decodes PexMetadata to download S3 files locally and setup a runnable PEX environment."""

import hashlib
import logging
import os
import shutil
import subprocess
import threading
from dataclasses import dataclass
from os.path import expanduser
from pathlib import Path
from typing import NamedTuple
from uuid import uuid4

from dagster import _check as check
from dagster_cloud_cli.core.workspace import PexMetadata

DEFAULT_PEX_FILES_DIR = "/tmp/pex-files"
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html
MULTIPART_DOWNLOAD_THREADS = 20  # Double the boto3 default of 10

logger = logging.getLogger("dagster.multipex")


def _download_from_s3(filename: str, local_filepath: str):
    # Lazy import boto3 to avoid a hard dependency during module load
    import boto3
    from boto3.s3.transfer import TransferConfig
    from botocore.config import Config

    config = Config(retries={"max_attempts": 3, "mode": "standard"})

    s3 = boto3.client(
        "s3",
        region_name=os.getenv("DAGSTER_CLOUD_SERVERLESS_REGION", "us-west-2"),
        config=config,
    )

    # TODO: move the bucket and prefix to pex_metdata
    s3_bucket_name = os.environ["DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_BUCKET"]
    # prefix is typically org-storage/{org_public_id}
    s3_prefix = os.environ["DAGSTER_CLOUD_SERVERLESS_STORAGE_S3_PREFIX"]

    s3_key = f"{s3_prefix}/pex/{filename}"
    # write to different file and rename for read safety
    local_tmp_filepath = local_filepath + "-" + str(uuid4())
    s3.download_file(
        Bucket=s3_bucket_name,
        Key=s3_key,
        Filename=local_tmp_filepath,
        Config=TransferConfig(max_concurrency=MULTIPART_DOWNLOAD_THREADS),
    )
    os.rename(local_tmp_filepath, local_filepath)


class PexExecutable(
    NamedTuple(
        "_PexExecutable",
        [
            ("source_path", str),
            ("all_paths", list[str]),
            ("environ", dict[str, str]),
            ("working_directory", str | None),
            ("venv_dirs", list[str]),
        ],
    )
):
    def __new__(
        cls,
        source_path: str,
        all_paths: list[str],
        environ: dict[str, str],
        working_directory: str | None,
        venv_dirs: list[str],
    ):
        return super().__new__(
            cls,
            check.str_param(source_path, "source_path"),
            check.list_param(all_paths, "all_paths", str),
            check.dict_param(environ, "environ", str, str),
            check.opt_str_param(working_directory, "working_directory"),
            check.list_param(venv_dirs, "venv_dirs"),
        )


@dataclass
class PexVenv:
    path: Path
    site_packages: Path
    bin: Path
    entrypoint: Path
    pex_filename: str


class PexInstallationError(Exception):
    pass


class PexS3Registry:
    def __init__(self, local_pex_files_dir: str | None = None):
        self._local_pex_files_dir = (
            local_pex_files_dir if local_pex_files_dir else DEFAULT_PEX_FILES_DIR
        )
        os.makedirs(self._local_pex_files_dir, exist_ok=True)
        self.working_dirs: dict[
            str, str
        ] = {}  # once unpacked, working dirs dont change so we cache them

        # keep track of local files and directories used by each pex tag
        self.local_paths_for_pex_tag: dict[str, set[str]] = {}

        # lock to do safe install and cleanup
        self._install_lock = threading.RLock()

    def get_pex_executable(self, pex_metadata: PexMetadata) -> PexExecutable:
        with self._install_lock:
            return self._get_pex_executable(pex_metadata)

    def _get_pex_executable(self, pex_metadata: PexMetadata) -> PexExecutable:
        if "=" not in pex_metadata.pex_tag:
            raise ValueError(f"Invalid pex tag, no prefix in {pex_metadata.pex_tag!r}")
        prefix, filenames = pex_metadata.pex_tag.split("=", 1)
        if prefix != "files":
            raise ValueError(
                f'Expected pex_tag prefix "files=" not found in tag {pex_metadata.pex_tag!r}'
            )

        pex_filenames = filenames.split(":")
        deps_pex_filepaths = []
        source_pex_filepath = None

        if pex_metadata.pex_tag not in self.local_paths_for_pex_tag:
            self.local_paths_for_pex_tag[pex_metadata.pex_tag] = set()
        local_paths = self.local_paths_for_pex_tag[pex_metadata.pex_tag]

        for filename in pex_filenames:
            local_filepath = os.path.join(self._local_pex_files_dir, filename)
            local_paths.add(local_filepath)

            # no need to download if we already have this file - these
            # files have a content hash suffix so name equality implies content is same
            if not os.path.exists(local_filepath):
                if os.getenv("S3_PEX_DISABLED"):
                    raise ValueError(
                        f"File {local_filepath} not found for pex tag {pex_metadata.pex_tag},"
                        " S3_PEX_DISABLED"
                    )
                _download_from_s3(filename, local_filepath)

            if filename.startswith("source-"):
                source_pex_filepath = local_filepath
                # make it executable
                os.chmod(source_pex_filepath, 0o775)
            else:
                deps_pex_filepaths.append(local_filepath)

        if not source_pex_filepath:
            raise ValueError(f"Invalid pex_tag has no source pex: {pex_metadata.pex_tag!r}")

        # we unpack each pex file into its own venv
        source_venv = self.venv_for(source_pex_filepath)
        local_paths.add(str(source_venv.path.absolute()))

        deps_venvs = []
        for deps_filepath in deps_pex_filepaths:
            deps_venv = self.venv_for(deps_filepath)
            deps_venvs.append(deps_venv)
            local_paths.add(str(deps_venv.path.absolute()))

        entrypoint = str(source_venv.entrypoint)
        pythonpaths = ":".join(
            [str(source_venv.site_packages)]
            + [str(deps_venv.site_packages) for deps_venv in deps_venvs]
        )
        bin_paths = ":".join(
            [str(source_venv.bin)] + [str(deps_venv.bin) for deps_venv in deps_venvs]
        )
        working_dir = self.get_working_dir_for_pex(entrypoint)
        env = {
            "PATH": bin_paths + ":" + os.environ["PATH"],
            "PYTHONPATH": pythonpaths,
        }

        # remove the PEX_ROOT transient cache to keep disk usage in check
        pex_root = os.getenv("PEX_ROOT", expanduser("~/.pex"))
        if pex_root and os.path.exists(pex_root):
            shutil.rmtree(pex_root)

        return PexExecutable(
            entrypoint,
            [source_pex_filepath] + deps_pex_filepaths,
            env,
            working_dir,
            venv_dirs=[str(source_venv.path)] + [str(deps_venv.path) for deps_venv in deps_venvs],
        )

    def cleanup_unused_files(self, in_use_pex_metadatas: list[PexMetadata]) -> None:
        with self._install_lock:
            return self._cleanup_unused_files(in_use_pex_metadatas)

    def _cleanup_unused_files(self, in_use_pex_metadatas: list[PexMetadata]) -> None:
        """Cleans up all local files and directories that are not associated with any PexMetadata provided."""
        in_use_pex_tags = [pex_metadata.pex_tag for pex_metadata in in_use_pex_metadatas]

        all_local_paths = set()
        in_use_local_paths = set()
        for pex_tag, local_paths in self.local_paths_for_pex_tag.items():
            all_local_paths.update(local_paths)

            if pex_tag in in_use_pex_tags:
                in_use_local_paths.update(local_paths)

        unused_local_paths = all_local_paths - in_use_local_paths
        unused_paths_present = [path for path in unused_local_paths if os.path.exists(path)]
        if unused_paths_present:
            logger.info(
                "Cleaning up %s unused local paths: %r",
                len(unused_paths_present),
                unused_paths_present,
            )
            for path in unused_paths_present:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                    else:
                        os.remove(path)
                except OSError:
                    logger.exception("Ignoring failure to clean up local unused path %s", path)

    def venv_for(self, pex_filepath) -> PexVenv:
        _, pex_filename = os.path.split(pex_filepath)
        venv_dir = self.venv_dir_for(pex_filepath)
        if os.path.exists(venv_dir):
            logger.info("Reusing existing venv %r for %r", venv_dir, pex_filepath)
        else:
            self.install_venv(venv_dir, pex_filepath)
            if not os.path.exists(venv_dir):
                raise PexInstallationError("Could not install venv", pex_filepath)
        venv_path = Path(venv_dir).absolute()
        return PexVenv(
            path=venv_path,
            site_packages=self.get_site_packages_dir_for_venv(venv_path),
            bin=venv_path / "bin",
            entrypoint=venv_path / "pex",
            pex_filename=pex_filename,
        )

    def venv_dir_for(self, pex_filepath: str):
        # Use a short name for better stack traces
        short_hash = hashlib.shake_256(pex_filepath.encode("utf-8")).hexdigest(6)
        venv_root = os.getenv("VENVS_ROOT", "/venvs")
        return os.path.join(venv_root, short_hash)

    def install_venv(self, venv_dir: str, pex_filepath: str):
        # Unpacks the pex file into a venv at venv_dir
        try:
            subprocess.check_output(
                [
                    "pex-tools",
                    pex_filepath,
                    "venv",
                    # multiple packages sometimes provide the same file, eg dbt/__init__.py is in
                    # both dbt_core and dbt_duckdb
                    "--collisions-ok",
                    # since we combine multiple venvs, we need non hermetic scripts
                    "--non-hermetic-scripts",
                    venv_dir,
                    "--pip",
                ],
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            shutil.rmtree(venv_dir, ignore_errors=True)  # don't leave invalid dir behind
            raise PexInstallationError(
                f"Could not install venv. Pex output: {e.output}", pex_filepath
            ) from e
        logger.info(
            "Unpacked pex file %r into venv at %r",
            pex_filepath,
            venv_dir,
        )

    def get_site_packages_dir_for_venv(self, venv_path: Path) -> Path:
        python = venv_path / "bin" / "python3"
        proc = subprocess.run(
            [python, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            check=False,
        )
        if not proc.returncode:
            return Path(proc.stdout.decode("utf-8").strip()).absolute()
        else:
            logger.error(
                "Cannot determine site-packages for venv at %r: %s\n%s",
                venv_path,
                proc.stdout.decode("utf-8"),
                proc.stderr.decode("utf-8"),
            )
            raise PexInstallationError("Cannot determine site-packages", venv_path, proc.stderr)

    def get_working_dir_for_pex(self, pex_path: str) -> str | None:
        # A special 'working_directory' package may be included the source package.
        # If so we use site-packages/working_directory/root as the working dir.
        # This allows shipping arbitrary files to the server - also used for python_file support.
        if pex_path in self.working_dirs:
            return self.working_dirs[pex_path]
        try:
            working_dir_file = subprocess.check_output(
                [
                    pex_path,
                    "-c",
                    "import working_directory; print(working_directory.__file__);",
                ],
                encoding="utf-8",
            ).strip()
            if working_dir_file:
                package_dir, _ = working_dir_file.rsplit("/", 1)  # remove trailing __init__.py
                working_dir = os.path.join(package_dir, "root")
                self.working_dirs[pex_path] = working_dir
                return working_dir
            return None

        except subprocess.CalledProcessError:
            # working_directory package is optional, just log a message
            logger.info("Cannot import working_directory package - not setting current directory.")
            return None
        except OSError:
            # some issue with pex not being runnable, log an error but don't fail yet
            # might fail later if we try to run this again
            logger.exception(
                "Ignoring failure to run pex file to determine working_directory %r", pex_path
            )
            return None
