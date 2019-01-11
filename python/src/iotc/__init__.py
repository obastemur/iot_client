# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

__version__ = "0.1.0"
__name__    = "iotc"

import sys

gIsMicroPython = ('implementation' in dir(sys)) and ('name' in dir(sys.implementation)) and (sys.implementation.name == 'micropython')

try:
  import urllib
except ImportError:
  print("ERROR: missing dependency `micropython-urllib`")
  print("Try micropython -m upip install micropython-urequests ",
        "micropython-time micropython-urllib.parse",
        "micropython-json micropython-hashlib",
        "micropython-hmac micropython-base64",
        "micropython-threading micropython-ssl",
        "micropython-umqtt.simple micropython-socket micropython-urequests"
        )
  sys.exit()

http = None
if gIsMicroPython == False:
  try:
    import httplib2 as http
  except ImportError:
    print("ERROR: missing dependency httplib2")
    sys.exit()
else:
  try:
    import urequests
  except ImportError:
    print("ERROR: missing dependency micropython-urequests")
    sys.exit()

try:
  import time
except ImportError:
  print("ERROR: missing dependency `micropython-time`")
  sys.exit()

if gIsMicroPython:
  try:
    import usocket
  except ImportError:
    print("ERROR: missing dependency `micropython-usocket`")
    sys.exit()

try:
  import json
except ImportError:
  print("ERROR: missing dependency `micropython-json`")
  sys.exit()

try:
  import hashlib
except ImportError:
  print("ERROR: missing dependency `micropython-hashlib`")
  sys.exit()

try:
  import hmac
except ImportError:
  print("ERROR: missing dependency `micropython-hmac`")
  sys.exit()

try:
  import base64
except ImportError:
  print("ERROR: missing dependency `micropython-base64`")
  sys.exit()

try:
  import ssl
except ImportError:
  print("ERROR: missing dependency `micropython-ssl`")
  sys.exit()

try:
  from threading import Timer
except ImportError:
  try:
    from threading import Thread
  except ImportError:
    print("ERROR: missing dependency `micropython-threading`")
    sys.exit()

try:
  import binascii
except ImportError:
  import ubinascii

mqtt = None
try:
  import paho.mqtt.client as mqtt
  MQTT_SUCCESS = mqtt.MQTT_ERR_SUCCESS
except ImportError:
  try:
    from umqtt.simple import MQTTClient
  except ImportError:
    if gIsMicroPython == True:
      print("ERROR: missing dependency `micropython-umqtt.simple`")
    else:
      print("ERROR: missing dependency `paho-mqtt`")

def _createMQTTClient(__self, username, passwd):
  if mqtt != None:
    __self._mqtts = mqtt.Client(client_id=__self._deviceId, protocol=mqtt.MQTTv311)
    __self._mqtts.on_connect = __self._on_connect
    __self._mqtts.on_message = __self._on_message
    __self._mqtts.on_log = __self._on_log
    __self._mqtts.on_publish = __self._on_publish
    __self._mqtts.on_disconnect = __self._on_disconnect
    __self._mqtts.username_pw_set(username=username, password=passwd)
    __self._mqtts.tls_set(ca_certs=_get_cert_path(), certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1, ciphers=None)
    __self._mqtts.tls_insecure_set(False)

    __self._mqtts.connect_async(__self._hostname, port=8883, keepalive=120)
    __self._mqtts.loop_start()
  else:
    __self._mqtts = MQTTClient(__self._deviceId, __self._hostname, port=8883, user=username, password=passwd, keepalive=0, ssl=True, ssl_params={})
    __self._mqtts.set_callback(__self._mqttcb)
    __self._mqtts.connect()

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

class HTTP_PROXY_OPTIONS:
  def __init__(self, host_address, port, username, password):
    self._host_address = host_address
    self._port = port
    self._username = username
    self._password = password

class IOTCallbackInfo:
  def __init__(self, client, eventName, payload, tag, status, msgid):
    self._client = client
    self._eventName = eventName
    self._payload = payload
    self._tag = tag
    self._status = status
    self._responseCode = None
    self._responseMessage = None
    self._msgid = msgid

  def setResponse(self, responseCode, responseMessage):
    self._responseCode = responseCode
    self._responseMessage = responseMessage

  def getClient(self):
    return self._client

  def getEventName(self):
    return self._eventName

  def getPayload(self):
    return self._payload

  def getTag(self):
    return self._tag

  def getStatusCode(self):
    return self._status

  def getResponseCode(self):
    return self._responseCode

  def getResponseMessage(self):
    return self._responseMessage

  def getMessageId(self):
    return self._msgid

