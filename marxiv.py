#!/usr/bin/env python
"""Downloads arXiv source and outputs to Markdown"""
import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
from urllib.request import urlopen
from urllib.error import HTTPError
from http.client import HTTPResponse


def find_main_latex_file(directory: str) -> str | None:
    """Choose a likely contender for the main LaTeX source file

    - Being named 'main.tex' is a plus
    - Containing 'documentclass' is another
    - Including lots of other files is too

    Args:
      directory: Where to search for .tex files

    Returns the path of the best choice, or None if there is none.
    """
    candidates = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".tex"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()
                    heuristic1 = "main" in file.lower()
                    heuristic2 = "\\documentclass" in content
                    heuristic3 = \
                        content.count("\\input") + content.count("\\include")

                    candidates.append(
                        (file_path, heuristic1, heuristic2, heuristic3)
                    )

    # Sort based on the number of heuristics passed and the heuristic3 score
    candidates.sort(key=lambda x: (sum(x[1:3]), x[3]), reverse=True)
    return candidates[0][0] if candidates else None


def fetch_url(url: str) -> HTTPResponse:
    """Fetch URL using standard library"""
    try:
        response: HTTPResponse = urlopen(url)
    except HTTPError as err:
        print(f"Failed to download source: {repr(err)}")
        raise err
    return response


def get_extension(filetype: str) -> str:
    """Return a filetype's extension"""
    match filetype:
        case 'markdown' | 'mardown_mmd' | 'gfm':
            return 'md'
        case _:
            return 'txt'


def download_arxiv_source(arxiv_id: str, output_dir: str) -> str | None:
    """Download source files for the given arXiv ID

    Args:
      arxiv_id: The arXiv ID of the article.
      output_dir: The directory where the source files will be saved.

    Returns the path to the downloaded file or None if the download fails.
    """
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    response = fetch_url(url)

    if response.status == 200:
        file_name = f"{arxiv_id}.tar.gz"
        file_path = os.path.join(output_dir, file_name)

        with tarfile.open(fileobj=response, mode="r|*") as tar:
            tar.extractall(path=output_dir)

        return file_path

    print(f"Error downloading source files for arXiv:{arxiv_id}")
    return None


def convert_to_markdown(
        source_file: str, working_dir: str, output_file: str = '', output_format: str = "gfm"
) -> None:
    """Convert LaTeX file to Markdown using Pandoc

    Args:
      source_file: Path to the source file
      output_file: Path for output file
      output_format (optional): Use format besides Markdown
    """
    args = ["pandoc", "-s", source_file, "-t", output_format, "--wrap=none"]
    if output_file:
        destination = os.path.join(os.getcwd(), output_file)
        args += ["-o", destination]
    subprocess.run(args, cwd=working_dir)


def main():
    """Run script based on CLI args"""
    parser = argparse.ArgumentParser(
        description="Fetch and convert arXiv article source to Markdown"
    )
    parser.add_argument("arxiv_id", help="The arXiv ID of the article.")
    parser.add_argument(
        "-f",
        "--format",
        help="Desired output format",
        default="markdown",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        help="The output filename. Defaults to stdout",
        default=None,
    )

    args = parser.parse_args()

    output_file = args.output_file
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            source_contents = download_arxiv_source(args.arxiv_id, temp_dir)
        except tarfile.ReadError:
            print(f"Error: Couldn't fetch source for arXiv:{args.arxiv_id}")
            sys.exit(1)

        main_file = find_main_latex_file(temp_dir) or source_contents

        if main_file:
            convert_to_markdown(main_file, temp_dir, output_file, args.format)
            if output_file:
                print(f"Converted arXiv:{args.arxiv_id} to '{output_file}'",
                      file=sys.stderr)
            else:
                print(f"Fetched arXiv:{args.arxiv_id}", file=sys.stderr)
        else:
            print(f"Couldn't find source for arXiv:{args.arxiv_id}.")
            sys.exit(1)


if __name__ == "__main__":
    main()
