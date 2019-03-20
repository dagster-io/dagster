# Introduction

This module is a collection of tools for generating example production data. 

The only script right now is generate_synthetic_events, which can be run as:

    generate_synthetic_events --s3-bucket "elementl-data" --s3-prefix "events/raw" --start-date "2017-01-01" --end-date "2017-01-03" --num-files 1 --num-events-per-file 10

Due to an issue with multiprocessing, on macOS you may need to run this first (see https://bit.ly/2Of9upO):

    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

