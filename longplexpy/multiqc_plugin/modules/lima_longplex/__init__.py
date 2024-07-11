import logging
import re
from typing import Any
from typing import Callable
from typing import Dict
from typing import TypedDict

from multiqc.base_module import BaseMultiqcModule  # type: ignore
from multiqc.base_module import ModuleNoSamplesFound
from multiqc.plots import bargraph  # type: ignore
from multiqc.plots import table

from longplexpy.multiqc_plugin import DEMUX_STAGE_I7_AND_I5
from longplexpy.multiqc_plugin import DEMUX_STAGE_I7_OR_I5
from longplexpy.multiqc_plugin import FIND_LOG_FILES_CONTENTS_KEY as CONTENTS_KEY
from longplexpy.multiqc_plugin import FIND_LOG_FILES_PATH_KEY as FILE_PATH_KEY
from longplexpy.multiqc_plugin import FIND_LOG_FILES_SAMPLE_NAME_KEY as SAMPLE_NAME_KEY
from longplexpy.multiqc_plugin import DemuxStage
from longplexpy.multiqc_plugin import DemuxStages
from longplexpy.multiqc_plugin import SampleId

log = logging.getLogger("multiqc")


class LimaMetric(TypedDict):
    input_reads: int


class LimaLongPlexMetric(TypedDict):
    input_reads: int
    i7_and_i5_demuxed: int
    i7_or_i5_demuxed: int
    total_demuxed: int
    failed_to_demux: int


class MetricDefinition:
    """Defines a metric found in a Lima output file"""

    def __init__(
        self,
        name: str,
        regex: re.Pattern,
        converter: Callable[[Any], int] = int,
        is_optional: bool = False,
    ) -> None:
        self.name = name
        self.regex = regex
        self.converter = converter
        self.is_optional = is_optional

    def search(self, text):
        return self.regex.search(text)


