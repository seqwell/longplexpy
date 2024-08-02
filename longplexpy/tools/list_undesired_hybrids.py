from pathlib import Path
from typing import Iterator

from longplexpy.lima import HYBRID_STATUS
from longplexpy.lima import LimaReportMetric


def list_undesired_hybrids(
    *,
    lima_report: Path,
    output: Path,
    read_name_suffix: str = "/ccs",
) -> None:
    """List undesired hybrids in lima.report file

    Args:
        lima_report: the lima.report file which identifies undesired hybrids.
        output: the text output file where the list of undesired hybrids will be written.
        read_name_suffix: string to append to ZMW names to generate read names.
            Lima may remove read suffixes to generate ZMW names.
            This parameter can be used to reconstruct read names as they appear in the input BAM.
            Default = "/ccs"
    """

    with open(output, mode="w") as out_file:
        report_reader: Iterator[LimaReportMetric] = LimaReportMetric.read(lima_report)
        for report_row in report_reader:
            if report_row.status == HYBRID_STATUS:
                out_file.write(f"{report_row.ZMW}{read_name_suffix}\n")
