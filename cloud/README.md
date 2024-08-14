# The data procssing pipeline

The `cloud` directory contains all the code to create the data pipeline for the FDL 2024 Thermo-CL project. 
It ingests, processes and acuumulates data from the following sources:
- GOES 
- SOHO & OMNIWEB
- celestrak and satellite indices data 
- GRACE, SWARM, CHAMP and GOCE (satellites)

The data is first ingested in it's raw format, stored on a bucket, and then processed into formats useful to the Thermo-CL projects (pandas dataframes).

The pipeline runs autonomously and continuuously accumulates data. 

## Building the pipeline
The pipeline is built using `terraform`. This README will assume you have some working knowledge of that software. 

To build the pipeline, first ensure the pipeline hasn't already been deployed. 
If it has, you need to do nothing. If it hasn't, navigate to the `cloud/deployment` directory and do the following
```
terraform init
terraform plan
terraform apply
``` 

This will automatically create the pipeline for you using `terraform`. The image below shows the scematic of the pipeline that is coded in this repository.
Note, not all resources are managed by terraform, the notable exceptions are:
- cloud shedulers 
- buckets

## Details on the data
The data-sources are split into 4 groups. Within each group, the data sources are related to one another. 
These groups are:
- "satellite data"
- "satellite indices"
- "GOES"
- "physical drivers"
Each group effectively has it's own independent pipeline, however some resources are shared between pipelines (e.g. buckets), and the "satellite data" pipeline requires inforation from the "satellite indices" pipeline. 
The sheduler is set  up such that this dependency is taken into account. 

### Satellite data
This sub-pipeline downloads and processes data from tudelft ftp server: thermosphere.tudelft.nl. This corresponds to data from the following 8 satellites:
- CHAMP
- GRACE A, B, C
- SWARM A, B, C
- GOCE

### Satellite indices
This sub-pipeline downloads and processes the celestrak and satellite indices data from https://sol.spacenvironment.net/ and https://www.celestrak.com


### GOES
This sub-pipeline downloads and processes data from the GOES satellites. There are several GOES missions, and as of 2024 only goes16 and goes18 are active. Since older GOES missions have completed, data from obsolete satellites is not continuuously collected as a copy already exists on the GCP buckets. 
Note that the GOES data is particularly sparse which affects the processing step. To fill in the missing data, a forward-fill is used to interpolate the missing data. This is done over a date-range, and the missing data can cross a year-boundary (hence why multiple years are needed). 
This complexity is manifested in the cloud function. 

The data is taken from https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/ and https://www.ncei.noaa.gov/data/goes-space-environment-monitor/access/science/euvs/


### physical drivers
The "physical drivers" correspond to data taken from SOHO and OMNIWEB. 
The SOHO data is taken from: https://lasp.colorado.edu/eve/data_access/eve_data/lasp_soho_sem_data/long/15_sec_avg/
The OMNIWEB data is taken from: https://omniweb.gsfc.nasa.gov/cgi/nx1.cg 


## The processing shedule
Note all timezones are in UTC. 

Different satellites and data sources are updated with differing frequencies. Each ingestion chain is triggered by a Cloud Scheduler (a cron job), with the following frequencies:
- satellite data (CHAMP, GRACE, SWARM, GOCE): montly
- satellite indices: daily (although the SW-data is only upaded monthly)
- GOES: monthly 
- physical drivers: daily


## Details on the directory structure
The `cloud` directory has the following (simplified) structure:
├── deployment
├── messages
└── src
    ├── goes
    ├── physical-drivers
    ├── satellite_data
    └── satellite_indices

- The `deployment` directory contains terraform code to construct the pipeline.
- The `messages` directory contains scripts that can be used by the user to directly communicate (and trigger) the cloud functions. This is normally only done for testing purpoases.
- The `src` directory contains the python code that is uploaded to the cloud functions 

Inside the `src` folder there is another directory structure, with each folder corresponding to one of the "sub-pipelines" mentioned above. 
Generally, each of these pipelines has the following steps:
- ingestion
- process 

The ingeston folder contains the cloud function to download raw data and store it to a bucket. In this step, no processing of the data is done and therefore the data remains in its original format.
The process folder contains the python code for the cloud function to process the data into formats use by the Thermo-CL team. 

The `satellite_indices` folder only has no sub-folder since both the ingestion and process steps are done in a single cloud function. 
You may also see a `messenger` folder. Some of the ingestion or processing functions are complex, and require multiple different start messages (and therefore multiple different instances of the cloud function) to do all necessary steps. The messenger function handles these messages, which then allows the messinger function itself to be triggered by a single Cloud Scheduler trigger.