class IOTConnectType:
  IOTC_CONNECT_SYMM_KEY  = 1
  IOTC_CONNECT_X509_CERT = 2

class IOTProtocol:
  IOTC_PROTOCOL_MQTT = 1
  IOTC_PROTOCOL_AMQP = 2
  IOTC_PROTOCOL_HTTP = 4

class IOTLogLevel:
  IOTC_LOGGING_DISABLED =  1
  IOTC_LOGGING_API_ONLY =  2
  IOTC_LOGGING_ALL      = 16

class IOTConnectionState:
  IOTC_CONNECTION_EXPIRED_SAS_TOKEN    =  1
  IOTC_CONNECTION_DEVICE_DISABLED      =  2
  IOTC_CONNECTION_BAD_CREDENTIAL       =  4
  IOTC_CONNECTION_RETRY_EXPIRED        =  8
  IOTC_CONNECTION_NO_NETWORK           = 16
  IOTC_CONNECTION_COMMUNICATION_ERROR  = 32
  IOTC_CONNECTION_OK                   = 64

class IOTMessageStatus:
  IOTC_MESSAGE_ACCEPTED  = 1
  IOTC_MESSAGE_REJECTED  = 2
  IOTC_MESSAGE_ABANDONED = 4

gLOG_LEVEL = IOTLogLevel.IOTC_LOGGING_DISABLED
gEXPIRES = 21600 # 6 hours

def LOG_IOTC(msg, level=IOTLogLevel.IOTC_LOGGING_API_ONLY):
  global gLOG_LEVEL
  if gLOG_LEVEL > IOTLogLevel.IOTC_LOGGING_DISABLED:
    if level <= gLOG_LEVEL:
      print(time.time(), msg)
  return 0

def MAKE_CALLBACK(client, eventName, payload, tag, status, msgid = None):
  LOG_IOTC("- iotc :: MAKE_CALLBACK :: " + eventName, IOTLogLevel.IOTC_LOGGING_ALL)
  try:
    obj = client["_events"]
  except:
    obj = client._events

  if obj[eventName] != None:
    cb = IOTCallbackInfo(client, eventName, payload, tag, status, msgid)
    obj[eventName](cb)
    return cb
  return 0

def _quote(a,b):
  global gIsMicroPython
  features = dir(urllib)
  if gIsMicroPython == False and int(sys.version[0]) < 3:
    return urllib.quote(a, safe=b)
  else:
    return urllib.parse.quote(a)

def _get_cert_path():
  file_path = __file__[:len(__file__) - len("__init__.py")]
  # check for .py(c) diff
  file_path = file_path[:len(file_path) - 1] if file_path[len(file_path) - 1:] == "_" else file_path
  LOG_IOTC("- iotc :: _get_cert_path :: " + file_path, IOTLogLevel.IOTC_LOGGING_ALL)
  return file_path + "baltimore.pem"

def _request(device, target_url, method, body, headers):
  content = None
  if http != None:
    response, content = http.Http(disable_ssl_certificate_validation=not device._sslVerificiationIsEnabled).request(
        target_url,
        method,
        body,
        headers)
  else:
    response = urequests.request(method, target_url, data=body, headers=headers)
    content = response.text

  return content

