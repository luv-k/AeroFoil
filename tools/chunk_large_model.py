import argparse
import os
import re
from pathlib import Path

BUFFER_SIZE = 8 * 1024 * 1024
DEFAULT_CHUNK_SIZE = 1024**3
PART_PATTERN = re.compile(r"part-(\d+)\.part$")


def split_file(source: Path, destination: Path, chunk_size: int) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"Chunk directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    index = 0
    with source.open("rb") as input_file:
        while True:
            part_path = destination / f"part-{index:04d}.part"
            written = 0
            with part_path.open("xb") as part_file:
                while written < chunk_size:
                    block = input_file.read(min(BUFFER_SIZE, chunk_size - written))
                    if not block:
                        break
                    part_file.write(block)
                    written += len(block)
            if written == 0:
                part_path.unlink()
                break
            index += 1
            if written < chunk_size:
                break

    print(f"Created {index} chunks in {destination}")


def join_parts(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise NotADirectoryError(source)

    indexed_parts = []
    for part in source.iterdir():
        match = PART_PATTERN.fullmatch(part.name)
        if match and part.is_file():
            indexed_parts.append((int(match.group(1)), part))
    indexed_parts.sort(key=lambda item: item[0])

    if not indexed_parts:
        raise FileNotFoundError(f"No model chunks found in {source}")
    if [index for index, _ in indexed_parts] != list(range(len(indexed_parts))):
        raise ValueError("Chunk sequence has missing or duplicate indexes.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(temporary)

    with temporary.open("xb") as output_file:
        for _, part in indexed_parts:
            with part.open("rb") as part_file:
                while block := part_file.read(BUFFER_SIZE):
                    output_file.write(block)
    os.replace(temporary, destination)

    print(f"Reassembled {len(indexed_parts)} chunks into {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split and reassemble large binary model files.")
    commands = parser.add_subparsers(dest="command", required=True)

    split_command = commands.add_parser("split")
    split_command.add_argument("source", type=Path)
    split_command.add_argument("destination", type=Path)
    split_command.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)

    join_command = commands.add_parser("join")
    join_command.add_argument("source", type=Path)
    join_command.add_argument("destination", type=Path)

    arguments = parser.parse_args()
    if arguments.command == "split":
        split_file(arguments.source, arguments.destination, arguments.chunk_size)
    else:
        join_parts(arguments.source, arguments.destination)


if __name__ == "__main__":
    main()
