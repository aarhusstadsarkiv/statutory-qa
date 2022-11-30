import os
from pathlib import Path

from statutory_qa import main


def test_parse_docIndex_xml():
    xml_file = Path("tests\\Indices\\docIndex.xml")
    output = main.parse_docIndex_xml(xml_file)
    assert output["odt"][0] == Path("docCollection1/1/1.tif")


def test_copy_files():
    files: dict[str, list[Path]] = {}
    files["odt"] = []
    files["odt"].append(Path("docCollection1/1/1.tif"))
    output_dir = Path(Path(__file__).parent.resolve(), "test_output")
    print(output_dir)

    input_dir = Path(__file__).parent.resolve()
    print(input_dir)
    checksums = main.parse_fileIndex_xml(Path("tests\\Indices\\fileIndex.xml"))
    main.copy_files(
        files,
        checksums,
        Path(input_dir, "Documents"),
        output_dir,
        max_examples=1,
    )

    file = Path(
        Path(__file__).parent.resolve(),
        "test_output\\odt\\docCollection1_1_1.tif",
    )
    file_exists = file.exists()
    assert file_exists

    if file_exists:
        file.unlink()
        os.rmdir(Path(output_dir, "odt"))
