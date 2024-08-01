import csv
from pathlib import Path

from longplexpy.lima import HYBRID_STATUS
from longplexpy.lima import REPORT_FIELDS
from longplexpy.lima import ZMW_NAME
from longplexpy.lima import status_from_report_row
from longplexpy.lima import validate_header


def list_undesired_hybrids(
    *,
    lima_report: Path,
    output: Path,
    read_name_suffix: str = "/ccs",
) -> None:
    """List undesired hybrids in lima.report file

    Args:
        lima_report: the lima.report file which identifies undesired hybrids
        read_name_suffix: String to append to ZMW names to generate read names.
            Lima may remove read suffixes to generate ZMW names.
            This parameter can be used to reconstruct read names as they appear in the input BAM.
            Default = "/ccs"
    """

    with open(lima_report) as report_file, open(output, mode="w") as out_file:
        report_reader = csv.DictReader(report_file, delimiter="\t")
        validate_header(report_reader.fieldnames, REPORT_FIELDS)
        for row in report_reader:
            if status_from_report_row(row) == HYBRID_STATUS:
                out_file.write(f"{row[ZMW_NAME]}{read_name_suffix}\n")
