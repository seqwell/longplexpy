import logging
import re

from typing import Any
from typing import Callable
from typing import Dict
from typing import Tuple
from typing import TypedDict
from typing import Union

from multiqc.plots import bargraph  # type: ignore
from multiqc.plots import table
from multiqc.modules.base_module import BaseMultiqcModule  # type: ignore
from multiqc.modules.base_module import ModuleNoSamplesFound

from longplexpy.multiqc_plugin import FIND_LOG_FILES_CONTENTS_KEY as CONTENTS_KEY
from longplexpy.multiqc_plugin import FIND_LOG_FILES_SAMPLE_NAME_KEY as SAMPLE_NAME_KEY
from longplexpy.multiqc_plugin import SampleId

log = logging.getLogger("multiqc")


class LimaLongPlexMetric(TypedDict):
    command: str
    optical_duplicate_distance: int
    read: int
    written: int
    excluded: int
    examined: int
    paired: int
    single: int
    duplicate_pair: int
    duplicate_single: int
    duplicate_pair_optical: int
    duplicate_single_optical: int
    duplicate_non_primary: int
    duplicate_non_primary_optical: int
    duplicate_primary_total: int
    duplicate_total: int
    estimated_library_size: int
    duplicate_optical_total: int
    duplicate_optical_fraction: float
    duplicate_fraction: float
    duplicate_paired_non_optical: int
    duplicate_single_non_optical: int
    duplicate_non_primary_non_optical: int
    non_duplicate: int


