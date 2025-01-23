import csv
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
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
from longplexpy.multiqc_plugin import AdapterId
from longplexpy.multiqc_plugin import AdapterSetName
from longplexpy.multiqc_plugin import DemuxStage
from longplexpy.multiqc_plugin import DemuxStages
from longplexpy.multiqc_plugin import SampleId
from longplexpy.multiqc_plugin import WellId

log = logging.getLogger("multiqc")

LONGPLEX_ADAPTER_REGEX = re.compile(r".*([A-H][0-9]{2})_(P[57])$")
"""Regex for matching Well ID (ex. A12) and Adapter (ex. P5)"""


def derive_well_and_adapter(barcode: str) -> tuple[WellId, AdapterId]:
    """Derive Well ID and Adapter ID from a seqWell barcode ID."""
    match = LONGPLEX_ADAPTER_REGEX.search(barcode)
    if match is None:
        raise ValueError(f"Could not find Well ID and Adapter ID in {barcode}")
    else:
        return (match.group(1), match.group(2))


class LimaSummaryMetric(TypedDict):
    """Metrics found in *.lima.summary files

    Attributes:
        input_reads: The number of reads in unmapped BAM input to LIMA.
        pass_thresholds: The number of reads assigned to a single barcode (pair).
        fail_thresholds: The number of reads not assigned to a single barcode (pair).
        below_min_length: The number of reads with length below min-length after trimming
            barcode(s).
        below_min_score: The number of reads with barcode score(s) <= min-score.
        below_min_end_score: The number of reads with at least one barcode score <= min-end-score.
            Only relevant for reads with different barcodes in a pair.
        below_min_passes: The number of reads with < min-passes.
            Only relevant for CLR data, not CCS/HiFi data.
        below_min_lead_score: The number of reads with a second best barcode score within score-lead
            of the first best barcode.
        below_min_ref_span: The number of reads with barcode(s) below min-ref-span.
            This is the fraction of the barcode found in the read (ex. 0.4 for a 10bp barcode
            means 4 bases were found).
        no_smrtbell: The number of reads without a SMRTbell adapter
        undesired_hybrids: The number of reads with mismatched (non-neighbor) barcodes.
    """

    input_reads: int
    pass_thresholds: int
    fail_thresholds: int
    below_min_length: int
    below_min_score: int
    below_min_end_score: int
    below_min_passes: int
    below_min_lead_score: int
    below_min_ref_span: int
    no_smrtbell: int
    undesired_hybrids: int


class LimaCountMetric:
    """Metrics for counts of each barcode combination output by Lima"""

    def __init__(self, well_counts: dict[WellId, dict[AdapterSetName, int]]) -> None:
        self.well_counts = well_counts

    @classmethod
    def from_counts_text(cls, lima_counts_text: str) -> "LimaCountMetric":
        well_counts: dict = {}
        for row in csv.reader(lima_counts_text.splitlines(), delimiter="\t"):
            if len(row) == 0 or "Counts" in row:
                continue
            else:
                well1, adapter1 = derive_well_and_adapter(row[2])
                well2, adapter2 = derive_well_and_adapter(row[3])
                well_set = {well1, well2}
                adapter_set = "+".join(sorted({adapter1, adapter2}))
                if len(well_set) != 1:
                    raise ValueError(f"Cannot create count metric for undesired hybrid, {row}")
                well_counts.setdefault(well1, {})
                well_counts[well1][adapter_set] = well_counts[well1].setdefault(
                    adapter_set, 0
                ) + int(row[4])
        return cls(well_counts)


class LimaLongPlexMetric(TypedDict):
    """LongPlex Metrics from Lima Demultiplexing Stages"""

    input_reads: int
    i7_and_i5_demuxed: int
    i7_demuxed: int
    i5_demuxed: int
    total_demuxed: int
    failed_to_demux: int
    percent_demuxed: float
    undesired_hybrids: int
    undesired_hybrids_percent: float


@dataclass(frozen=True)
class MetricDefinition:
    """Defines a metric found in a Lima output file"""

    name: str
    regex: re.Pattern
    converter: Callable[[Any], int] = int
    is_optional: bool = False

    def search(self, text: str) -> re.Match:
        return self.regex.search(text)


