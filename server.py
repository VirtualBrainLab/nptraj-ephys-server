#!/usr/bin/env python

# WS server example

import eventlet
import socketio
import numpy as np
import pandas as pd

data_indexes = np.load('pipeline/ea_hemisphere_mapping.npy')
print(data_indexes[100,100,100])

df = pd.read_csv('pipeline/ea_hemisphere_data.csv')

sio = socketio.Server()
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.on('data')
def data(sid, data):
	chan = data[0]
	if (data[3]>228):
		data[3] = 456-data[3]
	idx = data_indexes[data[1],data[2],data[3]]
	if not np.isnan(idx):
		out = df.iloc[np.argwhere(df['index'].values==idx)[0][0]].values.tolist()
		out.insert(0,chan)
		sio.emit('data',out)


@sio.event
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)


