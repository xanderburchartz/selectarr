# Security Policy

## Supported versions

Only the latest release of Selectarr receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes       |
| 0.1.x   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Use [GitHub private vulnerability reporting](https://github.com/xanderburchartz/selectarr/security/advisories/new) to submit a report confidentially. You'll receive a response within 7 days. If the vulnerability is confirmed, a fix will be released as soon as possible and you'll be credited in the changelog unless you prefer to remain anonymous.

## Scope

Things we consider in scope:

- Authentication bypass or session fixation
- Arbitrary file read/write through path traversal
- Server-side request forgery via user-supplied service URLs
- Injection vulnerabilities (command, template, SQL)

Things we consider out of scope:

- Vulnerabilities in Jellyfin, Radarr, Sonarr, or Lidarr themselves
- Issues that require physical access to the host machine
- Rate limiting / denial of service on a home-network deployment
