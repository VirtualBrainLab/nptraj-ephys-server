const express = require("express");
const socket = require("socket.io");
const cors = require("cors");

// App setup
const port = process.env.PORT || 5000
const app = express();

app.use(cors());

const server = app.listen(port, function () {
  console.log(`Listening on port ${port}`);
});

// Socket setup
const io = require("socket.io")(server, {
  cors:
  {
    "origin": "http://data.virtualbrainlab.org",
    "methods": "GET,HEAD,PUT,PATCH,POST,DELETE",
    "preflightContinue": false,
    "optionsSuccessStatus": 204
  } 
});

io.on("connection", function (socket) {
  console.log("Client connected with ID: " + socket.id);

  socket.on('disconnect', () => {
  	console.log('Client disconnected with ID: ' + socket.id);

  	if (idDict[clientIDdict[socket.id]]) {
		idDict[clientIDdict[socket.id]].splice(idDict[clientIDdict[socket.id]].indexOf(socket.id),1);
		clientIDdict[socket.id] = undefined;
  	}
  })

  socket.on('ID', function(newClientID) {
  	console.log('Client ' + socket.id + ' requested to update ID to ' + newClientID);
  	// Check if we have an old clientID that needs to be removed
  	if (clientIDdict[socket.id]) {
  		oldClientID = clientIDdict[socket.id]

  		idDict[oldClientID].splice(idDict[oldClientID].indexOf(socket.id),1);
  	}

  	if (idDict[newClientID] == undefined) {
  		// save the new entry into a new list
  		idDict[newClientID] = [socket.id];
  	}
  	else {
  		// save the new entry
  		idDict[newClientID].push(socket.id);
  	}
  	// update the client ID locally
	clientIDdict[socket.id] = newClientID;
  	console.log('User updated their ID to: ' + clientIDdict[socket.id]);
  	console.log('All connected clients with ID: ' + idDict[clientIDdict[socket.id]]);
  });

  socket.on('SetVolumeColors', function(data) {
  	emitToAll(socket.id, 'SetVolumeColors', data);
  });
});

function emitToAll(id, event, data) {
  	console.log('User sent data: ' + data + ' emitting to all clients with ID: ' + clientIDdict[id]);
  	for (var socketID of idDict[clientIDdict[id]]) {
  		console.log('Emitting to: ' + socketID);
  		io.to(socketID).emit(event,data);
  	}
}