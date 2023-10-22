import sys

import os
import yaml


from globalnoc_alertmon_agent import AlertMonAgent, Alert
    
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
config_file = script_dir+"/conf/config.yaml"
alerts_file = script_dir+"/data/send_active_alerts.yaml"

# read in config file
with open(config_file, "r") as stream:
    config = yaml.safe_load(stream)

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
        
        agent.add_alert(Alert(
            start_time   = alert.get('start_time', None),
            node_name    = alert.get('node_name'),
            service_name = alert.get('service_name'),
            description  = alert.get('description'),
            severity     = alert.get('severity')
        ))

    agent.send_alerts()


def get_active_alerts():
    with open(alerts_file, "r") as stream:
        alerts = yaml.safe_load(stream)

    return alerts

main()
