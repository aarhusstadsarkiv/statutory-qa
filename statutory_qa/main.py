import xml.etree.ElementTree as ET
import shutil
import argparse
from pathlib import Path
from typing import Set


ILLEGAL_NAMES = [
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
    version = "Ukendt version"
    with open(Path(__file__).absolute().parent.parent / "pyproject.toml") as i:
        for line in i.readlines():
            if line.startswith("version"):
                version = line[line.index('"') + 1 : -2]
    return version


def parse_fileIndex_xml(xml_file: Path) -> dict[str, str]:
    """Returns a dictionary containing the relative_paths and checksums
    of ALL files in the 'Documents' folder of the AVID.

    Params:
        xml_file: Path to a valid and wellformed fileIndex.xml

    Returns:
        A dict relative_paths and checksums of all the files in the
          'Documents' folder of the AVID.
    """
    checksums: dict[str, str] = {}
    tree = ET.parse(xml_file)
    root = tree.getroot()
    ns = ".//{http://www.sa.dk/xmlns/diark/1.0}"

    for f in root:
        fpath = Path(str(f.find(f"{ns}foN").text).strip())  # type: ignore
        fparts = fpath.parts
        if len(fparts) < 3:
            # print(f"{fpath}")
            continue
        if fparts[-3] != "Documents":
            continue

        fname = str(f.find(f"{ns}fiN").text).strip()  # type: ignore
        path = f"{fpath.parts[-2]}/{fpath.parts[-1]}/{fname}"

        if path in checksums:
            print(f"Path already in 'checksums'-dict: {path}", flush=True)
            continue

        checksums[path] = str(f.find(f"{ns}md5").text).strip()  # type: ignore

    return checksums


def parse_docIndex_xml(xml_file: Path) -> dict[str, list[Path]]:
    """Returns a dictionary containing suffixes as keys and lists
    of relative paths as values.

    Params:
        xml_file: Path to a valid and wellformed docIndex.xml.

    Returns:
        A dict with unique lowercase file-suffixes extracted from the
          original filenames and a list of paths to the files.
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
    files: dict[str, list[Path]],
    checksums: dict[str, str],
    document_dir: Path,
    output_dir: Path,
    max_examples: int,
) -> None:
    """Copies a dict of suffix: list of filepath to a given output_dir

    Params:
        files: Dict of suffix: filepaths[]
        checksums: Dict of filepath: MD5 checksum
        doc_dir: Path to the 'Documents' folder of the AVID
        output_dir: Path to the destination directory
        max_examples: Maximum number of examples files returned

    Returns:
        None
    """
    copied_files: dict[str, list[str]] = {}

    for suffix, file_paths in files.items():
        # rename if suffix is illegal
        if suffix in ILLEGAL_NAMES:
            suffix = suffix + " (windows renaming)"

        # ensure suffix is in copied_files
        if suffix not in copied_files:
            copied_files[suffix] = []

        # ensure suffix is in output_dir
        suffix_path = Path(output_dir, suffix)
        if not suffix_path.exists():
            suffix_path.mkdir(parents=True)

        # for each "{docCollection}/{id}/1.{ext}" copy to output_dir/suffix
        for file_path in file_paths:
            if len(copied_files[suffix]) == max_examples:
                print(f"Reached limit of {max_examples} for ext: {suffix}")
                break

            fname = "/".join(file_path.parts)
            checksum = checksums.get(fname, "")
            # if checksum already copied
            if checksum in copied_files[suffix]:
                print(f"Checksum already copied: {checksum}")
                continue

            source_path = Path(document_dir, file_path)
            if not source_path.exists():
                print(f"File from docIndex not found: {source_path}")
                continue

            try:
                shutil.copy2(
                    source_path,
                    Path(output_dir / suffix / fname.replace("/", "_")),
                )
                copied_files[suffix].append(checksum)
            except Exception as e:
                print(f"Error copying file: {source_path} {e}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description=(
            "Copies examples of statutory files from an AVID-compliant"
            " Documents' folder to the supplied output_dir.\n\n"
            "The statutory files to copy are grouped by the suffix of their"
            " original filename, found in the '<oFn>' tag in 'docIndex.xml'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=get_version())

    parser.add_argument(
        "input",
        metavar="avid_dir",
        type=Path,
        help="Path to the root of a valid AVID-package",
    )
    parser.add_argument(
        "output",
        metavar="output_dir",
        type=Path,
        help="Output directory for copied files",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=5,
        help=(
            "max number of example files to copy for each file"
            " extension (default: %(default)s)"
        ),
    )

    parser.add_argument(
        "--histogram",
        action="store_true",
        help=("print a list of suffixes and number of original files"),
    )

    parser.add_argument(
        "--checksum",
        type=str,
        help=("print ext: count for each file matching the checksum"),
    )

    args = parser.parse_args(args)

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    max_examples = int(args.max)

    ##############
    # Validation #
    ##############
    if max_examples < 1:
        exit(
            "Choose a positive number of example files with the '--max' option"
        )

    if not input_dir.exists():
        exit("Input directory doesn't exists.")

    fileIndex_xml = Path(input_dir, "Indices", "fileIndex.xml")
    if not fileIndex_xml.exists():
        exit("The avid_dir path doesn't contain 'Indices\\fileIndex.xml'")

    docIndex_xml = Path(input_dir, "Indices", "docIndex.xml")
    if not docIndex_xml.exists():
        exit("The avid_dir path doesn't contain 'Indices\\docIndex.xml'")

    # try to create output_dir
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=False)
        except Exception as e:
            exit(
                f"Access error: Unable to make directory "
                f"at the specified location: {e}"
            )
    # try to write a file to output_dir
    try:
        temp_file_path: Path = output_dir / "temp.tmp"
        f = open(temp_file_path, "w")
        f.write("Write access test...")
        f.close()
        temp_file_path.unlink()
    except Warning as w:
        exit(
            f"Access error: Unable to create file "
            f"at the specified location: {w}"
        )

    #####################
    # Files by checksum #
    #####################
    if args.checksum:
        # dict of extension, count signifying number of extensions matching
        # args.checksum
        output: dict[str, int] = {}
        checksums = parse_fileIndex_xml(fileIndex_xml)
        print(f"Samlet antal filer: {len(checksums)}", flush=True)
        paths: Set[str] = set(
            k for k, v in checksums.items() if v == args.checksum
        )
        print(f"Antal matching filer fundet: {len(paths)}", flush=True)
        docIndex_files: dict[str, list[Path]] = parse_docIndex_xml(
            docIndex_xml
        )
        print("Start iterating through matches in docIndex.xml", flush=True)
        i = 0
        for ext, path_list in docIndex_files.items():
            if i % 10 == 0:
                print("Finished parsing 10 extensions", flush=True)
            for path in path_list:
                if "/".join(path.parts) not in paths:
                    continue
                if ext not in output:
                    output[ext] = 0
                output[ext] += 1
            i += 1

        for k, v in output.items():
            print(f"{k},{v}", flush=True)

        # print(f"checksum submittet: {args.checksum}")
        exit()

    # Histogram #
    #############
    if args.histogram:
        docIndex_files = parse_docIndex_xml(docIndex_xml)
        print("File extension\tCount", flush=True)
        for tuple in sorted(
            docIndex_files.items(), key=lambda i: len(i[1]), reverse=True
        ):
            print(f"{tuple[0]}\t\t{len(tuple[1])}", flush=True)
        exit()

    ##############
    # copy files #
    ##############
    checksums = parse_fileIndex_xml(fileIndex_xml)
    docIndex_files = parse_docIndex_xml(docIndex_xml)
    copy_files(
        docIndex_files,
        checksums,
        Path(input_dir, "Documents"),
        output_dir,
        max_examples,
    )


if __name__ == "__main__":
    main()
