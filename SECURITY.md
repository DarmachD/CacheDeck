# Security policy

## Reporting a vulnerability

Please report security issues privately to the repository maintainer through
GitHub's private vulnerability reporting feature when it is available.

Do not include credentials, Steam session data, Docker socket contents or other
private server information in a public issue.

## Deployment warning

CacheDeck mounts the Docker socket and currently has no built-in authentication.
Do not expose it directly to the public internet. Restrict access to a trusted
LAN or protect it behind an authenticated reverse proxy.
