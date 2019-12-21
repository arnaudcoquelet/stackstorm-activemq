import json
import pickle

from proton import Message
from proton.handlers import MessagingHandler, EndpointStateHandler
from proton.reactor import Container, DynamicNodeProperties, DurableSubscription
import urllib
from urlparse import urlparse

import eventlet

from st2reactor.sensor.base import Sensor

DESERIALIZATION_FUNCTIONS = {
    'json': json.loads,
    'pickle': pickle.loads
}


class ActiveMQTopicSensor(Sensor):
    """Sensor which monitors a ActiveMQ topics for new messages

    This is a ActiveMQ Topic sensor i.e. it works on the simplest ActiveMQ
    messaging model.

    It is capable of simultaneously consuming from multiple queues. Each message is
    dispatched to stackstorm as a `activemq.new_message` TriggerInstance.
    """

    def __init__(self, sensor_service, config=None):
        super(ActiveMQTopicSensor, self).__init__(
            sensor_service=sensor_service, config=config)

        self._logger = self._sensor_service.get_logger(
            name=self.__class__.__name__)
        self.hosts = self._config['sensor_config']['hosts']
        if not isinstance(self.hosts, list):
            self.hosts = [self.hosts]

        self.username = self._config['sensor_config']['username']
        self.password = self._config['sensor_config']['password']

        self.urls = []
        for host in hosts:
            self.urls.append("{}:{}@{}:{}".format(
                self.username, self.password, host, self.port))

        topic_sensor_config = self._config['sensor_config']['activemq_topic_sensor']
        self.topics = topic_sensor_config['topics']
        if not isinstance(self.topics, list):
            self.topics = [self.topics]
        self.deserialization_method = topic_sensor_config['deserialization_method']

        supported_methods = DESERIALIZATION_FUNCTIONS.keys()
        if self.deserialization_method and self.deserialization_method not in supported_methods:
            raise ValueError('Invalid deserialization method specified: %s' %
                             (self.deserialization_method))

        self.receiver = None

    def start_receiver():
        Container(self.receiver).run()

    def run(self):
        self._logger.info(
            'Start consuming messages from ActiveMQ for {}'.format(self.topics))

        # run in an eventlet in-order to yield correctly
        gt = eventlet.spawn(self.start_receiver)
        # wait else the sensor will quit
        gt.wait()

    def cleanup(self):
        if self.receiver:
            self.receiver.close()

    def setup(self):
        def callback(payload):
            self._dispatch_trigger(payload)

        # Create Receiver
        self.receiver = Client(self.urls,
                               self.username,
                               self.password,
                               port=5672,
                               topics=self.topics,
                               callback=callback
                               )

    def _dispatch_trigger(self, payload):
        self._logger.debug('Received message {}'.format(topic))
        try:
            self._sensor_service.dispatch(
                trigger="rabbitmq.new_message", payload=payload)
        except:
            pass

    def update_trigger(self, trigger):
        pass

    def add_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass

    def _deserialize_body(self, body):
        if not self.deserialization_method:
            return body

        deserialization_func = DESERIALIZATION_FUNCTIONS[self.deserialization_method]

        try:
            body = deserialization_func(body)
        except Exception:
            pass

        return body


class Client(MessagingHandler):
    def __init__(self, ips=[], username=None, password=None, port=5672, topics=[], callback=None):
        super(Client, self).__init__()
        self.username = urllib.quote("{}".format(username))
        self.password = urllib.quote("{}".format(password))
        self.port = port
        self.urls = []
        for ip in ips:
            self.urls.append("{}:{}@{}:{}".format(
                self.username, self.password, ip, self.port))

        self.topicName = "topic://topic/CNAMessages"
        self.queueName = "queue://queue/CNAQueue"
        self.durable = True

        self.conn = None
        self.receiver = None

        self.callback = callback

    def on_start(self, event):
        print "Creating connection"
        self.conn = event.container.connect(urls=self.urls, heartbeat=1000)

        options = None
        if self.durable:
            options = DurableSubscription()

        print "Start listening"
        self.receiver = event.container.create_receiver(
            self.conn, self.topicName, options=options)

    def on_message(self, event):
        body = event.message.body
        topic = event.message.topic
        payload = {"topic": topic, "body": body}
        # print "New Message:\n{}".format(body)

        if self.callback:
            self.callback(payload)

    def on_connection_closed(self, event):
        # print "Closing connecttion"
        if self.receiver:
            self.receiver.close()

    def close(self):
        if self.receiver:
            self.receiver.close()
