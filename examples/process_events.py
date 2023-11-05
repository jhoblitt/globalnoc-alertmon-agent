import sys

import json
import os
import http.server
import threading
import time
import yaml
import queue


from globalnoc_alertmon_agent import AlertMonAgent, Alert
    
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
config_file = script_dir+"/conf/config.yaml"
alerts_file = script_dir+"/data/send_active_alerts.yaml"

# read in config file
with open(config_file, "r") as stream:
    config = yaml.safe_load(stream)


# Define the HTTP server settings
host = '127.0.0.1'
port = 8080

alert_queue = queue.Queue()

# Create a simple HTTP request handler
class MyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        # Get the content length from the headers
        content_length = int(self.headers['Content-Length'])
        
        post_data = self.rfile.read(content_length)
        try:
            json_data = json.loads(post_data)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Successfully received and parsed alert\n'.encode('utf-8'))
            alert_queue.put_nowait(json_data)

        except json.JSONDecodeError as e:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Error parsing alert: {e}\n'.encode('utf-8'))

# Function to start the HTTP server
def start_http_server():
    with http.server.HTTPServer((host, port), MyHTTPRequestHandler) as httpd:
        print(f"HTTP server is running at http://{host}:{port}")
        httpd.serve_forever()

# Function to execute a task every five minutes
def send_alerts():
    while True:

        # sleep for 5 minutes then send our alerts 
        time.sleep(1 * 30)

        print("Sending Alerts...")

        # initialize the alertmon agent 
        agent = AlertMonAgent(
            username    = config.get('username'),
            password    = config.get('password'),
            server      = config.get('server'),
            realm       = config.get('realm')
        )

        # start with the alerts currently added in our system
        agent.add_current_alerts()

        # add alerts that we've queued up until there are no more remaining or we've reached 250
        alerts_processed = 0 
        while alert_queue.qsize() > 0 and alerts_processed <= 250:
            alert_msg = alert_queue.get()
            alert_queue.task_done()
            
            alert = Alert(
                node_name    = alert_msg.get('node_name'),
                service_name = alert_msg.get('service_name'),
                description  = alert_msg.get('description'),
                severity     = alert_msg.get('severity')
            )

            # if this alert is OK ( i.e. it has cleared ) delete any active alert that might exist
            if( alert.get('severity') == 'OK'):
                agent.delete_alert(alert)

            # otherwise add the alert to our agent's list of alerts to send
            else:
                agent.add_alert(alert)

            alerts_processed += 1

        # expire event based alerts based on time
        for alert in agent.get_alerts():
            if( alert.is_older_than(seconds=250) ):
                agent.delete_alert( alert )

        agent.send_alerts()



def main():

    # Create and start the HTTP server thread
    http_server_thread = threading.Thread(target=start_http_server)
    http_server_thread.start()

    # Create and start the task execution thread
    send_alerts_thread = threading.Thread(target=send_alerts)
    send_alerts_thread.start()

    # Wait for the threads to finish
    http_server_thread.join()
    send_alerts_thread.join()


main()