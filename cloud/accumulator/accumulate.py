import logging
import sys
from pathlib import Path
import glob

import pandas as pd
import fastparquet
import time
import errno
import os

# Logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Globals
COMPLETED_LIST_DIR = Path("completed_lists")
MOUNT_BUCKET_BASE = Path("/mnt/")
BUCKET_SAT_DATA = Path("satellite-data-processed")
BUCKET_EXPORT = Path("asimovs-accumulated-data")
BUCKET_PHY_DRIVERS = Path("physical-drivers-processed")


# Utils
def read_completed_list(list_path, create=True) -> list:
    """
    Reads a list from a file.

    Args:
        list_path (str): The path to the file.
        create (bool, optional): If True, creates the file if it doesn't exist. Defaults to True.

    Returns:
        list: The list read from the file.

    Raises:
        FileNotFoundError: If the file doesn't exist and create is False.
    """
    # Check if path exists
    if not os.path.exists(list_path):
        if create:
            open(list_path, "a").close()
            return []
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), list_path)

    # If so, open and return the list
    with open(list_path, "r") as f:
        return [line.rstrip("\n") for line in f]


def write_completed_list(list_path, completed_list):
    """
    Writes a list to a file.

    Args:
        list_path (str): The path to the file.
        completed_list (list): The list to be written to the file.
    """
    with open(list_path, "a") as f:
        for item in completed_list:
            f.write(item + "\n")


def sync():
    # Collect completed cache lists and append those found on the buckets

    list_names = [
        "thermo",
        "merged_omni_indices",
        "merged_omni_solar_wind",
        "merged_omni_magnetic_field",
        "goes_256nm_sw",
        "goes_284nm_sw",
        "goes_304nm_sw",
        "goes_1175nm_sw",
        "goes_1216nm_sw",
        "goes_1335nm_sw",
        "goes_1405nm_sw",
        "soho_data",
        "nrlmsise00_time_series",
    ]

    # Create an empty dictionary to store completed lists
    completed_lists = {}

    # Iterate over each name in the list_names list
    for name in list_names:
        # Read the completed list file for the current name and store it in the completed_lists dictionary
        completed_lists[name] = read_completed_list(
            Path("completed_lists") / (name + ".txt")
        )

    merge_data_paths = {}
    for name in list_names:
        match name:
            case "thermo":
                merge_data_paths[name] = glob.glob(
                    str(MOUNT_BUCKET_BASE / BUCKET_SAT_DATA / "/tudelft/*/*/*.parquet")
                )
            case "merged_omni_indices":
                merge_data_paths[name] = glob.glob(
                    str(
                        MOUNT_BUCKET_BASE
                        / BUCKET_PHY_DRIVERS
                        / "/OMNIWEB/*/indices_*.parquet"
                    )
                )
            case "merged_omni_solar_wind":
                merge_data_paths[name] = glob.glob(
                    str(
                        MOUNT_BUCKET_BASE
                        / BUCKET_PHY_DRIVERS
                        / "/OMNIWEB/*/solar_wind_velocity_*.parquet"
                    )
                )
            case "merged_omni_magnetic_field":
                merge_data_paths[name] = glob.glob(
                    str(
                        MOUNT_BUCKET_BASE
                        / BUCKET_PHY_DRIVERS
                        / "/OMNIWEB/*/magnetic_*.parquet"
                    )
                )
            # GOES
            case "soho_data":
                merge_data_paths[name] = glob.glob(
                    str(MOUNT_BUCKET_BASE / BUCKET_PHY_DRIVERS / "/SOHO/*/*.parquet")
                )
            # MSIS

    def write_chunk(path, data):
        """
        Write data to a Parquet file at the given path.

        If the file already exists, the data will be appended to it.
        If the file does not exist, a new Parquet file will be created.

        Parameters:
        - path (str): The path to the Parquet file.
        - data: The data to be written to the file.

        Returns:
        None
        """
        if os.path.exists(path):
            fastparquet.write(path, data, append=True)
        else:
            concatenated_data.to_parquet(path, engine="fastparquet")

    for name in list_names:
        if "goes" in name:
            continue

        # Check if there is data
        if len(merge_data_paths[name]) == 0:
            logging.warn(f"No files found for {name}, skipping...")
            continue

        # Grab the unprocessed changes
        unprocessed_list = [
            new for new in merge_data_paths[name] if new not in completed_lists[name]
        ]
        if len(unprocessed_list) == 0:
            logging.warn(f"No new data found for {name}, skipping...")
            continue

        logging.info(f"Processing new {len(unprocessed_list)} files for {name}.")
        existing_path = MOUNT_BUCKET_BASE / BUCKET_EXPORT / Path(name + ".parquet")

        # Chunked processing of files, rarely needed if using at daily cadance but will be if at greater
        # This script is intended to be run a low-cost VM
        c = 0
        CHUNK_SIZE = 100
        total_unprocessed = len(unprocessed_list)
        while c < total_unprocessed // CHUNK_SIZE + 1:
            a = c * CHUNK_SIZE
            b = (c + 1) * CHUNK_SIZE
            b = b if not b > total_unprocessed else total_unprocessed

            # exactly on the edge
            if a == b:
                break

            concatenated_data = pd.concat(
                [
                    pd.read_parquet(file_path, engine="fastparquet")
                    for file_path in unprocessed_list[a:b]
                ]
            )
            c += 1
            logging.info(
                f"Writing files {a}-{b}, {(b/total_unprocessed)*100:.02f}%, and updating completed cache."
            )
            write_chunk(existing_path, concatenated_data)
            write_completed_list(
                str(COMPLETED_LIST_DIR) + "/" + name + ".txt", unprocessed_list[a:b]
            )

        del concatenated_data


if __name__ == "__main__":
    time_start = time.time()
    sync()
    print("\nTotal duration: {}".format(time.time() - time_start))
    sys.exit(0)
