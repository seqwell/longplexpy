def well_from_barcode(barcode_name: str) -> str:
    """Identify barcode well from barcode name

    Args:
        barcode_name: Barcode name expected to adhere to pattern
            seqwell_[Barcode Set]_[Well]_[Adapter]
    Raises:
        ValueError if barcode name is not split into 4 elements by underscores
    """
    split_barcode = barcode_name.split("_")
    if len(split_barcode) != 4:
        raise ValueError(
            f"Barcode, ${barcode_name} does not match expected pattern"
            "seqwell_[Barcode Set]_[Well]_[Adapter]"
        )
    return split_barcode[2]
