import xml.etree.ElementTree as ET
import shutil
import argparse
from pathlib import Path


ILLIGAL_NAMES = [
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
]


def get_version() -> str:
    version: str = "Ukendt version"
    with open(Path(__file__).absolute().parent.parent / "pyproject.toml") as i:
        for line in i.readlines():
            if line.startswith("version"):
                version = line[line.index('"') + 1 : -2]
    return version


def parse_docIndex_xml(
    xml_file: Path, max_examples: int = 3
) -> dict[str, list[Path]]:
    """Returns a dictionary containing suffixes as keys and lists
    of relative paths to be copied as values.

    Params:
        xml_file: Path to a valid and wellformed docIndex.xml file.

    Returns:
        A dict with unique lowercase file-suffixes extracted from the
          original filenames and a list of paths to example files.
    """
    # resulting output-dict of suffix: list of filepaths
    files_to_copy: dict[str, list[Path]] = {}

    # docIndex = Path(root_folder, "Indices\\docIndex.xml")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = ".//{http://www.sa.dk/xmlns/diark/1.0}"

    for doc in root:
        # extract suffix from original filename and clean it
        suffix = Path(
            str(doc.find(f"{ns}oFn").text)  # type: ignore
        ).suffix.strip()
        if suffix:
            suffix = suffix.lower()[1:]
        else:
            suffix = "manglende_filendelse"

        # ensure key exists and is not fully populated, in output-dict
        if suffix not in files_to_copy:
            files_to_copy[suffix] = []
        if len(files_to_copy[suffix]) >= max_examples:
            continue

        # assemble the relative path to the document that we have to copy
        # e.g. 'docCollection2/32/1.tif' (dCf / dID / "1." + aFt)
        doc_path = Path(
            str(doc.find(f"{ns}dCf").text),  # type: ignore
            str(doc.find(f"{ns}dID").text),  # type: ignore
            "1." + str(doc.find(f"{ns}aFt").text),  # type: ignore
        )

        # add relative filepath to output dict
        files_to_copy[suffix].append(doc_path)

    return files_to_copy


def copy_files(
    files: dict[str, list[Path]], document_dir: Path, output_dir: Path
) -> None:
    """Copies a dict of suffix: list of filepath to a given output_dir

    Params:
        files:
        output_dir: Path to the destination directory

    Returns:
        None
    """
    for suffix, file_paths in files.items():
        if suffix in ILLIGAL_NAMES:
            suffix = suffix + " (windows renaming)"

        folder_path = Path(output_dir, suffix)
        try:
            folder_path.mkdir(parents=True, exist_ok=False)
        except Exception as e:
            exit(f"Unable to create output-path: {folder_path}: {e}")

        # for each "{docCollection}/{id}/1.{ext}" copy to output_dir / suffix
        for file_path in file_paths:
            fname = str(file_path).replace("\\", "_")
            try:
                source = Path(document_dir, file_path)
                shutil.copy2(source, folder_path / fname)
            except Exception as e:
                print(f"Unable to copy file to: {folder_path / fname} {e}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description=(
            "Takes the first 3 files with the same suffix and copy them to"
            " output directory."
        )
    )
    parser.add_argument(
        "input", metavar="AVID_dir", type=str, help="Input AVID directory."
    )
    parser.add_argument(
        "output",
        metavar="output_dir",
        type=str,
        help="Output directory for copied files.",
    )

    parser.add_argument("--version", action="version", version=get_version())

    args = parser.parse_args(args)

    input_dir = args.input
    output_dir = args.output

    if Path(input_dir).exists():
        files = parse_docIndex_xml(
            Path(input_dir, "Indices", "docIndex.xml"), max_examples=4
        )
        copy_files(files, Path(input_dir, "Documents"), output_dir)


if __name__ == "__main__":
    main()
