from statutory_qa import main

# import sys
# sys.path.append("C:\\Users\\az68636\\github\\statutory-qa\\statutory_qa")
# import main
import os
from pathlib import Path


def test_parse_docIndex_xml():

    xml_file: Path = Path("tests\\docIndex.xml")

    output: dict[str, list[Path]] = main.parse_docIndex_xml(xml_file, 1)

    assert output["odt"][0] == Path("docCollection1/1/1.tif")


def test_copy_files():

    files: dict[str, list[Path]] = {}
    files["odt"] = []
    files["odt"].append(Path("docCollection1/1/1.tif"))
    # dir_path = Path(os.path.dirname(os.path.realpath(__file__)))
    output_dir = Path(Path(__file__).parent.resolve(), "test_output")
    print(output_dir)

    input_dir = Path(__file__).parent.resolve()
    print(input_dir)

    main.copy_files(files, Path(input_dir, "Documents"), output_dir)

    file = Path(
        Path(__file__).parent.resolve(),
        "test_output\\odt\\docCollection1_1_1.tif",
    )
    file_exists = file.exists()
    assert file_exists

    if file_exists:
        file.unlink()
        os.rmdir(Path(output_dir, "odt"))
