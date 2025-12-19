export default function handler(req: any, res: any) {
  res.status(200).json({
    status: 'ok',
    service: 'theia-core',
    ts: new Date().toISOString()
  });
}

