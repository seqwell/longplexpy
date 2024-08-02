import pytest

import longplexpy.lima as lima
from longplexpy.lima import LimaReportMetric


@pytest.mark.parametrize(
    "report_row, status",
    [
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_A01_P5",
                IdxHighestNamed="seqwell_UDI1_A01_P5",
            ),
            lima.PASS_STATUS,
        ),
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_A01_P5",
                IdxHighestNamed="seqwell_UDI1_A01_P7",
            ),
            lima.PASS_STATUS,
        ),
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_B01_P5",
                IdxHighestNamed="seqwell_UDI1_B01_P5",
            ),
            lima.PASS_STATUS,
        ),
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_A01_P5",
                IdxHighestNamed="seqwell_UDI1_A02_P5",
            ),
            lima.HYBRID_STATUS,
        ),
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_A01_P5",
                IdxHighestNamed="seqwell_UDI1_A02_P7",
            ),
            lima.HYBRID_STATUS,
        ),
        (
            LimaReportMetric(
                ZMW="zmw1",
                IdxLowestNamed="seqwell_UDI1_A01_P5",
                IdxHighestNamed="seqwell_UDI1_B01_P5",
            ),
            lima.HYBRID_STATUS,
        ),
    ],
)
def test_status_from_report_metric(report_row: LimaReportMetric, status: str) -> None:
    assert report_row.status == status
