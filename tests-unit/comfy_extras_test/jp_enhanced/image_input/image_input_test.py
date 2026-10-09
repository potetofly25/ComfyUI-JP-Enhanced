import numpy as np
import pytest
from PIL import Image

from comfy_extras.jp_enhanced.image_input import JPImageFolderList


def test_mixed_sizes_and_page_selection(tmp_path):
    Image.new("RGB", (71, 93), "red").save(tmp_path / "001.png")
    Image.new("RGB", (120, 65), "blue").save(tmp_path / "002.png")
    sub = tmp_path / "sub"
    sub.mkdir()
    Image.new("RGB", (55, 77), "green").save(sub / "003.png")
    loader = JPImageFolderList()
    images, = loader.load_images(str(tmp_path))
    assert [tuple(x.shape) for x in images] == [(1, 93, 71, 3), (1, 65, 120, 3)]
    np.testing.assert_array_equal(images[0][0, 0, 0].numpy(), [1, 0, 0])
    selected, = loader.load_images(str(tmp_path), 1, 1)
    assert tuple(selected[0].shape) == (1, 65, 120, 3)
    recursive, = loader.load_images(str(tmp_path), include_subfolders=True)
    assert len(recursive) == 3
    with pytest.raises(ValueError, match="No images"):
        loader.load_images(str(tmp_path), start_index=3)


def test_exif_orientation(tmp_path):
    image = Image.new("RGB", (70, 90))
    exif = Image.Exif()
    exif[274] = 6
    image.save(tmp_path / "page.jpg", exif=exif)
    images, = JPImageFolderList().load_images(str(tmp_path))
    assert tuple(images[0].shape) == (1, 70, 90, 3)