class LimaLongPlexModule(BaseMultiqcModule):
    """A MultiQC module for Lima LongPlex metrics."""

    search_key: str = "longplexpy/lima-longplex"
    """The configuration key for storing search patterns about Lima LongPlex outputs."""

    @staticmethod
    def markdup_metric_patterns() -> Dict[str, Tuple[re.Pattern, Callable[[Any], Union[int, str]]]]:
        """Patterns for parsing the metrics within Lima LongPlex outputs."""
        return {
            "command": (re.compile(r"COMMAND:\s(.*)"), str),
            "optical_duplicate_distance": (re.compile(r"COMMAND:\s.*-d\s(\d+)"), int),
            "read": (re.compile(r"READ:\s(\d+)"), int),
            "written": (re.compile(r"WRITTEN:\s(\d+)"), int),
            "excluded": (re.compile(r"EXCLUDED:\s(\d+)"), int),
            "examined": (re.compile(r"EXAMINED:\s(\d+)"), int),
            "paired": (re.compile(r"PAIRED:\s(\d+)"), int),
            "single": (re.compile(r"SINGLE:\s(\d+)"), int),
            "duplicate_pair": (re.compile(r"DUPLICATE\sPAIR:\s(\d+)"), int),
            "duplicate_single": (re.compile(r"DUPLICATE\sSINGLE:\s(\d+)"), int),
            "duplicate_pair_optical": (re.compile(r"DUPLICATE\sPAIR\sOPTICAL:\s(\d+)"), int),
            "duplicate_single_optical": (re.compile(r"DUPLICATE\sSINGLE\sOPTICAL:\s(\d+)"), int),
            "duplicate_non_primary": (re.compile(r"DUPLICATE\sNON\sPRIMARY:\s(\d+)"), int),
            "duplicate_non_primary_optical": (re.compile(r"DUPLICATE\sNON\sPRIMARY\sOPTICAL:\s(\d+)"), int),
            "duplicate_primary_total": (re.compile(r"DUPLICATE\sPRIMARY\sTOTAL:\s(\d+)"), int),
            "duplicate_total": (re.compile(r"DUPLICATE\sTOTAL:\s(\d+)"), int),
            "estimated_library_size": (re.compile(r"ESTIMATED_LIBRARY_SIZE:\s(\d+)"), int),
        }

    @staticmethod
    def parse_contents(contents: str) -> LimaLongPlexMetric:
        """Parse the contents of a Lima LongPlex output file."""
        metrics: LimaLongPlexMetric = dict()  # type: ignore

        for metric, (regex, converter) in LimaLongPlexModule.markdup_metric_patterns().items():
            match = regex.search(contents)
            if match:
                metrics[metric] = converter(match.group(1))  # type: ignore

            # TODO: should we have an else? Or something stronger like a raised exception?

        return metrics

    @staticmethod
    def derive_metrics(metrics: LimaLongPlexMetric) -> LimaLongPlexMetric:
        """Derive custom metrics from the contents of a Lima LongPlex output file."""
        reads: int = metrics["paired"] + metrics["single"]
        metrics["duplicate_optical_total"] = metrics["duplicate_pair_optical"] + metrics["duplicate_single_optical"]
        metrics["duplicate_optical_fraction"] = reads and metrics["duplicate_optical_total"] / reads or 0.0
        metrics["duplicate_fraction"] = reads and metrics["duplicate_total"] / reads or 0.0
        metrics["duplicate_paired_non_optical"] = metrics["duplicate_pair"] - metrics["duplicate_pair_optical"]
        metrics["duplicate_single_non_optical"] = metrics["duplicate_single"] - metrics["duplicate_single_optical"]
        metrics["duplicate_non_primary_non_optical"] = metrics["duplicate_non_primary"] - metrics["duplicate_non_primary_optical"]
        metrics["non_duplicate"] = metrics["paired"] + metrics["single"] - metrics["duplicate_total"]
        return metrics

    def __init__(self) -> None:
        """Initialize the MultiQC Lima LongPlex module."""
        super(LimaLongPlexModule, self).__init__(
            name="Lima LongPlex",
            anchor="LimaLongPlex",
            target="LimaLongPlex",
            href="https://seqwell.com/",
            info=" is the use of Lima for the seqWell LongPlex assay.",
        )

        metrics: Dict[SampleId, LimaLongPlexMetric] = dict()

        for file in self.find_log_files(self.search_key):
            parsed = self.parse_contents(file[CONTENTS_KEY])
            metrics[file[SAMPLE_NAME_KEY]] = self.derive_metrics(parsed)

        metrics = self.ignore_samples(data=metrics)

        if len(metrics) == 0:
            raise ModuleNoSamplesFound

        self.write_data_file(data=metrics, fn="multiqc_longplexpy_limalongplex")

        # General Statistics ###########################################################

        # TODO: ZACH EDIT ALL THE BELOW

        headers = {
            "duplicate_fraction": {
                "title": "% Duplicates",
                "description": "The percent of all types of duplicate reads.",
                "min": 0,
                "modify": lambda x: x * 100,
                "format": "{:,.0f}",
                "suffix": "%",
                "scale": "RdYlGn-rev",
            },
            "estimated_library_size": {
                "title": "Estimated Library Size",
                "description": "The estimated library size after de-duplication.",
                "min": 0,
                "format": "{:,.0f}",
            },
        }

        self.general_stats_addcols(data=metrics, headers=headers)

        # Detailed Metrics #############################################################

        headers = {
            "estimated_library_size": {
                "title": "Estimated Library Size",
                "description": "The estimated library size after de-duplication.",
                "min": 0,
                "format": "{:,.0f}",
            },
            "optical_duplicate_distance": {
                "title": "Optical Distance",
                "description": "The optical distance for considering instrument duplicates.",
                "min": 0,
                "format": "{:,.0f}",
            },
            "duplicate_fraction": {
                "title": "% Duplicates",
                "description": "The percent of all types of duplicate reads.",
                "min": 0,
                "modify": lambda x: x * 100,
                "format": "{:,.0f}",
                "suffix": "%",
                "scale": "RdYlGn-rev",
            },
            "duplicate_optical_fraction": {
                "title": "% Optical Duplicates",
                "description": "The percent of optical/clustering duplicate reads.",
                "min": 0,
                "modify": lambda x: x * 100,
                "format": "{:,.0f}",
                "suffix": "%",
                "scale": "RdYlGn-rev",
            },
        }

        self.add_section(
            name="Duplicate Marking",
            anchor="tn_seq-samtools-markdup-metrics",
            description=(
                "Optical duplicates are due to either optical or clustering-based artifacts. "
                + "See the following links to learn more about instrument-based duplicate "
                + "artifacts:"
                + "<br>"
                + "<ul>"
                + '<li><a href="https://core-genomics.blogspot.com/2016/05/increased-read-duplication-on-patterned.html" '
                + 'target="_blank">Core Genomics Post: Increased Read Duplication on Patterned '
                + "Flowcells</a>"
                + "</li>"
                + '<li><a href="https://sequencing.qcfail.com/articles/illumina-patterned-flow-cells-generate-duplicated-sequences/" '
                + 'target="_blank">QC Fail Post: Illumina Patterned Flow Cells Generate '
                + "Duplicated Sequences</a>"
                + "</li>"
                + "</ul>."
            ),
            plot=table.plot(
                data=metrics,
                headers=headers,
                pconfig={
                    "namespace": self.name,
                    "id": "tn_seq_samtools_markdup_metrics_table",
                    "table_title": "Samtools: Duplicate Marked SAM Records (Alignments)",
                    "sortRows": False,
                },
            ),
        )

        # Stacked Bar Plot #############################################################

        bargraph_config = {
            "namespace": self.name,
            "id": "tn_seq_samtools_markdup_metrics_fraction",
            "title": "Samtools: Duplicate Marked SAM Records (Alignments)",
            "cpswitch": True,
            "ylab": "% SAM Records",
        }

        # TODO; Confirm that under all ways to run samtools markdup, these sum up to "all records"
        keys: Dict[str, Dict[str, str]] = {
            "non_duplicate": {"name": "Non-Duplicates"},
            "duplicate_pair_optical": {"name": "Optical Duplicates in Pairs"},
            "duplicate_single_optical": {"name": "Optical Duplicates in Singletons"},
            "duplicate_non_primary_optical": {"name": "Optical Non-Primary Duplicate"},
            "duplicate_pair_non_optical": {"name": "Non-optical Duplicates in Pairs"},
            "duplicate_single_non_optical": {"name": "Non-optical Duplicates in Singletons"},
            "duplicate_non_primary_non_optical": {"name": "Non-Optical Non-Primary Duplicates"},
            "excluded": {"name": "Ignored (QC fail or unmapped)"},
        }

        self.add_section(
            description=(
                "For more information about the duplicate categories, see the "
                + '<a href="https://www.htslib.org/doc/samtools-markdup.html#STATISTICS" '
                + 'target="_blank">samtools documentation</a>. '
            ),
            plot=bargraph.plot(data=metrics, cats=keys, pconfig=bargraph_config),
        )