class Device:
  def __init__(self, scopeId, keyORCert, deviceId, credType):
    self._mqtts = None
    self._loopInterval = 2
    self._mqttConnected = False
    self._deviceId = deviceId
    self._scopeId = scopeId
    self._keyORCert = keyORCert
    self._credType  = credType
    self._hostname = None
    self._auth_response_received = None
    self._messages = {}
    self._loopTry = 0
    self._protocol = IOTProtocol.IOTC_PROTOCOL_MQTT
    self._dpsEndPoint = "global.azure-devices-provisioning.net"
    self._modelData = None
    self._sslVerificiationIsEnabled = True
    self._dpsAPIVersion = "2018-11-01"
    self._events = {
      "MessageSent": None,
      "ConnectionStatus": None,
      "Command": None,
      "SettingUpdated": None
    }

  def setSSLVerification(self, is_enabled):
    if self._auth_response_received:
      LOG_IOTC("ERROR: setSSLVerification should be called before `connect`")
      return 1
    self._sslVerificiationIsEnabled = is_enabled
    return 0

  def setProtocol(self, protocol):
    LOG_IOTC("ERROR: Python client currently only supports MQTT")
    return 1

  def setModelData(self, data):
    LOG_IOTC("- iotc :: setModelData :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    if self._auth_response_received:
      LOG_IOTC("ERROR: setModelData should be called before `connect`")
      return 1

    if type(data) is str:
      self._modelData = data
    else:
      self._modelData = json.dumps(data)
    self._dpsAPIVersion = "2019-01-15"
    return 0

  def setDPSEndpoint(self, endpoint):
    LOG_IOTC("- iotc :: setDPSEndpoint :: " + endpoint, IOTLogLevel.IOTC_LOGGING_ALL)

    if self._auth_response_received:
      LOG_IOTC("ERROR: setDPSEndpoint should be called before `connect`")
      return 1

    self._dpsEndPoint = endpoint
    return 0

  def setLogLevel(self, logLevel):
    global gLOG_LEVEL
    if logLevel < IOTLogLevel.IOTC_LOGGING_DISABLED or logLevel > IOTLogLevel.IOTC_LOGGING_ALL:
      LOG_IOTC("ERROR: (setLogLevel) invalid argument. ERROR:0x0001")
      return 1
    gLOG_LEVEL = logLevel
    return 0

  def _computeDrivedSymmetricKey(self, secret, regId):
    global gIsMicroPython
    try:
      secret = base64.b64decode(secret)
    except:
      LOG_IOTC("ERROR: broken base64 secret => `" + secret + "`")
      sys.exit()

    if gIsMicroPython == False:
      return base64.b64encode(hmac.new(secret, msg=regId.encode('utf8'), digestmod=hashlib.sha256).digest())
    else:
      return base64.b64encode(hmac.new(secret, msg=regId.encode('utf8'), digestmod=hashlib._sha256.sha256).digest())

  def _loopAssign(self, operationId, headers):
    uri = "https://%s/%s/registrations/%s/operations/%s?api-version=%s" % (self._dpsEndPoint, self._scopeId, self._deviceId, operationId, self._dpsAPIVersion)
    LOG_IOTC("- iotc :: _loopAssign :: " + uri, IOTLogLevel.IOTC_LOGGING_ALL)
    target = urlparse(uri)

    content = _request(self, target.geturl(), "GET", None, headers)
    data = json.loads(content)

    if data != None and 'status' in data:
      if data['status'] == 'assigning':
        time.sleep(3)
        if self._loopTry < 20:
          self._loopTry = self._loopTry + 1
          return self._loopAssign(operationId, headers)
        else:
          LOG_IOTC("ERROR: Unable to provision the device.") # todo error code
          data = "Unable to provision the device."
          return 1
      elif data['status'] == "assigned":
        state = data['registrationState']
        hostName = state['assignedHub']
        return self._mqttConnect(None, hostName)
    else:
      data = str(data)

    return self._mqttConnect("DPS L => " + str(data), None)

  def _on_connect(self, client, userdata, _, rc):
    LOG_IOTC("- iotc :: _on_connect :: rc = " + str(rc), IOTLogLevel.IOTC_LOGGING_ALL)
    if rc == 0:
      self._mqttConnected = True
    self._auth_response_received = True

  def _echoDesired(self, msg, topic):
    LOG_IOTC("- iotc :: _echoDesired :: " + topic, IOTLogLevel.IOTC_LOGGING_ALL)
    obj = None
    try:
      obj = json.loads(msg)
    except:
      LOG_IOTC("ERROR: JSON parse for SettingsUpdated message object has failed. => " + msg)
      return

    version = None
    if '$version' in obj:
      version = obj['$version']
    else:
      LOG_IOTC("ERROR: Unexpected payload for settings update => " + msg)
      return

    for attr, value in obj.items():
      if attr != '$version':
        ret = MAKE_CALLBACK(self, "SettingsUpdated", json.dumps(value), attr, 0)
        ret_code = 200
        ret_message = "completed"
        if ret.getResponseCode() != None:
          ret_code = ret.getResponseCode()
        if ret.getResponseMessage() != None:
          ret_message = ret.getResponseMessage()

        value["statusCode"] = ret_code
        value["status"] = ret_message
        value["desiredVersion"] = version
        wrapper = {}
        wrapper[attr] = value
        msg = json.dumps(wrapper)
        self.sendProperty(msg)

  def _on_message(self, client, _, data):
    LOG_IOTC("- iotc :: _on_message :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    topic = ""
    msg = None
    if data == None:
      LOG_IOTC("WARNING: (_on_message) data is None.")
      return

    if data.payload != None:
      msg = str(data.payload)

    if data.topic != None:
      topic = str(data.topic)

    if topic.startswith('$iothub/'): # twin
      # DO NOT need to echo twin response since IOTC api takes care of the desired messages internally
      # if topic.startswith('$iothub/twin/res/'): # twin response
      #   self._handleTwin(topic, msg)
      #
      if topic.startswith('$iothub/twin/PATCH/properties/desired/'): # twin desired property change
        self._echoDesired(msg, topic)
      elif topic.startswith('$iothub/methods'): # C2D
        ret = MAKE_CALLBACK(self, "Command", msg, topic, 0)
        ret_code = 200
        ret_message = "{}"
        if ret.getResponseCode() != None:
          ret_code = ret.getResponseCode()
        if ret.getResponseMessage() != None:
          ret_message = ret.getResponseMessage()
        topic_template = "$iothub/methods/POST/echo/?$rid="
        method_id = topic[len(topic_template):]
        next_topic = '$iothub/methods/res/{}/?$rid={}'.format(ret_code, method_id)
        LOG_IOTC("C2D: => " + next_topic + " with data " + ret_message)
        (result, msg_id) = self._mqtts.publish(next_topic, ret_message, qos=0)
        if result != MQTT_SUCCESS:
          LOG_IOTC("ERROR: (send method callback) failed to send. MQTT client return value: " + str(result) + ". ERROR:0x000B")
      else:
        if not topic.startswith('$iothub/twin/res/'): # not twin response
          LOG_IOTC('ERROR: unknown twin! {} - {}'.format(topic, msg))
    else:
      LOG_IOTC('ERROR: (unknown message) {} - {}'.format(topic, msg))

  def _on_log(self, client, userdata, level, buf):
    global gLOG_LEVEL
    if gLOG_LEVEL > IOTLogLevel.IOTC_LOGGING_API_ONLY:
      LOG_IOTC("mqtt-log : " + buf)
    elif level <= 8:
      LOG_IOTC("mqtt-log : " + buf) # transport layer exception

  def _on_disconnect(self, client, userdata, rc):
    LOG_IOTC("- iotc :: _on_disconnect :: rc = " + str(rc), IOTLogLevel.IOTC_LOGGING_ALL)
    self._auth_response_received = True

    if rc == 5:
      LOG_IOTC("on(disconnect) : Not authorized")
      self.disconnect()
      sys.exit()
    else:
      MAKE_CALLBACK(self, "ConnectionStatus", userdata, "", rc)

  def _on_publish(self, client, data, msgid):
    LOG_IOTC("- iotc :: _on_publish :: " + str(data), IOTLogLevel.IOTC_LOGGING_ALL)
    if data == None:
      data = ""
    if self._messages[str(msgid)] == None:
      LOG_IOTC("ERROR: message send confirmation failed. (_on_publish) Unknown message id. ERR:0x000C")
    else:
      MAKE_CALLBACK(self, "MessageSent", self._messages[str(msgid)], data, 0)
      del self._messages[str(msgid)]

  def _mqttcb(self, topic, msg):
    # NOOP
    LOG_IOTC("???" + topic + " " + msg)

  def _mqttConnect(self, err, hostname):
    if err != None:
      LOG_IOTC("ERROR : (_mqttConnect) " + str(err))
      return 1

    LOG_IOTC("- iotc :: _mqttConnect :: " + hostname, IOTLogLevel.IOTC_LOGGING_ALL)

    self._hostname = hostname
    username = '{}/{}/api-version=2016-11-14'.format(self._hostname, self._deviceId)
    passwd = self._gen_sas_token(self._hostname, self._deviceId, self._keyORCert)

    _createMQTTClient(self, username, passwd)

    LOG_IOTC(" - iotc :: _mqttconnect :: created mqtt client. connecting..", IOTLogLevel.IOTC_LOGGING_ALL)
    if mqtt != None:
      while self._auth_response_received == None:
        self.doNext()
      LOG_IOTC(" - iotc :: _mqttconnect :: on_connect must be fired. Connected ? " + str(self.isConnected()), IOTLogLevel.IOTC_LOGGING_ALL)
      if not self.isConnected():
        return 1
    else:
      self._mqttConnected = True
      self._auth_response_received = True

    self._mqtts.subscribe('devices/{}/messages/events/#'.format(self._deviceId))
    self._mqtts.subscribe('devices/{}/messages/deviceBound/#'.format(self._deviceId))
    self._mqtts.subscribe('$iothub/twin/PATCH/properties/desired/#') # twin desired property changes
    self._mqtts.subscribe('$iothub/twin/res/#') # twin properties response
    self._mqtts.subscribe('$iothub/methods/#')

    MAKE_CALLBACK(self, "ConnectionStatus", None, None, 0)

    return 0

  def connect(self):
    global gEXPIRES
    LOG_IOTC("- iotc :: connect :: ", IOTLogLevel.IOTC_LOGGING_ALL)
    body = "{\"registrationId\":\"%s\"}" % (self._deviceId)
    expires = int(time.time() + gEXPIRES)

    sr = self._scopeId + "%2Fregistrations%2F" + self._deviceId
    sigNoEncode = self._computeDrivedSymmetricKey(self._keyORCert, sr + "\n" + str(expires))
    sigEncoded = _quote(sigNoEncode, '~()*!.\'')

    authString = "SharedAccessSignature sr=" + sr + "&sig=" + sigEncoded + "&se=" + str(expires) + "&skn=registration"
    headers = {
      "content-type": "application/json; charset=utf-8",
      "user-agent": "iot-central-client/1.0",
      "Accept": "*/*",
      "authorization" : authString
    }

    if self._modelData != None:
      headers["data"] = self._modelData

    uri = "https://%s/%s/registrations/%s/register?api-version=%s" % (self._dpsEndPoint, self._scopeId, self._deviceId, self._dpsAPIVersion)
    target = urlparse(uri)

    content = _request(self, target.geturl(), "PUT", body, headers)
    data = None
    try:
      data = json.loads(content)
    except:
      err = "ERROR: non JSON is received from %s => %s", (self._dpsEndPoint, content)
      LOG_IOTC(err)
      return self._mqttConnect(err, None)

    if 'errorCode' in data:
      err = "DPS => " + str(data)
      return self._mqttConnect(err, None)
    else:
      time.sleep(1)
      return self._loopAssign(data['operationId'], headers)

  def _gen_sas_token(self, hub_host, device_name, key):
    global gEXPIRES
    token_expiry = int(time.time() + gEXPIRES)
    uri = hub_host + "%2Fdevices%2F" + device_name
    signed_hmac_sha256 = self._computeDrivedSymmetricKey(key, uri + "\n" + str(token_expiry))
    signature = _quote(signed_hmac_sha256, '~()*!.\'')
    if signature.endswith('\n'):  # somewhere along the crypto chain a newline is inserted
      signature = signature[:-1]
    token = 'SharedAccessSignature sr={}&sig={}&se={}'.format(uri, signature, token_expiry)
    return token

  def sendTelemetry(self, data):
    LOG_IOTC("- iotc :: sendTelemetry :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    target = 'devices/{}/messages/events/'.format(self._deviceId)
    if mqtt != None:
      (result, msg_id) = self._mqtts.publish(target, data)
      if result != mqtt.MQTT_ERR_SUCCESS:
        LOG_IOTC("ERROR: (sendTelemetry) failed to send. MQTT client return value: " + str(result) + ". ERROR:0x000B")
        return 11
      self._messages[str(msg_id)] = data
    else:
      self._mqtts.publish(target, data)
      msg_id = 0
      self._messages[str(msg_id)] = data
      self._on_publish(None, target, msg_id)

    return 0

  def sendState(self, data):
    return self.sendTelemetry(data)

  def sendEvent(self, data):
    return self.sendTelemetry(data)

  def sendProperty(self, data):
    LOG_IOTC("- iotc :: sendProperty :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    target = '$iothub/twin/PATCH/properties/reported/?$rid={}'.format(int(time.time()))
    self._mqtts.publish(target, data)
    if mqtt != None:
      msg_id = 0
      self._messages[str(msg_id)] = data
      self._on_publish(None, target, msg_id)
    return 0

  def disconnect(self):
    if not self.isConnected():
      return

    LOG_IOTC("- iotc :: disconnect :: ", IOTLogLevel.IOTC_LOGGING_ALL)
    self._mqttConnected = False
    if mqtt != None:
      self._mqtts.disconnect()
    else:
      MAKE_CALLBACK(self, "ConnectionStatus", None, None, 0)
    return 0

  def on(self, eventName, callback):
    self._events[eventName] = callback
    return 0

  def isConnected(self):
    return self._mqttConnected

  def doNext(self):
    if not self.isConnected():
      return
    if mqtt == None:
      try: # try non-blocking
        self._mqtts.check_msg()
        time.sleep(1)
      except: # non-blocking wasn't implemented
        self._mqtts.wait_msg()
    else: #paho
      self._mqtts.loop()
      time.sleep(1)