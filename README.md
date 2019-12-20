# ActiveMQ Integration Pack

Pack which allows integration with [ActiveMQ](https://activemq.apache.org/).

## Configuration

Configuration is required to use the ActiveMQ sensor. Copy the example configuration 
in [activemq.yaml.example](./activemq.yaml.example) to `/opt/stackstorm/configs/activemq.yaml`
and edit as required.

* ``host`` - ActiveMQ host to connect to.
* ``username`` - Username to connect to ActiveMQ.
* ``password`` - Password to connect to ActiveMQ.
* ``topics`` - List of topics to check for messages. See an example below.
* ``queues`` - List of queues to check for messages. See an example below.
* ``deserialization_method`` - Which method to use to de-serialize the
  message body. By default, no deserialization method is specified which means
  the message body is left as it is. Valid values are ``json`` and ``pickle``.

You can also use dynamic values from the datastore. See the
[docs](https://docs.stackstorm.com/reference/pack_configs.html) for more info.

You can specify multiple queues using this syntax:

```yaml
sensor_config:
  activemq_queue_sensor:
    tpoics:
      - topic1
      - topic2
    queues:
      - queue1
      - queue2
      - ....
```


## Sensors

* ``new_message`` - Sensor that triggers a activemq.new_message with a payload containing the queue and the body


