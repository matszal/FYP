const http = require('http');

const hostname = 'localhost';
const port = 3000;

const server = http.createServer((req, res) =>{
	res.statusCode = 200;
	res.setHeader('Content-type', 'text/plain');
	res.end('Hello world');

});

server.listen (port, hostname, () =>{
	console.log('Sever started on port '+port);
});