import importlib.metadata
import logging

from typing import TypeAlias


__version__ = importlib.metadata.version("longplexpy")
"""The current version of the the longplexpy package."""

FIND_LOG_FILES_CONTENTS_KEY: str = "f"
"""The MultiQC configuration key for the contents of the metrics or logs files."""

FIND_LOG_FILES_FILENAME_KEY: str = "fn"
"""The MultiQC configuration key for the filename of the metrics or logs files."""

FIND_LOG_FILES_SAMPLE_NAME_KEY: str = "s_name"
"""The MultiQC configuration key for the inferred sample name of the metrics or logs files."""

SampleId: TypeAlias = str
"""A type alias for a sample ID."""

def longplexpy_multiqc_plugin_start() -> None:
    """Setup all the configuration needed for this MultiQC plugin."""

    from multiqc.utils import config  # type: ignore

    config.longplexpy_version = __version__

    log = logging.getLogger("multiqc")

    log.info(f"Running Fulcrum Genomics MultiQC Plugins (longplexpy) v{__version__}")

    if "longplexpy/lima-longplex" not in config.sp:
        config.update_dict(
            config.sp,
            {"longplexpy/lima-longplex": {"contents": "XXXXXXXX"}},  # TODO: how to autodetect file?
        )

    config.fn_clean_exts.extend([".lima", ".summary"])
