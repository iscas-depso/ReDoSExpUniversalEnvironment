const { createApp } = require('./app');

const PORT = Number(process.env.PORT) || 8080;
const HOST = process.env.HOST || '0.0.0.0';

const app = createApp();

app.listen(PORT, HOST, () => {
  console.log(`ReDoS web service listening at http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
});
