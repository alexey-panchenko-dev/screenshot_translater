from screen_translator.capture.geometry import ScreenPoint, ScreenRegion


def test_region_normalizes_reverse_drag() -> None:
    region = ScreenRegion.from_points(ScreenPoint(300, 250), ScreenPoint(100, 50))

    assert region == ScreenRegion(left=100, top=50, width=200, height=200)


def test_region_preserves_negative_monitor_coordinates() -> None:
    region = ScreenRegion.from_points(ScreenPoint(-1200, 20), ScreenPoint(-900, 220))

    assert region == ScreenRegion(left=-1200, top=20, width=300, height=200)


def test_minimum_size_requires_both_dimensions() -> None:
    assert ScreenRegion(0, 0, 8, 8).is_large_enough(8)
    assert not ScreenRegion(0, 0, 7, 100).is_large_enough(8)
    assert not ScreenRegion(0, 0, 100, 7).is_large_enough(8)


def test_mss_monitor_mapping() -> None:
    region = ScreenRegion(left=-10, top=20, width=30, height=40)

    assert region.as_mss_monitor() == {
        "left": -10,
        "top": 20,
        "width": 30,
        "height": 40,
    }


def test_region_scales_qt_logical_coordinates_to_physical_pixels() -> None:
    region = ScreenRegion(left=100, top=50, width=117, height=43)

    assert region.scaled(1.25) == ScreenRegion(
        left=125, top=62, width=146, height=54
    )


def test_region_scaling_preserves_negative_monitor_coordinates() -> None:
    region = ScreenRegion(left=-2048, top=0, width=100, height=50)

    assert region.scaled(1.25) == ScreenRegion(
        left=-2560, top=0, width=125, height=62
    )
