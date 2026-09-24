from src.settings import study_area


def test_study_area_bbox_is_valid():
    bbox = study_area()["provisional_bbox_wgs84"]
    assert len(bbox) == 4
    assert bbox[0] < bbox[2]
    assert bbox[1] < bbox[3]
