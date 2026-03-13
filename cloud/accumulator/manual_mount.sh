# Only use this if the mounting via /etc/fstab has failed.

sudo mount -t gcsfuse -o allow_other,file_mode=777,dir_mode=777,implicit_dirs physical-drivers-processed /mnt/physical-drivers-processed
sudo mount -t gcsfuse -o allow_other,file_mode=777,dir_mode=777,implicit_dirs satellite-data-processed /mnt/satellite-data-processed
sudo mount -t gcsfuse -o allow_other,file_mode=777,dir_mode=777,implicit_dirs asimovs-accumulated-data /mnt/asimovs-accumulated-data
