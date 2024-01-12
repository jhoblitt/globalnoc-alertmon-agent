#!/usr/bin/python3

import sys

import os
import yaml
import requests

from globalnoc_alertmon_agent import AlertMonAgent, Alert

script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
config_file = script_dir+"/conf/config.yaml"

# read in config file
with open(config_file, "r") as stream:
    config = yaml.safe_load(stream)

def sanitize_severity(severity):
    s = 'Unknown'

    # match statement doesn't seem to have an easy way to do case insensitive matching, so we force everything to lower case.
    match severity.lower():
        case 'critical': s = 'Critical'
        case 'major' | 'warning': s ='Major'
        case 'minor' | 'info': s = 'Minor'
        case 'unknown': s = 'Unknown'
        case 'ok': s ='Ok'

    print(f'severity: {severity}, s: {s}')
    return s

def main():
    # initialize the alertmon agent
    agent = AlertMonAgent(
        username    = config.get('username'),
        password    = config.get('password'),
        server      = config.get('server'),
        realm       = config.get('realm')
    )

    alerts = get_active_alerts()

    for alert in alerts:
        data = {
            'node_name': alert['labels'].get('pod', 'Unknown'),
            'service_name': alert['labels'].get('alertname', 'Unknown'),
            'severity': sanitize_severity(alert['labels'].get('severity', 'Unknown')),
            'description': alert['annotations'].get('description', 'Unknown'),
            'start_time': alert.get("activeAt", None),
        }

        agent.add_alert(Alert(
            start_time   = data.get('start_time', None),
            node_name    = data.get('node_name'),
            service_name = data.get('service_name'),
            description  = data.get('description'),
            severity     = data.get('severity')
        ))

    agent.send_alerts()


def get_active_alerts():
    r = requests.get('https://prometheus.ayekan.ls.lsst.org/api/v1/alerts')
    return r.json()['data']['alerts']

main()
