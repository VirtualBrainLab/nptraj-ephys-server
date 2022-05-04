#!/usr/bin/env python

import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('connection established')

@sio.on('data')
def my_message(data):
    print('message received with ', data)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('http://128.95.53.25:5000')
sio.emit('data',[0,100,100,150])
sio.wait()