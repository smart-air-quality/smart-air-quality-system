"""
MQTT: connect, publish, reconnect with backoff, short queue when offline.
Requires: `from umqtt.simple import MQTTClient` (see iot/README.md).
"""

import time

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None


class MqttPublisher:
    def __init__(self, client_id, broker, port, user, password, queue_max, backoff_s):
        self._client_id = client_id
        self._broker = broker
        self._port = port
        self._user = user
        self._password = password
        self._queue_max = queue_max
        self._backoff = backoff_s
        self._queue = []
        self._mqtt = None
        self._fail_streak = 0

    def _disconnect(self):
        if self._mqtt is None:
            return
        try:
            self._mqtt.disconnect()
        except Exception:
            pass
        self._mqtt = None

    def _connect(self):
        if MQTTClient is None:
            return False
        self._disconnect()
        try:
            c = MQTTClient(
                self._client_id,
                self._broker,
                port=self._port,
                user=self._user,
                password=self._password,
            )
            c.connect()
            self._mqtt = c
            self._fail_streak = 0
            return True
        except Exception:
            self._mqtt = None
            self._fail_streak += 1
            return False

    def _enqueue(self, topic, payload):
        self._queue.append((topic, payload))
        while len(self._queue) > self._queue_max:
            self._queue.pop(0)

    def publish(self, topic, payload, qos=0):
        if MQTTClient is None:
            self._enqueue(topic, payload)
            return False
        if self._mqtt is None:
            self._connect()
        try:
            if self._mqtt is None:
                self._enqueue(topic, payload)
                return False
            self._mqtt.publish(topic, payload, qos=qos)
            self._drain_safe()
            return True
        except Exception:
            self._disconnect()
            self._enqueue(topic, payload)
            return False

    def _drain_safe(self):
        while self._queue:
            t, p = self._queue[0]
            try:
                if self._mqtt is None:
                    break
                self._mqtt.publish(t, p, qos=0)
                self._queue.pop(0)
            except Exception:
                self._disconnect()
                break

    def reconnect_cycle(self):
        if self._mqtt is None:
            self._connect()

    def backoff_sleep(self):
        i = min(max(self._fail_streak, 0), len(self._backoff) - 1)
        time.sleep(float(self._backoff[i]))
