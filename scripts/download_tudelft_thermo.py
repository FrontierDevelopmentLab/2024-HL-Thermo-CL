from ftplib import FTP
import datetime
import os
from glob import glob
import zipfile

def is_directory(ftp, item):
    """ Check if an item is a directory on the FTP server. """
    original_cwd = ftp.pwd()
    try:
        ftp.cwd(item)
        ftp.cwd(original_cwd)
        return True
    except Exception:
        return False
    
# Function to download files and directories recursively
# Function to download files and directories recursively

# Function to download files and directories recursively
def download_directory(ftp, path, local_dir):
    try:
        os.makedirs(local_dir, exist_ok=True)  # Ensure local directory exists
        ftp.cwd(path)
        print(f"Changed directory to {path}")
    except OSError:
        pass

    files = ftp.nlst()

    for file in files:
        local_path = os.path.join(local_dir, file)
        if is_directory(ftp, file):
            download_directory(ftp, file, local_path)
        else:
            if os.path.exists(local_path):
                print(f"File already exists: {local_path}, skipping download.                       ",end="\r")
            else:
                try:
                    with open(local_path, 'wb') as f:
                        ftp.retrbinary(f"RETR {file}", f.write)
                        print(f"Downloaded file: {file}                       ",end="\r")
                except ftplib.error_perm:
                    print(f"Cannot download: {file}                       ",end="\r")
    # Return to the parent directory on FTP and local file system
    ftp.cwd("..")
    os.chdir(os.path.dirname(local_dir))
start = datetime.datetime.now()
ftp = FTP('thermosphere.tudelft.nl')
ftp.login()
#passive mode
ftp.set_pasv(True)

# Directory to start downloading from (empty if the objective is to download everything)
starting_directory = ''

# Local directory to save files
local_base_dir = '/home/jupyter/tudelft_data'

# Download all files and directories recursively from 'version_02'
download_directory(ftp, starting_directory, local_base_dir)

ftp.quit()

end = datetime.datetime.now()
diff = end - start
print(f'All files downloaded for {diff.seconds}s')

def unzip_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.zip'):
                file_path = os.path.join(root, file)
                extract_dir = os.path.join(root, 'unzipped')
                
                # Check if the directory already exists
                if os.path.exists(os.path.join(extract_dir,file[:-4])):
                    print(f"Skipping {file_path} as it is already unzipped.")
                    continue
                
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"Unzipped {file_path} in {extract_dir}")

directory = 'tudelft_data'  # Replace this with your directory path
unzip_all_files(directory)