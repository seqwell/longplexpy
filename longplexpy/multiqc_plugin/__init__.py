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

FIND_LOG_FILES_PATH_KEY: str = "root"
"""The MultiQC configuration key for the path to the metrics or logs files."""

SampleId: TypeAlias = str
"""A type alias for a sample ID."""

DemuxStage: TypeAlias = str
"""A type alias for a stage of demultiplexing."""

WellId: TypeAlias = str
"""A type alias for the well associated with a sample within a LongPlex pool."""

AdapterId: TypeAlias = str
"""A type alias for the adapter associated with a specific barcode (P5 or P7)"""

AdapterSetName: TypeAlias = str
"""A set of AdapterIds"""

DEMUX_STAGE_I7_AND_I5: DemuxStage = "i7_i5"
DEMUX_STAGE_I7_OR_I5: DemuxStage = "either_i7_i5"

DemuxStages: list[DemuxStage] = [DEMUX_STAGE_I7_AND_I5, DEMUX_STAGE_I7_OR_I5]
"""The recognized Lima LongPlex demultiplexing stages."""

AdapterSetList: list[AdapterSetName] = ["P5+P7", "P5", "P7"]
"""List of recognized AdapterSets"""


def longplexpy_multiqc_plugin_start() -> None:
    """Setup all the configuration needed for this MultiQC plugin."""

    from multiqc.utils import config  # type: ignore

    config.longplexpy_version = __version__

    log = logging.getLogger("multiqc")

    log.info(f"Running Fulcrum Genomics MultiQC Plugins (longplexpy) v{__version__}")

    if "longplexpy/lima-longplex" not in config.sp:
        config.update_dict(
            config.sp,
            {
                "longplexpy/lima-longplex/summary": {"fn": "*.lima.summary"},
                "longplexpy/lima-longplex/counts": {"fn": "*.lima.counts"},
            },
        )

    config.fn_clean_exts.extend([".lima", ".summary", ".csv", "_demux_report"])
