from ftplib import FTP
import datetime
import os
from glob import glob
import zipfile
import ftplib
from pathlib import Path


def unzip_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.zip'):
                print(file, file.endswith('.zip'))
                file_path = os.path.join(root, file)
                extract_dir = os.path.join(root, 'unzipped')

                # Check if the directory already exists
                if os.path.exists(os.path.join(extract_dir, file[:-4])):
                    print(f"Skipping {file_path} as it is already unzipped.")
                    continue

                try:
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    print(f"Unzipped {file_path} in {extract_dir}")
                except zipfile.BadZipFile:
                    print(f"Bad zip file: {file_path}, will not unzip.")
                    continue


class TUDelftThermoFTP:

    def __init__(self):

        # connect to the FTP server
        self.ftp = FTP('thermosphere.tudelft.nl')
        self.ftp.login()
        self.ftp.set_pasv(True)

    def is_ftp_directory(self, item) -> bool:
        """ Check if an item is a directory on the FTP server. """
        original_cwd = self.ftp.pwd()
        try:
            self.ftp.cwd(item)
            self.ftp.cwd(original_cwd)
            return True
        except Exception:
            return False

    def download_directory(self, path, local_dir, files_to_download):

        print(path)
        self.ftp.cwd(path)
        print(f"Changed directory to {path}")
        successfully_downloaded = []

        for file in files_to_download:
            local_path = os.path.join(local_dir, file)
            if self.is_ftp_directory(file):
                successfully_downloaded += self.download_directory(
                    file, local_path)
            else:
                if os.path.exists(local_path):
                    print(f"File already exists: {local_path}, skipping download. ", end="\r")
                else:
                    try:
                        with open(local_path, 'wb') as f:
                            self.ftp.retrbinary(f"RETR {file}", f.write)
                            print(f"Downloaded file: {file}                       ", end="\r")
                            successfully_downloaded.append(file)
                    except ftplib.error_perm:
                        print(f"Cannot download: {file}                       ", end="\r")

        # Return to the parent directory on FTP and local file system
        self.ftp.cwd("..")
        os.chdir(os.path.dirname(local_dir))
        print("")
        return successfully_downloaded

    def list_files(self, path) -> list[str]:
        """ List all files in a directory on the FTP server. """
        self.ftp.cwd(path)
        files = self.ftp.nlst()
        return sorted(files)


def download_data(local_base_dir, starting_ftp_directory, existing_files) -> list[str]:
    """
    Args:
        - local_base_dir: string, local directory to save files
        - starting_directory: string, directory to start downloading from on the FTP server
        - existing_files: list of files that have already been downloaded
    Returns:
        - list of new files that have been downloaded.
    """

    # Make sure the local directory exists
    try:
        os.makedirs(local_base_dir, exist_ok=True)
    except OSError:
        pass

    # Connect to the FTP server
    start = datetime.datetime.now()
    thermo_downloader = TUDelftThermoFTP()

    # Get the list of files in the starting directory
    # remove any "license" files in this data directory
    remote_files = thermo_downloader.list_files(starting_ftp_directory)
    remote_files = [
        file for file in remote_files if 'license' not in file.lower()]
    print(f"Found {len(remote_files)} files on the remote server.")
    print(f"There are {len(existing_files)} files already downloaded.")

    # print(remote_files[0:10])
    # print(existing_files[0:10])

    # Snip off any directory paths from the existing files
    existing_files = [os.path.basename(file) for file in existing_files]

    # Remove files that have already been downloaded
    files_to_download = list(set(remote_files) - set(existing_files))

    print(f"There are {len(files_to_download)} files to download.")
    if files_to_download == 0:
        return []

    # Now download the remaining data
    files_downloaded = thermo_downloader.download_directory(
        starting_ftp_directory, local_base_dir, files_to_download)

    print("Files downloaded:")
    print(files_downloaded)

    # ftp.quit()

    end = datetime.datetime.now()
    diff = end - start
    print(f'All files downloaded in {diff.seconds}s')

    return sorted(files_downloaded)


def main():

    # Local directory to save files (use absolute path!)
    home = str(Path.home())
    local_base_dir = f'{home}/data/raw/champ'
    print(f"Will write download data to {local_base_dir}")

    existing_files = sorted(glob(f"{local_base_dir}/*"))

    # # Directory to start downloading from (empty if the objective is to download everything)
    # # WJF: downloads ALL data in this directory -- unknown how to get only files in a date range.
    starting_directory = '/version_02/CHAMP_data'
    download_data(local_base_dir, starting_directory, existing_files)

    # unzip lal files will create a new directory 'unzipped' in the same directory as supplied to the function
    # unzip_all_files(local_base_dir)


if __name__ == "__main__":
    main()
