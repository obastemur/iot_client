## iotc - Azure IoT Central - Python (light) device SDK Documentation

### Prerequisites

Python 2.7+ or Python 3.4+ or Micropython 1.9+

*Runtime dependencies vary per platform*

### Install

Python 2/3
```
pip install iotc
```

### Usage

```
import iotc
device = iotc.Device(scopeId, keyORCert, deviceId, credType)
```

- *scopeId*    : Azure IoT DPS Scope Id
- *keyORcert*  : Symmetric key or x509 Certificate
- *deviceId*   : Device Id
- *credType*   : `IOTConnectType.IOTC_CONNECT_SYMM_KEY` or `IOTConnectType.IOTC_CONNECT_X509_CERT`

`keyORcert` for `X509` certificate:
```
credType = IOTConnectType.IOTC_CONNECT_X509_CERT
keyORcert = {
  "keyfile": "/src/python/test/device.key.pem",
  "certfile": "/src/python/test/device.cert.pem"
}
```

`keyORcert` for `SAS` token:
```
credType = IOTConnectType.IOTC_CONNECT_SYMM_KEY
keyORcert = "xxxxxxxxxxxxxxx........"
```


#### setLogLevel
set logging level
```
device.setLogLevel(logLevel)
```

*logLevel*   : (default value is `IOTC_LOGGING_DISABLED`)
```
class IOTLogLevel:
  IOTC_LOGGING_DISABLED =  1
  IOTC_LOGGING_API_ONLY =  2
  IOTC_LOGGING_ALL      = 16
```

*i.e.* => `device.setLogLevel(IOTLogLevel.IOTC_LOGGING_API_ONLY)`

#### setServiceHost
set the service endpoint URL
```
device.setServiceHost(url)
```

*url*    : URL for service endpoint. (default value is `global.azure-devices-provisioning.net`)

*call this before connect*

#### connect
connect device client

```
device.connect()
```

i.e. `device.connect()`

#### sendTelemetry
send telemetry

```
device.sendTelemetry(payload)
```

*payload*  : A text payload.

i.e. `device.sendTelemetry('{ "temperature": 15 }')`

#### sendState
send device state

```
device.sendState(payload)
```

*payload*  : A text payload.

i.e. `device.sendState('{ "status": "WARNING"}')`

#### sendProperty
send reported property

```
device.sendProperty(payload)
```

*payload*  : A text payload.

i.e. `device.sendProperty('{"countdown":{"value": %d}}')`

#### doNext
let framework do the partial MQTT work.

```
device.doNext()
```

#### isConnected
returns whether the connection was established or not.

```
device.isConnected()
```

i.e. `device.isConnected()`

#### disconnect
disconnect device client

```
device.disconnect()
```

i.e. `device.disconnect()`

#### on
set event callback to listen events

- `ConnectionStatus` : connection status has changed
- `MessageSent`      : message was sent
- `Command`          : a command received from Azure IoT Central
- `SettingsUpdated`  : device settings were updated

i.e.
```
def onconnect(info):
  if info.getStatusCode() == 0:
    print("connected!")

device.on("ConnectionStatus", onconnect)
```

```
def onmessagesent(info):
  print("message sent -> " + info.getPayload())

device.on("MessageSent", onmessagesent)
```

```
def oncommand(info):
  print("command -> " + info.getPayload())

device.on("Command", oncommand)
```

```
def onsettingsupdated(info):
  print("settings -> " + info.getTag() + " = " + info.getPayload())

device.on("SettingsUpdated", onsettingsupdated)
```

#### callback info class

`iotc` callbacks have a single argument derived from `IOTCallbackInfo`.
Using this interface, you can get the callback details and respond back when it's necessary.

public members of `IOTCallbackInfo` are;

`getResponseCode()` : get response code or `None`

`getResponseMessage()` : get response message or `None`

`setResponse(responseCode, responseMessage)` : set callback response

i.e. `info.setResponse(200, 'completed')`

`getClient()` : get active `device` client

`getEventName()` : get the name of the event

`getPayload()` : get the payload or `None`

`getTag()` : get the tag or `None`

`getStatusCode()` : get callback status code

#### sample app

```
import iotc
from iotc import IOTConnectType, IOTLogLevel

deviceId = "DEVICE_ID"
scopeId = "SCOPE_ID"
mkey = "DEVICE_KEY"

# see iotc.Device documentation above for x509 argument sample
iotc = iotc.Device(scopeId, mkey, deviceId, IOTConnectType.IOTC_CONNECT_SYMM_KEY)
iotc.setLogLevel(IOTLogLevel.IOTC_LOGGING_API_ONLY)

gCanSend = False
gCounter = 0

def onconnect(info):
  global gCanSend
  print("- [onconnect] => status:" + str(info.getStatusCode()))
  if info.getStatusCode() == 0:
     if iotc.isConnected():
       gCanSend = True

def onmessagesent(info):
  print("\t- [onmessagesent] => " + str(info.getPayload()))

def oncommand(info):
  print("- [oncommand] => command name(" + info.getTag() + ") => " + str(info.getPayload()))

def onsettingsupdated(info):
  print("- [onsettingsupdated] => settings name(" + info.getTag() + ") => " + info.getPayload())

iotc.on("ConnectionStatus", onconnect)
iotc.on("MessageSent", onmessagesent)
iotc.on("Command", oncommand)
iotc.on("SettingsUpdated", onsettingsupdated)

iotc.connect()

while iotc.isConnected():
  iotc.doNext() # do the async work needed to be done for MQTT
  if gCanSend == True:
    if gCounter % 20 == 0:
      gCounter = 0
      print("Sending telemetry..")
      iotc.sendTelemetry("{\"temp\": " + str(randint(20, 45)) + "}")

    gCounter += 1
```