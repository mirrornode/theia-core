export default function handler(req, res) {
  res.status(200).json({
    status: 'ok',
    service: 'theia-core',
    ts: new Date().toISOString(),
  });
}
