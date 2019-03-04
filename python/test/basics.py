# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license.

import os
import sys

file_path = __file__[:len(__file__) - len("basics.py")]
# Update /usr/local/lib/python2.7/site-packages/iotc/__init__.py ?
if 'dont_write_bytecode' in dir(sys):
  sys.dont_write_bytecode = True
else: # micropython
  file_path = file_path[:len(file_path) - 1] if file_path[len(file_path) - 1:] == "b" else file_path
  sys.path.append(file_path + "../src")

import iotc
from iotc import IOTConnectType, IOTLogLevel
import json

pytest_run = False
def test_LOG_IOTC():
  global pytest_run
  pytest_run = True
  assert iotc.LOG_IOTC("LOGME") == 0

def CALLBACK_(info):
  if info.getPayload() == "{\"number\":1}":
    if info.getTag() == "TAG":
      if info.getStatusCode() == 0:
        if info.getEventName() == "TEST":
          info.setResponse(200, "DONE")
          return 0
  return 1

def test_MAKE_CALLBACK():
  client = { "_events" : { "TEST" : CALLBACK_ } }
  ret = iotc.MAKE_CALLBACK(client, "TEST", "{\"number\":1}", "TAG", 0)

  assert ret != 0
  assert ret.getResponseCode() == 200
  assert ret.getResponseMessage() == "DONE"

def test_quote():
  assert iotc._quote("abc+\\0123\"?%456@def", '~()*!.') == "abc%2B%5C0123%22%3F%25456%40def"

with open(file_path + "config.json", "r") as fh:
  configText = fh.read()
config = json.loads(configText)
assert config["scopeId"] != None and config["deviceKey"] != None and config["deviceId"] != None and config["hostName"] != None

testCounter = 0

def test_lifetime():
  device = iotc.Device(config["scopeId"], config["deviceKey"], config["deviceId"], IOTConnectType.IOTC_CONNECT_SYMM_KEY)

  def onconnect(info):
    global testCounter
    if device.isConnected():
      assert info.getStatusCode() == 0
      testCounter += 1
      assert device.sendTelemetry("{\"temp\":22}") == 0
      testCounter += 1
      assert device.sendProperty("{\"dieNumber\":3}") == 0
    else:
      assert testCounter == 4
      print ("- ", "done")

  def onmessagesent(info):
    global testCounter
    assert info.getPayload() == "{\"temp\":22}" or info.getPayload() == "{\"dieNumber\":3}" or info.getPayload() == " "
    testCounter += 1
    if info.getPayload() == "{\"dieNumber\":3}":
      assert device.disconnect() == 0

  def oncommand(info):
    global testCounter

    print("oncommand", info)
    assert info.getTag() == "echo"
    testCounter += 1
    assert device.disconnect() == 0

  def onsettingsupdated(info):
    global testCounter
    # TODO: match the tag / payload
    testCounter += 1
    assert device.disconnect() == 0

  assert device.on("ConnectionStatus", onconnect) == 0
  assert device.on("MessageSent", onmessagesent) == 0
  assert device.on("Command", oncommand) == 0
  assert device.on("SettingsUpdated", onsettingsupdated) == 0

  assert device.setLogLevel(IOTLogLevel.IOTC_LOGGING_ALL) == 0

  assert device.setDPSEndpoint(config["hostName"]) == 0
  assert device.connect() == 0

  while device.isConnected():
    device.doNext()

if pytest_run == False:
  test_LOG_IOTC()
  test_MAKE_CALLBACK()
  test_quote()
  test_lifetime()