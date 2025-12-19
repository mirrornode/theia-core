const http = require('http');
const server = http.createServer((req, res) => {
if (req.url === '/health') {
res.writeHead(200, { 'Content-Type': 'application/json' });
res.end(JSON.stringify({
status: 'ok',
service: 'theia-core',
ts: new date().toISOString()
}));
return;
}
res.writehead(404, { 'Content-Type': 'text/plain' });
res.end('Not Found');
});
const port = process.env.PORT || 3000;
server.listen(port);