class LimaLongPlexModule(BaseMultiqcModule):
    """A MultiQC module for Lima LongPlex lima_summary_metrics."""

    summary_key: str = "longplexpy/lima-longplex/summary"
    counts_key: str = "longplexpy/lima-longplex/counts"
    """The configuration keys for storing search patterns about Lima LongPlex outputs."""

    @staticmethod
    def demux_metric_patterns() -> list[MetricDefinition]:
        """Patterns for parsing the lima_summary_metrics within Lima LongPlex outputs."""
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
    def parse_summary_contents(contents: str) -> LimaSummaryMetric:
        """Parse the contents of a Lima LongPlex output file."""
        lima_summary_metrics: LimaSummaryMetric = dict()  # type: ignore

        for metric in LimaLongPlexModule.demux_metric_patterns():
            match = metric.search(contents)
            if match is not None:
                lima_summary_metrics[metric.name] = metric.converter(match.group(1))  # type: ignore

            elif not metric.is_optional:
                raise ValueError(
                    f"Could not find expected metric, {metric.name}, in Lima LongPlex output"
                )

        return lima_summary_metrics

    @staticmethod
    def summarize_stage_count_data(
        stage_data: Iterable[LimaCountMetric],
    ) -> LimaCountMetric:
        new_counts: dict[WellId, dict[AdapterSetName, int]] = defaultdict(dict)
        wells = set(chain(*[list(d.well_counts.keys()) for d in stage_data]))
        for well in wells:
            new_counts[well] = {}
            adapter_sets = set(
                chain(*[list(d.well_counts.get(well, {}).keys()) for d in stage_data])
            )
            for adapter_set in adapter_sets:
                new_counts[well][adapter_set] = sum(
                    [d.well_counts.get(well, {}).get(adapter_set, 0) for d in stage_data]
                )
        return LimaCountMetric(well_counts=new_counts)

    @staticmethod
    def summarize_longplex_data(
        stage_summary_data: dict[DemuxStage, LimaSummaryMetric],
        summed_count_data: LimaCountMetric,
    ) -> LimaLongPlexMetric:
        lima_summary_metrics: LimaLongPlexMetric = dict()  # type: ignore
        lima_summary_metrics["input_reads"] = max(
            [m["input_reads"] for m in stage_summary_data.values()]
        )
        lima_summary_metrics["i7_and_i5_demuxed"] = sum(
            [
                summed_count_data.well_counts[well].get("P5+P7", 0)
                + summed_count_data.well_counts[well].get("P7+P5", 0)
                for well in summed_count_data.well_counts.keys()
            ]
        )
        lima_summary_metrics["i7_demuxed"] = sum(
            [
                summed_count_data.well_counts[well].get("P7", 0)
                for well in summed_count_data.well_counts.keys()
            ]
        )
        lima_summary_metrics["i5_demuxed"] = sum(
            [
                summed_count_data.well_counts[well].get("P5", 0)
                for well in summed_count_data.well_counts.keys()
            ]
        )
        lima_summary_metrics["total_demuxed"] = (
            stage_summary_data[DEMUX_STAGE_I7_AND_I5]["pass_thresholds"]
            + stage_summary_data[DEMUX_STAGE_I7_OR_I5]["pass_thresholds"]
        )
        lima_summary_metrics["failed_to_demux"] = stage_summary_data[DEMUX_STAGE_I7_OR_I5][
            "fail_thresholds"
        ]
        lima_summary_metrics["percent_demuxed"] = (
            lima_summary_metrics["total_demuxed"] / lima_summary_metrics["input_reads"]
        )
        lima_summary_metrics["undesired_hybrids"] = stage_summary_data[DEMUX_STAGE_I7_AND_I5][
            "undesired_hybrids"
        ]
        lima_summary_metrics["undesired_hybrids_percent"] = (
            lima_summary_metrics["undesired_hybrids"] / lima_summary_metrics["input_reads"]
        )
        return lima_summary_metrics

    @staticmethod
    def derive_demux_stage(file_path: str) -> DemuxStage:
        """Derive the DemuxStage from the the path to the Lima LongPlex output file."""
        demux_stage = re.sub(".*demux_", "", file_path)
        if demux_stage not in DemuxStages:
            raise ValueError(f"Unrecognized Lima LongPlex demultiplexing stage, {demux_stage}")
        return demux_stage

    @staticmethod
    def derive_sample_id(sample_id: str) -> SampleId:
        """Strip seqWell prefixes from sample id"""
        return re.sub(r"^i7_i5_|^i7_5_", "", sample_id)

    def __init__(self) -> None:
        """Initialize the MultiQC Lima LongPlex module."""
        super(LimaLongPlexModule, self).__init__(
            name="Lima LongPlex",
            anchor="LimaLongPlex",
            target="LimaLongPlex",
            href="https://seqwell.com/",
            info=" is the use of Lima for the seqWell LongPlex assay.",
        )

        lima_summary_metrics: dict[SampleId, dict[DemuxStage, LimaSummaryMetric]] = defaultdict(
            dict
        )
        lima_count_metrics: dict[SampleId, dict[DemuxStage, LimaCountMetric]] = defaultdict(dict)

        for file in self.find_log_files(self.summary_key):
            summary_sample_id: SampleId = self.derive_sample_id(file[SAMPLE_NAME_KEY])
            summary_demux_stage: DemuxStage = self.derive_demux_stage(file[FILE_PATH_KEY])
            summary_parsed = self.parse_summary_contents(file[CONTENTS_KEY])
            lima_summary_metrics[summary_sample_id][summary_demux_stage] = summary_parsed

        for file in self.find_log_files(self.counts_key):
            count_sample_id: SampleId = self.derive_sample_id(file[SAMPLE_NAME_KEY])
            count_demux_stage: DemuxStage = self.derive_demux_stage(file[FILE_PATH_KEY])
            counts_parsed = LimaCountMetric.from_counts_text(file[CONTENTS_KEY])
            lima_count_metrics[count_sample_id][count_demux_stage] = counts_parsed

        lima_summary_metrics = self.ignore_samples(data=lima_summary_metrics)
        lima_count_metrics = self.ignore_samples(data=lima_count_metrics)

        if len(lima_summary_metrics) == 0 or len(lima_count_metrics) == 0:
            raise ModuleNoSamplesFound

        if set(lima_count_metrics.keys()) != set(lima_summary_metrics):
            raise ValueError("Incomplete Lima Count|Summary data for input samples.")

        summed_count_metrics: dict[SampleId, LimaCountMetric] = {
            sample: self.summarize_stage_count_data(lima_count_metrics[sample].values())
            for sample in lima_count_metrics.keys()
        }

        longplex_summary_metrics = {
            sample: self.summarize_longplex_data(
                lima_summary_metrics[sample], summed_count_metrics[sample]
            )
            for sample in lima_summary_metrics.keys()
        }

        # This doesn't seem to actually write anything
        self.write_data_file(data=longplex_summary_metrics, fn="multiqc_longplexpy_limalongplex")

        # General Statistics ###########################################################

        headers = {
            "input_reads": {
                "title": "ZMWs Input",
                "description": "The number of reads input to Lima.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "blue",
            },
            "total_demuxed": {
                "title": "ZMWs Demuxed",
                "description": "The number of reads successfully demultiplexed by Lima.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn",
            },
            "percent_demuxed": {
                "title": "ZMWs Demuxed (%)",
                "description": "The percent of reads successfully demultiplexed by Lima.",
                "min": 0,
                "format": "{:.1%}",
                "scale": "RdYlGn",
            },
            "failed_to_demux": {
                "title": "ZMWs Failed Demux",
                "description": "The number of reads identified with neither I7 nor I5 barcodes.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn-rev",
            },
            "undesired_hybrids": {
                "title": "Undesired Hybrids",
                "description": "Reads with mismatched barcodes",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn-rev",
            },
            "undesired_hybrids_percent": {
                "title": "Undesired Hybrids (%)",
                "description": "The percent of reads with mismatched barcodes",
                "min": 0,
                "format": "{:.1%}",
                "scale": "RdYlGn-rev",
            },
        }

        self.general_stats_addcols(longplex_summary_metrics, headers=headers)

        # Detailed Metrics #############################################################

        headers = {
            "input_reads": {
                "title": "ZMWs Input",
                "description": "The number of reads input to Lima.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "blue",
            },
            "i7_and_i5_demuxed": {
                "title": "i7 and i5 Demuxed",
                "description": "The number of reads identified with i7 and i5 barcodes.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn",
            },
            "i7_demuxed": {
                "title": "i7 Demuxed",
                "description": "The number of reads identified with either i7 barcodes.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn",
            },
            "i5_demuxed": {
                "title": "i5 Demuxed",
                "description": "The number of reads identified with either i5 barcodes.",
                "min": 0,
                "format": "{:.0f}",
                "scale": "RdYlGn",
            },
            "failed_to_demux": {
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
                data=longplex_summary_metrics,
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
            "title": "Lima LongPlex: Demultiplexing Summary",
            "cpswitch": True,
            "ylab": "ZMWs",
        }

        keys: Dict[str, Dict[str, str]] = {
            "i7_and_i5_demuxed": {"name": "ZMWs with i5 and i7"},
            "i7_demuxed": {"name": "ZMWs with i7"},
            "i5_demuxed": {"name": "ZMWs with i5"},
            "failed_to_demux": {"name": "ZMWs without i5 or i7"},
        }

        self.add_section(
            description=("Lima LongPlex Demultiplexing Summary Stacked Bar Graph"),
            plot=bargraph.plot(data=longplex_summary_metrics, cats=keys, pconfig=bargraph_config),
        )

        # Per-pool Bar Plots #############################################################
        pools = list(summed_count_metrics.keys())
        per_pool_pconfig = {
            "namespace": self.name,
            "id": "lima_longplex_well_demux_fractions",
            "title": "Lima LongPlex: Demultiplexing Summary by Well",
            "cpswitch": True,
            "ylab": "ZMWs",
            "data_labels": pools,
        }

        well_data = [summed_count_metrics[pool].well_counts for pool in pools]

        well_keys: Dict[str, Dict[str, str]] = {
            "P7+P5": {"name": "ZMWs with i5 and i7"},
            "P5+P7": {"name": "ZMWs with i5 and i7"},
            "P7": {"name": "ZMWs with i7"},
            "P5": {"name": "ZMWs with i5"},
        }

        self.add_section(
            description="LongPlex Demultiplexing by Well",
            plot=bargraph.plot(data=well_data, cats=well_keys, pconfig=per_pool_pconfig),
        )
