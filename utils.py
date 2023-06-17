#!/usr/bin/env python3
import os
import sys
import csv
import json
import requests
import subprocess

# simple key sort
def sort_json_files():
    for i in os.listdir("."):
        if i.endswith(".json"):
            with open(i, "r") as f:
                data = json.load(f)
            with open(i, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)



def convert_csv(file, has_headers=False):
    for i in os.listdir("."):
        if i.endswith(".csv"):
            with open(i, "r") as f:
                csv_reader = csv.DictReader(f)
                line_count = 0
                data = []
                for row in csv_reader:
                    data.append(row)
                    line_count += 1
                print(f'Processed {line_count} lines.')
            with open(i, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)


def download_progress(url, fn):
    with open(fn, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')

        if total is None:
            f.write(r.content)
        else:
            downloaded = 0
            total = int(total)
            for data in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write(f"\rDownloading {fn}: [{'#' * done}{'.' * (50-done)}] {done*2}%")
                sys.stdout.flush()
    sys.stdout.write('\n')
    return r


def preexec(): # Don't forward signals.
    os.setpgrp()

def launch(launch_params, log_output):
    subprocess.Popen(launch_params, stdout=log_output, stderr=log_output, universal_newlines=True, preexec_fn=preexec)