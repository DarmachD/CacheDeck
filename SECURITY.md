# Security policy

## Reporting a vulnerability

Report security issues privately through GitHub private vulnerability reporting
when available. Do not include Steam credentials, session data, database copies,
Docker socket contents or other private server information in a public issue.

## Deployment warning

CacheDeck has no built-in user authentication. Do not expose it directly to the
public internet. Restrict access to a trusted LAN or place it behind an
authenticated reverse proxy.

## Embedded Steam credentials

The v0.8 embedded engine stores SteamPrefill configuration and session data under:

```text
/config/steam-engine/Config
```

Treat the complete `/config` mapping and its backups as sensitive. Restrict file
permissions and do not attach it to public bug reports.

## Docker socket

The default `embedded-steam` provider does not require `/var/run/docker.sock`.
Do not mount the socket unless using the legacy external-container provider or
the explicit old-selection importer. Docker socket access can provide effective
root-level control over the host.

## Browser origins

CacheDeck validates same-origin WebSocket and state-changing HTTP requests by
default. When an authenticated reverse proxy deliberately presents another
browser origin, add it to `CACHEDECK_ALLOWED_ORIGINS`. Do not use `*` unless a
trusted access-control layer protects all requests before they reach CacheDeck.
