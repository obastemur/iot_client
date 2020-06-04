# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

__version__ = "0.3.9"
__name__    = "iotc"

import sys

class IOTConnectType:
  IOTC_CONNECT_SYMM_KEY  = 1
  IOTC_CONNECT_X509_CERT = 2

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
    import httplib as http
  except ImportError:
    import http.client as http
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
    LOG_IOTC('Clean session enabled: {}'.format(__self._cleanSession),IOTLogLevel.IOTC_LOGGING_ALL)
    __self._mqtts = mqtt.Client(client_id=__self._deviceId, protocol=mqtt.MQTTv311,clean_session=__self._cleanSession)
    __self._mqtts.on_connect = __self._onConnect
    __self._mqtts.on_message = __self._onMessage
    __self._mqtts.on_log = __self._onLog
    __self._mqtts.on_publish = __self._onPublish
    __self._mqtts.on_disconnect = __self._onDisconnect

    __self._mqtts.username_pw_set(username=username, password=passwd)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.load_default_certs()
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.check_hostname = True

    if __self._credType != IOTConnectType.IOTC_CONNECT_SYMM_KEY:
      ssl_context.load_cert_chain(certfile=__self._certfile, keyfile=__self._keyfile)

    __self._mqtts.tls_set_context(ssl_context)
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

class IOTProtocol:
  IOTC_PROTOCOL_MQTT = 1
  IOTC_PROTOCOL_AMQP = 2
  IOTC_PROTOCOL_HTTP = 4

class IOTLogLevel:
  IOTC_LOGGING_DISABLED =  1
  IOTC_LOGGING_API_ONLY =  2
  IOTC_LOGGING_ALL      = 16

class IOTQosLevel:
  IOTC_QOS_AT_MOST_ONCE  = 0
  IOTC_QOS_AT_LEAST_ONCE = 1

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
gQOS_LEVEL = IOTQosLevel.IOTC_QOS_AT_MOST_ONCE # default is set to QoS 0 "At most once" IoT hub also supports QoS 1 "At least once"

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

  if obj != None and (eventName in obj) and obj[eventName] != None:
    cb = IOTCallbackInfo(client, eventName, payload, tag, status, msgid)
    obj[eventName](cb)
    return cb
  return 0

def _quote(a, b):
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

def _doRequest(device, target_url, method, body, headers):
  conn = http.HTTPSConnection(device._dpsEndPoint, '443', cert_file=device._certfile, key_file=device._keyfile)

  req_headers = {"Content-Type": headers["content-type"],
                   "User-Agent": headers["user-agent"],
                   "Accept": headers["Accept"],
                   "Accept-Encoding": "gzip, deflate"}

  if "authorization" in headers:
    req_headers["authorization"] = headers["authorization"]

  if body != None:
    req_headers["Content-Length"] = str(len(body))

  conn.request(method, target_url, body, req_headers)

  response = conn.getresponse()
  return response.read()

def _request(device, target_url, method, body, headers):
  content = None
  if http != None:
    return _doRequest(device, target_url, method, body, headers)
  else:
    if device._certfile != None:
      LOG_IOTC("ERROR: micropython client requires the client certificate is embedded.")
      sys.exit()

    response = urequests.request(method, target_url, data=body, headers=headers)
    return response.text

