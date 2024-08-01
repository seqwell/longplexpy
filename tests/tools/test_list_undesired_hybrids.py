import os
import tempfile
from pathlib import Path

from longplexpy.lima import FIRST_BARCODE
from longplexpy.lima import SECOND_BARCODE
from longplexpy.lima import ZMW_NAME
from longplexpy.tools.list_undesired_hybrids import list_undesired_hybrids


def test_list_undesired_hybrids() -> None:
    header = [ZMW_NAME, FIRST_BARCODE, SECOND_BARCODE]
    undesired_hybrids = [
        ("zmw1", "seqwell_UDI1_A01_P5", "seqwell_UDI1_B01_P5"),
        ("zmw2", "seqwell_UDI1_A01_P5", "seqwell_UDI1_A02_P7"),
    ]
    pass_zmws = [
        ("zmw3", "seqwell_UDI1_B01_P5", "seqwell_UDI1_B01_P5"),
        ("zmw4", "seqwell_UDI1_B01_P5", "seqwell_UDI1_B01_P7"),
    ]
    read_suffix = "/ccs"
    expected_zmws = [zmw + read_suffix for zmw, _, _ in undesired_hybrids]
    temp_directory = tempfile.TemporaryDirectory()
    report_path = os.path.join(temp_directory.name, "sample.lima.report")
    output_path = os.path.join(temp_directory.name, "sample.hybrids.txt")
    with open(report_path, mode="w") as report_file:
        report_file.writelines(
            [
                "\t".join(header) + "\n",
                "\n".join(["\t".join(row) for row in undesired_hybrids]) + "\n",
                "\n".join(["\t".join(row) for row in pass_zmws]) + "\n",
            ]
        )
        report_file.seek(0)
        list_undesired_hybrids(
            lima_report=Path(report_file.name),
            output=Path(output_path),
            read_name_suffix=read_suffix,
        )

    with open(output_path) as output:
        observed_zmws = [line.rstrip() for line in output.readlines()]
    assert observed_zmws == expected_zmws

