import xml.etree.ElementTree as ET
from pathlib import Path
import os
import shutil
import argparse

histogram: dict[str, int] = {}  # ".pdf": 0
paths_out: list[Path] = []
to_copy: dict[str, list[Path]] = {}
to_copy_filename: dict[str, list[str]] = {}

def get_version() -> str:
    version: str = "Ukendt version"
    with open(Path(__file__).absolute().parent.parent / "pyproject.toml") as i:
        for line in i.readlines():
            if line.startswith("version"):
                version = line[line.index('"') + 1 : -2]
    return version


def readXML(parent_folder: Path):

    docIndex = Path(parent_folder, "Indices\\docIndex.xml")
    tree = ET.parse(docIndex)
    root = tree.getroot()

    print(parent_folder)
    parent_folder = Path(parent_folder, "Documents")

    ns = ".//{http://www.sa.dk/xmlns/diark/1.0}"

    for doc in root:

        suffix = Path(str(doc.findall(f"{ns}oFn")[0].text)).suffix

        try:
            if histogram[suffix] >= 3:
                continue

            histogram[suffix] = histogram[suffix] + 1

            path = Path(
                str(doc.findall(f"{ns}dCf")[0].text),
                str(doc.findall(f"{ns}dID")[0].text),
                str(doc.findall(f"{ns}mID")[0].text)
                + "."
                + str(doc.findall(f"{ns}aFt")[0].text),
            )
            final_path = Path(parent_folder, path)
            paths_out.append(final_path)

            key = suffix.replace(".", "")
            to_copy[key].append(final_path)
            to_copy_filename[key].append(
                str(doc.findall(f"{ns}dCf")[0].text)
                + "_"
                + str(doc.findall(f"{ns}dID")[0].text)
                + "_"
                + str(doc.findall(f"{ns}mID")[0].text)
            )

        except KeyError:
            histogram[suffix] = 1

            path = Path(
                str(doc.findall(f"{ns}dCf")[0].text),
                str(doc.findall(f"{ns}dID")[0].text),
                str(doc.findall(f"{ns}mID")[0].text)
                + "."
                + str(doc.findall(f"{ns}aFt")[0].text),
            )
            final_path = Path(parent_folder, path)
            paths_out.append(final_path)

            key = suffix.replace(".", "")
            to_copy[key] = [final_path]
            to_copy_filename[key] = [
                str(doc.findall(f"{ns}dCf")[0].text)
                + "_"
                + str(doc.findall(f"{ns}dID")[0].text)
                + "_"
                + str(doc.findall(f"{ns}mID")[0].text)
            ]


def make_dirs(output_dir):

    for suffix in to_copy.keys():
        path_out = Path(output_dir, suffix)

        try:
            os.mkdir(path_out)

            for i in range(len(to_copy[suffix])):
                print(to_copy[suffix][i])

                renamed_file = Path(
                    to_copy_filename[suffix][i] + to_copy[suffix][i].suffix
                )
                # print(renamed_file)
                path_out_full = Path(path_out, renamed_file)
                print(path_out_full)
                shutil.copy2(to_copy[suffix][i], path_out_full)

        except FileExistsError:
            print("Folder exists already...")


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

    print(args.input)
    print(args.output)

    input_dir = args.input  # Path(sys.argv[1])
    output_dir = args.output  # Path(sys.argv[2])

    if Path(input_dir).exists():
        print(input_dir)
        readXML(input_dir)
        # print(to_copy)
        # print(to_copy_filename)
        make_dirs(output_dir)
        print(histogram)
        # print(to_copy_filename)


if __name__ == "__main__":
    main()