class Device:
  def __init__(self, scopeId, keyORCert, deviceId, credType):
    self._mqtts = None
    self._loopInterval = 2
    self._mqttConnected = False
    self._deviceId = deviceId
    self._scopeId = scopeId
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
    self._keyfile = None
    self._certfile = None
    self._addMessageTimeStamp = False
    self._cleanSession = True
    self._exitOnError = False
    self._tokenExpires = 21600
    self._events = {
      "MessageSent": None,
      "ConnectionStatus": None,
      "Command": None,
      "SettingUpdated": None,
      "EnqueuedCommand":None
    }

    if credType == IOTConnectType.IOTC_CONNECT_SYMM_KEY:
      self._keyORCert = keyORCert
    else:
      self._keyfile = keyORCert["keyfile"]
      self._certfile = keyORCert["certfile"]

  def setTokenExpiration(self, totalSeconds):
    self._tokenExpires = totalSeconds
    return 0

  def setExitOnError(self, isEnabled):
    self._exitOnError = isEnabled
    return 0

  def setCleanSession(self, isEnabled):
    self._cleanSession = isEnabled
    return 0

  def setSSLVerification(self, isEnabled):
    if self._auth_response_received:
      LOG_IOTC("ERROR: setSSLVerification should be called before `connect`")
      return 1
    self._sslVerificiationIsEnabled = isEnabled
    return 0

  def setModelData(self, data):
    LOG_IOTC("- iotc :: setModelData :: " + json.dumps(data), IOTLogLevel.IOTC_LOGGING_ALL)
    if self._auth_response_received:
      LOG_IOTC("ERROR: setModelData should be called before `connect`")
      return 1

    self._modelData = data
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
      LOG_IOTC("ERROR: (setLogLevel) invalid argument.")
      return 1
    gLOG_LEVEL = logLevel
    return 0

  def setQosLevel(self, qosLevel):
    global gQOS_LEVEL
    if qosLevel < IOTQosLevel.IOTC_QOS_AT_MOST_ONCE or qosLevel > IOTQosLevel.IOTC_QOS_AT_LEAST_ONCE:
      LOG_IOTC("ERROR: Only QOS level 0 (at most once) or 1 (at least once) is supported by IoT Hub")
      return 1
    gQOS_LEVEL = qosLevel
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
    try:
      data = json.loads(content.decode("utf-8"))
    except:
      try:
        data = json.loads(content)
      except Exception as e:
        err = "ERROR: %s => %s", (str(e), content)
        LOG_IOTC(err)
        return self._mqttConnect(err, None)

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
        self._hostName = state['assignedHub']
        return self._mqttConnect(None, self._hostName)
    else:
      data = str(data)

    return self._mqttConnect("DPS L => " + str(data), None)

  def _onConnect(self, client, userdata, _, rc):
    LOG_IOTC("- iotc :: _onConnect :: rc = " + str(rc), IOTLogLevel.IOTC_LOGGING_ALL)
    if rc == 0:
      self._mqttConnected = True
      MAKE_CALLBACK(self, "ConnectionStatus", userdata, "", rc)
    self._auth_response_received = True

  def _echoDesired(self, msg, topic):
    LOG_IOTC("- iotc :: _echoDesired :: " + topic, IOTLogLevel.IOTC_LOGGING_ALL)
    obj = None

    try:
      obj = json.loads(msg)
    except Exception as e:
      LOG_IOTC("ERROR: JSON parse for SettingsUpdated message object has failed. => " + msg + " => " + str(e))
      return

    version = None
    if 'desired' in obj:
      obj = obj['desired']

    if not '$version' in obj:
      LOG_IOTC("ERROR: Unexpected payload for settings update => " + msg)
      return 1

    version = obj['$version']

    for attr, value in obj.items():
      if attr != '$version':
        try:
          eventValue = json.loads(json.dumps(value))
          if version != None:
            eventValue['$version'] = version
        except:
          continue

        ret = MAKE_CALLBACK(self, "SettingsUpdated", json.dumps(eventValue), attr, 0)

        if not topic.startswith('$iothub/twin/res/200/?$rid=') and version != None:
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
          topic = '$iothub/twin/PATCH/properties/reported/?$rid={}'.format(int(time.time()))
          self._sendCommon(topic, msg, True)

  def _onMessage(self, client, _, data):
    topic = ""
    msg = None
    if data == None:
      LOG_IOTC("WARNING: (_onMessage) data is None.")
      return

    LOG_IOTC("- iotc :: _onMessage :: topic(" + str(data.topic) + ") payload(" + str(data.payload) + ")", IOTLogLevel.IOTC_LOGGING_ALL)

    if data.payload != None:
      try:
        msg = data.payload.decode("utf-8")
      except:
        msg = str(data.payload)

    if data.topic != None:
      try:
        topic = data.topic.decode("utf-8")
      except:
        topic = str(data.topic)

    if topic.startswith('$iothub/'): # twin
      # DO NOT need to echo twin response since IOTC api takes care of the desired messages internally
      # if topic.startswith('$iothub/twin/res/'): # twin response
      #   self._handleTwin(topic, msg)
      #
      if topic.startswith('$iothub/twin/PATCH/properties/desired/') or topic.startswith('$iothub/twin/res/200/?$rid='): # twin desired property change
        self._echoDesired(msg, topic)
      elif topic.startswith('$iothub/methods'): # Direct method
        index = topic.find("$rid=")
        method_id = 1
        method_name = "None"
        if index == -1:
          LOG_IOTC("ERROR: Command doesn't include topic id")
        else:
          method_id = topic[index + 5:]
          topic_template = "$iothub/methods/POST/"
          len_temp = len(topic_template)
          method_name = topic[len_temp:topic.find("/", len_temp + 1)]

        ret = MAKE_CALLBACK(self, "Command", msg, method_name, 0)
        ret_code = 200
        ret_message = "{}"
        if ret.getResponseCode() != None:
          ret_code = ret.getResponseCode()
        if ret.getResponseMessage() != None:
          ret_message = ret.getResponseMessage()

        next_topic = '$iothub/methods/res/{}/?$rid={}'.format(ret_code, method_id)
        LOG_IOTC("C2D: => " + next_topic + " with data " + ret_message  + " and name => " + method_name, IOTLogLevel.IOTC_LOGGING_ALL)
        (result, msg_id) = self._mqtts.publish(next_topic, ret_message, qos=gQOS_LEVEL)
        if result != MQTT_SUCCESS:
          LOG_IOTC("ERROR: (send method callback) failed to send. MQTT client return value: " + str(result))
      else:
        if not topic.startswith('$iothub/twin/res/'): # not twin response
          LOG_IOTC('ERROR: unknown twin! {} - {}'.format(topic, msg))
    elif topic.startswith('devices/{}/messages/devicebound'.format(self._deviceId)): # C2D offline message
      LOG_IOTC('C2D Offline message: {} - {}'.format(topic, msg))
      data=json.loads(msg)
      method_name=data['methodName']
      ret = MAKE_CALLBACK(self, "EnqueuedCommand", msg, method_name, 0)
    else:
      LOG_IOTC('ERROR: unknown message: {} - {}'.format(topic, msg))

  def _onLog(self, client, userdata, level, buf):
    global gLOG_LEVEL
    if gLOG_LEVEL > IOTLogLevel.IOTC_LOGGING_API_ONLY:
      LOG_IOTC("mqtt-log : " + buf)
    elif level <= 8:
      LOG_IOTC("mqtt-log : " + buf) # transport layer exception
      if self._exitOnError:
        sys.exit()

  def _onDisconnect(self, client, userdata, rc):
    LOG_IOTC("- iotc :: _onDisconnect :: rc = " + str(rc), IOTLogLevel.IOTC_LOGGING_ALL)
    self._auth_response_received = True

    if rc == 5:
      LOG_IOTC("on(disconnect) : Not authorized")
      self.disconnect()

    if rc == 1:
      self._mqttConnected = False

    MAKE_CALLBACK(self, "ConnectionStatus", userdata, "", rc)

  def _onPublish(self, client, data, msgid):
    LOG_IOTC("- iotc :: _onPublish :: " + str(data), IOTLogLevel.IOTC_LOGGING_ALL)
    if data == None:
      data = ""

    if msgid != None and (str(msgid) in self._messages) and self._messages[str(msgid)] != None:
      MAKE_CALLBACK(self, "MessageSent", self._messages[str(msgid)], data, 0)
      if (str(msgid) in self._messages):
        del self._messages[str(msgid)]

  def _mqttcb(self, topic, msg):
    # NOOP
    pass

  def _mqttConnect(self, err, hostname):
    if err != None:
      LOG_IOTC("ERROR : (_mqttConnect) " + str(err))
      return 1

    LOG_IOTC("- iotc :: _mqttConnect :: " + hostname, IOTLogLevel.IOTC_LOGGING_ALL)

    self._hostname = hostname
    passwd = None

    username = '{}/{}/api-version=2016-11-14'.format(self._hostname, self._deviceId)
    if self._credType == IOTConnectType.IOTC_CONNECT_SYMM_KEY:
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
    self._mqtts.subscribe('devices/{}/messages/devicebound/#'.format(self._deviceId))
    self._mqtts.subscribe('$iothub/twin/PATCH/properties/desired/#') # twin desired property changes
    self._mqtts.subscribe('$iothub/twin/res/#') # twin properties response
    self._mqtts.subscribe('$iothub/methods/#')

    if self.getDeviceSettings() == 0:
      MAKE_CALLBACK(self, "ConnectionStatus", None, None, 0)
    else:
      return 1

    return 0

  def getDeviceSettings(self):
    LOG_IOTC("- iotc :: getDeviceSettings :: ", IOTLogLevel.IOTC_LOGGING_ALL)
    self.doNext()
    return self._sendCommon("$iothub/twin/GET/?$rid=0", " ")

  def getHostName(self):
    return self._hostName

  def connect(self, hostName = None):
    LOG_IOTC("- iotc :: connect :: ", IOTLogLevel.IOTC_LOGGING_ALL)

    if hostName != None:
      self._hostName = hostName
      return self._mqttConnect(None, self._hostName)

    expires = int(time.time() + self._tokenExpires)
    authString = None

    if self._credType == IOTConnectType.IOTC_CONNECT_SYMM_KEY:
      sr = self._scopeId + "%2Fregistrations%2F" + self._deviceId
      sigNoEncode = self._computeDrivedSymmetricKey(self._keyORCert, sr + "\n" + str(expires))
      sigEncoded = _quote(sigNoEncode, '~()*!.\'')
      authString = "SharedAccessSignature sr=" + sr + "&sig=" + sigEncoded + "&se=" + str(expires) + "&skn=registration"

    headers = {
      "content-type": "application/json; charset=utf-8",
      "user-agent": "iot-central-client/1.0",
      "Accept": "*/*"
    }

    if authString != None:
      headers["authorization"] = authString

    if self._modelData != None:
      body = "{\"registrationId\":\"%s\",\"data\":%s}" % (self._deviceId, json.dumps(self._modelData))
    else:
      body = "{\"registrationId\":\"%s\"}" % (self._deviceId)

    uri = "https://%s/%s/registrations/%s/register?api-version=%s" % (self._dpsEndPoint, self._scopeId, self._deviceId, self._dpsAPIVersion)
    target = urlparse(uri)

    content = _request(self, target.geturl(), "PUT", body, headers)
    data = None
    try:
      data = json.loads(content.decode("utf-8"))
    except:
      try:
        data = json.loads(content)
      except Exception as e:
        err = "ERROR: non JSON is received from %s => %s .. message : %s", (self._dpsEndPoint, content, str(e))
        LOG_IOTC(err)
        return self._mqttConnect(err, None)

    if 'errorCode' in data:
      err = "DPS => " + str(data)
      return self._mqttConnect(err, None)
    else:
      time.sleep(1)
      return self._loopAssign(data['operationId'], headers)

  def _gen_sas_token(self, hub_host, device_name, key):
    token_expiry = int(time.time() + self._tokenExpires)
    uri = hub_host + "%2Fdevices%2F" + device_name
    signed_hmac_sha256 = self._computeDrivedSymmetricKey(key, uri + "\n" + str(token_expiry))
    signature = _quote(signed_hmac_sha256, '~()*!.\'')
    if signature.endswith('\n'):  # somewhere along the crypto chain a newline is inserted
      signature = signature[:-1]
    token = 'SharedAccessSignature sr={}&sig={}&se={}'.format(uri, signature, token_expiry)
    return token

  def _sendCommon(self, topic, data, noEvent = None):
    if mqtt != None:
      (result, msg_id) = self._mqtts.publish(topic, data, qos=gQOS_LEVEL)
      if result != mqtt.MQTT_ERR_SUCCESS:
        LOG_IOTC("ERROR: (sendTelemetry) failed to send. MQTT client return value: " + str(result) + "")
        return 1
    else:
      self._mqtts.publish(topic, data, qos=gQOS_LEVEL)
      msg_id = 0
      self._messages[str(msg_id)] = None

    if noEvent == None:
      self._messages[str(msg_id)] = data
      if mqtt == None:
        self._onPublish(None, topic, msg_id)

    return 0

  def sendTelemetry(self, data, systemProperties = None):
    LOG_IOTC("- iotc :: sendTelemetry :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    topic = 'devices/{}/messages/events/'.format(self._deviceId)

    if systemProperties != None:
      firstProp = True
      for prop in systemProperties:
        if not firstProp:
          topic += "&"
        else:
          firstProp = False
        topic += prop + '=' + str(systemProperties[prop])

    return self._sendCommon(topic, data)

  def sendState(self, data):
    return self.sendTelemetry(data)

  def sendEvent(self, data):
    return self.sendTelemetry(data)

  def sendProperty(self, data):
    LOG_IOTC("- iotc :: sendProperty :: " + data, IOTLogLevel.IOTC_LOGGING_ALL)
    topic = '$iothub/twin/PATCH/properties/reported/?$rid={}'.format(int(time.time()))

    return self._sendCommon(topic, data)

  def disconnect(self):
    if not self.isConnected():
      return

    LOG_IOTC("- iotc :: disconnect :: ", IOTLogLevel.IOTC_LOGGING_ALL)
    self._mqttConnected = False
    if mqtt != None:
      self._mqtts.disconnect()
      self._mqtts.loop_stop()
    else:
      MAKE_CALLBACK(self, "ConnectionStatus", None, None, 0)
    return 0

  def on(self, eventName, callback):
    self._events[eventName] = callback
    return 0

  def isConnected(self):
    return self._mqttConnected

  def doNext(self, idleTime=1):
    if not self.isConnected():
      return
    if mqtt == None:
      try: # try non-blocking
        self._mqtts.check_msg()
        time.sleep(idleTime)
      except: # non-blocking wasn't implemented
        self._mqtts.wait_msg()
    else: #paho
      time.sleep(idleTime)
