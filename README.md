# raphael-connectors

Native connectors, sync jobs, credentials

## API

- Prefix: `/v1/connectors`
- Port: `8096`
- Health: `GET /health`

## Events

_Published and consumed events documented in `openapi.yaml` and raphael-contracts._

## Development

```bash
uv sync
uv run uvicorn raphael_connectors.app:app --reload --port 8096
```

Part of the [Raphael Platform](https://github.com/hummingbird-labs) by HummingBird Labs.
