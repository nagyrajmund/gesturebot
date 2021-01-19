import time
import sys
import urllib
import random
import datetime
import stomp
# install package stomp.py
class MessagingServer():
    """
    This class is responsible for sending messages to and receiving messages from
    the standalone ActiveMQ Broker.
    """
    def __init__(self, listener, host, port):
        """
        Initialize the network parameters.
        
        Args:
            listener:  An object that defines what to do with incoming messages. 
                       It should define at least two functions:
                            on_message(self, headers, message)
                       and
                            on_error(self, headers, message).

            host:      The hostname of the ActiveMQ connection.
            port:      The port of the ActiveMQ connection.
               
            See the stomp.py documentation for more details.

        NOTE: this class should be used with the 'with' statement, e.g.:
              
                with GestureGeneratorService(model_file, mean_pose_file) as service:
                print("Waiting for messages\n")

                while True:
                    time.sleep(0.01)
        """
        self.listener = listener
        host_and_ports = [(host, port)]
        self.conn = stomp.Connection(host_and_ports=host_and_ports)
        
    def open_network(self):
        self.conn.set_listener("", self.listener)
        self.conn.connect(username='admin', passcode='password', wait=True)
        self.conn.subscribe(destination='/topic/FROM_UNITY', id = 123)
        self.conn.auto_content_length = False

    def close_network(self):
        self.conn.disconnect()

    def send_JSON(self, msg):
        """Send the given JSON message to Unity."""
        self.conn.send(body=msg, destination='/topic/TO_UNITY')

    def send_msg(self, prefix, msg):
        msg = prefix + " " + urllib.quote_plus(msg)
        #print(msg)
        self.conn.send(body=msg, headers=self.headers, destination='/topic/DEFAULT_SCOPE')