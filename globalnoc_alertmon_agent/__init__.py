from globalnoc import wsc
import json
from time import time
from copy import deepcopy

__version__="1.0.1"

class ConfigError(Exception):
    pass

class AgentError(Exception):
    pass

class AlertError(Exception):
    pass

class Alert:
    def __init__(
        self, 
        node_name: str, 
        service_name: str,
        description: str,
        severity: str,
        start_time: int = None,
        host_group: str = None,
        service_group: str = None,
        device: str = None,
        interface_abbr_name: str = None,
        interface_id: int = None,
        bgp_peer_id: int = None
    ):

        # do sanity checking on required parameters 
        if( len(node_name) > 255):
            raise AlertError(f"node_name must not be greater than 255 characters")

        if( len(service_name) > 255):
            raise AlertError(f"service_name must not be greater than 255 characters")

        if( len(description) > 1024 ):
            raise AlertError(f"description must not be greater than 1024 characters")

        valid_severities = ['Critical', 'Major', 'Minor', 'Unknown', 'OK' ]
        if( severity not in valid_severities ):
            raise AlertError(f"severity must be one of ({valid_severities})")

        # do sanity checking on optional parameters
        if( start_time is not None and (start_time < 0 or start_time > int(time()))  ):
            raise AlertError(f"start_time must be greater than 0 and not represent a future time ( i.e. a value greater than the current value for epoch seconds )")

        if( service_group is not None and len(service_group) > 255 ):
            raise AlertError(f"service_group must not be greater than 255 characters")
        
        if( host_group is not None and len(host_group) > 255 ):
            raise AlertError(f"host_group must not be greater than 255 characters")
        
        if( device is not None and len(device) > 255 ):
            raise AlertError(f"device must not be greater than 255 characters")
        
        if( interface_abbr_name is not None and len(interface_abbr_name) > 64 ):
            raise AlertError(f"interface_abbr_name must not be greater than 64 characters")
        
        if( interface_id is not None and (interface_id < 0 or interface_id > 2147483647) ):
            raise AlertError(f"invalid value for interface_id")
        
        if( bgp_peer_id is not None and (bgp_peer_id < 0 or bgp_peer_id > 2147483647) ):
            raise AlertError(f"invalid value for bgp_peer_id")
        

        self._alert = {
            'node_name': node_name,
            'service_name': service_name,
            'description': description,
            'severity': severity,
            'start_time': start_time,
            'service_group': service_group,
            'device': device,
            'interface_abbr_name': interface_abbr_name,
            'host_group': host_group,
            'interface_id': interface_id,
            'bgp_peer_id': bgp_peer_id
        }

    def is_older_than( self, seconds: int):
        start_time = self.get('start_time', None)

        # if start_time is None we can't no the age so return false
        if(start_time is None):
            return False

        # if the alerts age is older than the seconds passed in return true 
        if( (time() - start_time) > seconds):
            return True
        
        return False

    def get( self, key: str, default_value=None):
        if( default_value):
            return self._alert.get(key, default_value)

        return self._alert.get( key ) 
    
    def get_alert_key(self):
    
        return f"{self.get('node_name')}{self.get('service_name')}{self.get('severity')}{self.get('device', '')})"
    
    def json(self):
        json_alert = {}
        for key in self._alert.keys():
            value = self._alert[key]
            if(value is not None):
                json_alert[key] = value

        return json.dumps(json_alert) 

class AlertMonAgent:

    def __init__(self, username: str, password: str, realm: str, server: str):

        self._alerts = {}
        self._agent_details = {}

        # instantiate the webservice client object
        self._classify_client = wsc.WSC()
        self._classify_client.username = username 
        self._classify_client.password = password 
        self._classify_client.url      = f"https://{server}/classification/classification.cgi"
        self._classify_client.realm    = realm 
        self._classify_client._strict_content_type = False

        # ensure agent is registered and store agent information
        self._get_agent_info()


    def add_alert( self, alert: Alert ):
        self._alerts[alert.get_alert_key()] = alert
    
    def delete_alert( self, alert: Alert ):

        # if the alert to delete has a severity of OK delete all instances of this alert regardless of severity
        # effectively "clearing" the alert
        if( alert.get('severity') == 'OK' ):
            for severity in ['Critical', 'Major', 'Minor', 'Unknown']:
                tmp_alert = deepcopy(alert) 
                tmp_alert._alert['severity'] = severity
                if( tmp_alert.get_alert_key() in self._alerts ):
                    del self._alerts[tmp_alert.get_alert_key()]

        if( alert.get_alert_key() in self._alerts ):
            del self._alerts[alert.get_alert_key()]

    def get_alerts( self ):
        return list(self._alerts.values())

    def _get_agent_info( self ):
        alertmon_agent_details = self._classify_client.get_alertmon_agent_details()

        if( int(alertmon_agent_details.get("error", 0)) == 1):
            raise AgentError(alertmon_agent_details.get('error_text', 'Unknown error encountered attempting to retrieve AlertMon Agent information.'))

        self._agent_details = alertmon_agent_details
    
    def send_alerts(self):
        
        json_alerts = []
        for alert in self.get_alerts():
            json_alerts.append(alert.json())

        cloud = self._agent_details['cds_cloud']

        send_alerts_data = {
            'cloud':       cloud,
            'is_keyframe': 1
        }
        if( len(json_alerts) > 0):
            send_alerts_data['alert'] = json_alerts
        
        response = self._classify_client.send_alerts( **send_alerts_data )

        if( int(response.get("error", 0)) == 1):
            raise AgentError(response.get('error_text', 'Unknown error encountered attempting to send alerts.'))

    def add_current_alerts( self ):

        alerts = self.get_current_alerts()

        for alert in alerts:
            add_alert_args = {
                'node_name': alert.get('node_name'),
                'service_name': alert.get('service_name'),
                'description': alert.get('description'),
                'severity': alert.get('severity'),
                'start_time': int(alert.get('start_time')),
                'service_group': alert.get('service_group', None),
                'host_group': alert.get('host_group', None),
                'device': alert.get('device', None),
                'interface_abbr_name': alert.get('interface_abbr_name', None)
            }

            if( alert.get('interface_id', None) is not None):
                add_alert_args['interface_id'] = int(alert.get('interface_id'))

            if( alert.get('bgp_peer_id', None) is not None):
                add_alert_args['bgp_peer_id'] = int(alert.get('bgp_peer_id'))

            self.add_alert(Alert(**add_alert_args))

    def get_current_alerts( self ):

        response = self._classify_client.get_alertmon_agent_alerts(
            current_alerts = 1
        )

        if( int(response.get("error", 0)) == 1):
            raise AgentError(response.get('error_text', 'Unknown error encountered attempting to send alerts.'))

        return response['results']