class LimaLongPlexModule(BaseMultiqcModule):
    """A MultiQC module for Lima LongPlex metrics."""

    search_key: str = "longplexpy/lima-longplex"
    """The configuration key for storing search patterns about Lima LongPlex outputs."""

    @staticmethod
    def demux_metric_patterns() -> list[MetricDefinition]:
        """Patterns for parsing the metrics within Lima LongPlex outputs."""
        return [
            MetricDefinition(
                name="input_reads",
                regex=re.compile(r"ZMWs input.*:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="pass_thresholds",
                regex=re.compile(r"ZMWs above all thresholds.*:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="fail_thresholds",
                regex=re.compile(r"ZMWs below any threshold.*:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_length",
                regex=re.compile(r"Below min length[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_score",
                regex=re.compile(r"Below min score[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_end_score",
                regex=re.compile(r"Below min end score[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_passes",
                regex=re.compile(r"Below min passes[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_lead_score",
                regex=re.compile(r"Below min score lead[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="below_min_ref_span",
                regex=re.compile(r"Below min ref span[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="no_smrtbell",
                regex=re.compile(r"Without SMRTbell adapter[\s]+:\s([0-9]+)"),
            ),
            MetricDefinition(
                name="undesired_hybrids",
                regex=re.compile(r"Undesired hybrids[\s]+:\s([0-9]+)"),
                is_optional=True,
            ),
            MetricDefinition(
                name="not_direct_neighbors",
                regex=re.compile(r"Not direct neighbors[\s]+:\s([0-9]+)"),
                is_optional=True,
            ),
        ]

    @staticmethod
    def parse_contents(contents: str) -> LimaMetric:
        """Parse the contents of a Lima LongPlex output file."""
        metrics: LimaMetric = dict()  # type: ignore

        for metric in LimaLongPlexModule.demux_metric_patterns():
            match = metric.search(contents)
            if match is not None:
                metrics[metric.name] = metric.converter(match.group(1))  # type: ignore

            elif not metric.is_optional:
                raise ValueError(
                    f"Could not find expected metric, {metric.name}, in Lima LongPlex output"
                )

        return metrics

    @staticmethod
    def summarize_stage_data(stage_data: dict[DemuxStage, LimaMetric]) -> LimaLongPlexMetric:
        metrics: LimaLongPlexMetric = dict()  # type: ignore
        metrics["input_reads"] = max([m["input_reads"] for m in stage_data.values()])
        metrics[DEMUX_STAGE_I7_AND_I5] = stage_data[DEMUX_STAGE_I7_AND_I5]["pass_thresholds"]
        metrics[DEMUX_STAGE_I7_OR_I5] = stage_data[DEMUX_STAGE_I7_OR_I5]["pass_thresholds"]
        metrics["total_demuxed"] = (
            stage_data[DEMUX_STAGE_I7_AND_I5]["pass_thresholds"]
            + stage_data[DEMUX_STAGE_I7_OR_I5]["pass_thresholds"]
        )
        metrics["failed_demux"] = stage_data[DEMUX_STAGE_I7_OR_I5]["fail_thresholds"]
        return metrics

    @staticmethod
    def derive_demux_stage(file_path: str) -> DemuxStage:
        """Derive the DemuxStage from the the path to the Lima LongPlex output file."""
        demux_stage = re.sub(".*demux_", "", file_path)
        if demux_stage not in DemuxStages:
            raise ValueError(f"Unrecognized Lima LongPlex demultiplexing stage, {demux_stage}")
        return demux_stage

    def __init__(self) -> None:
        """Initialize the MultiQC Lima LongPlex module."""
        super(LimaLongPlexModule, self).__init__(
            name="Lima LongPlex",
            anchor="LimaLongPlex",
            target="LimaLongPlex",
            href="https://seqwell.com/",
            info=" is the use of Lima for the seqWell LongPlex assay.",
        )

        metrics: Dict[SampleId, Dict[DemuxStage, LimaMetric]] = dict()

        for file in self.find_log_files(self.search_key):
            metrics.setdefault(file[SAMPLE_NAME_KEY], {})
            demux_stage = self.derive_demux_stage(file[FILE_PATH_KEY])
            parsed = self.parse_contents(file[CONTENTS_KEY])
            metrics[file[SAMPLE_NAME_KEY]][demux_stage] = parsed

        metrics = self.ignore_samples(data=metrics)

        if len(metrics) == 0:
            raise ModuleNoSamplesFound

        longplex_metrics = {
            sample: self.summarize_stage_data(stages_dict)
            for sample, stages_dict in metrics.items()
        }

        # This doesn't seem to actually write anything
        self.write_data_file(data=longplex_metrics, fn="multiqc_longplexpy_limalongplex")

        # General Statistics ###########################################################

        headers = {
            "input_reads": {
                "title": "ZMWs Input",
                "description": "The number of reads input to Lima.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            "total_demuxed": {
                "title": "ZMWs Demuxed",
                "description": "The number of reads successfully demultiplexed by Lima.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            "failed_demux": {
                "title": "ZMWs Failed Demux",
                "description": "The number of reads identified with neither I7 nor I5 barcodes.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn-rev",
            },
        }

        self.general_stats_addcols(data=longplex_metrics, headers=headers)

        # Detailed Metrics #############################################################

        headers = {
            "input_reads": {
                "title": "ZMWs Input",
                "description": "The number of reads input to Lima.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            DEMUX_STAGE_I7_AND_I5: {
                "title": f"{DEMUX_STAGE_I7_AND_I5} Demuxed",
                "description": "The number of reads identified with I7 and I5 barcodes.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            DEMUX_STAGE_I7_OR_I5: {
                "title": f"{DEMUX_STAGE_I7_OR_I5} Demuxed",
                "description": "The number of reads identified with either I7 or I5 barcodes.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            "total_demuxed": {
                "title": "ZMWs Demuxed",
                "description": "The number of reads successfully demultiplexed by Lima.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn",
            },
            "failed_demux": {
                "title": "ZMWs Failed Demux",
                "description": "The number of reads identified with neither I7 nor I5 barcodes.",
                "min": 0,
                "format": "{:,.0f}",
                "scale": "RdYlGn-rev",
            },
        }

        self.add_section(
            name="Lima LongPlex Demultiplexing",
            anchor="lima-longplex-demultiplexing",
            description=("Summary of Lima demultiplexing results for a LongPlex pool. "),
            plot=table.plot(
                data=longplex_metrics,
                headers=headers,
                pconfig={
                    "namespace": self.name,
                    "id": "lima_longplex_metrics_table",
                    "title": "ZMWs Demultiplexed with Lima",
                    "sort_rows": False,
                },
            ),
        )

        # Stacked Bar Plot #############################################################

        bargraph_config = {
            "namespace": self.name,
            "id": "lima_longplex_demux_fractions",
            "title": "Lima LongPlex: Demultiplexing by Stage",
            "cpswitch": True,
            "ylab": "% ZMWs",
        }

        keys: Dict[str, Dict[str, str]] = {
            DEMUX_STAGE_I7_AND_I5: {"name": "ZMWs with I5 and I7"},
            DEMUX_STAGE_I7_OR_I5: {"name": "ZMWs with I5 or I7"},
            "failed_demux": {"name": "ZMWs without I5 or I7"},
        }

        self.add_section(
            description=(""),
            plot=bargraph.plot(data=longplex_metrics, cats=keys, pconfig=bargraph_config),
        )
