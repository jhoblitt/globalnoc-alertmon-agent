# globalnoc-alertmon-agent

A package to faciltate sending alerts to the GlobalNOC AlertMon system.

# Examples

## send_active_alerts.py

In this example all active alerts are gathered from an external source and sent to AlertMon.

(examples/send_active_alerts.py)[https://github.com/GlobalNOC/globalnoc-alertmon-agent/blob/master/examples/send_active_alerts.py]

## process_events.py

In this example an http server is started to listen for events POST'd to it. On a regular interval those POST'd events are combined with the current set of active alerts.

* If an **OK** alerts is POST'd the corresponding active alert is cleared.
* To handle cases where a clear event may have been missed, alerts exceeding some time threshold are also cleared.

Then the full set of alerts are sent to the system.

(examples/process_events.py)[https://github.com/GlobalNOC/globalnoc-alertmon-agent/blob/master/examples/process_events.py]
