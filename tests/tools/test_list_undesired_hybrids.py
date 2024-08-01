import os
import tempfile
from pathlib import Path

from longplexpy.lima import LimaReportMetric
from longplexpy.tools.list_undesired_hybrids import list_undesired_hybrids


def test_list_undesired_hybrids() -> None:
    undesired_hybrids = [
        LimaReportMetric(
            ZMW="zmw1", IdxLowestNamed="seqwell_UDI1_A01_P5", IdxHighestNamed="seqwell_UDI1_B01_P5"
        ),
        LimaReportMetric(
            ZMW="zmw2", IdxLowestNamed="seqwell_UDI1_A01_P5", IdxHighestNamed="seqwell_UDI1_A02_P7"
        ),
    ]
    pass_zmws = [
        LimaReportMetric(
            ZMW="zmw3", IdxLowestNamed="seqwell_UDI1_B01_P5", IdxHighestNamed="seqwell_UDI1_B01_P5"
        ),
        LimaReportMetric(
            ZMW="zmw4", IdxLowestNamed="seqwell_UDI1_B01_P5", IdxHighestNamed="seqwell_UDI1_B01_P7"
        ),
    ]
    read_suffix = "/ccs"
    expected_reads = [lima_report.ZMW + read_suffix for lima_report in undesired_hybrids]
    temp_directory = tempfile.TemporaryDirectory()
    report_path = Path(os.path.join(temp_directory.name, "sample.lima.report"))
    output_path = os.path.join(temp_directory.name, "sample.hybrids.txt")
    LimaReportMetric.write(report_path, *(undesired_hybrids + pass_zmws))
    list_undesired_hybrids(
        lima_report=report_path,
        output=Path(output_path),
        read_name_suffix=read_suffix,
    )

    with open(output_path) as output:
        observed_zmws = [line.rstrip() for line in output.readlines()]
    assert observed_zmws == expected_reads
