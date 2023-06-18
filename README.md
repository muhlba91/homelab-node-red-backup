# Homelab: Node-RED Backup & Restore

[![](https://img.shields.io/github/license/muhlba91/homelab-node-red-backup?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/actions/workflow/status/muhlba91/homelab-node-red-backup/verify.yml?style=for-the-badge)](https://github.com/muhlba91/homelab-node-red-backup/actions/workflows/verify.yml)
[![](https://img.shields.io/pypi/pyversions/homelab-node-red-backup?style=for-the-badge)](https://pypi.org/project/homelab-node-red-backup/)
[![](https://img.shields.io/pypi/v/homelab-node-red-backup?style=for-the-badge)](https://pypi.org/project/homelab-node-red-backup/)
[![](https://img.shields.io/github/release-date/muhlba91/homelab-node-red-backup?style=for-the-badge)](https://github.com/muhlba91/homelab-node-red-backup/releases)
[![](https://img.shields.io/pypi/dm/homelab-node-red-backup?style=for-the-badge)](https://pypi.org/project/homelab-node-red-backup/)
[![Known Vulnerabilities](https://snyk.io/test/github/muhlba91/homelab-node-red-backup/badge.svg)](https://snyk.io/test/github/muhlba91/homelab-node-red-backup/)
<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="28" width="150"></a>

This repository contains Python scripts leveraging the [Node-RED Admin API](https://nodered.org/docs/api/admin/methods/) endpoints to create and restore backups.

**Attention:** the Node-RED installation must either be unsecured or secured by OAuth!

---

## Installation

The package is published in **(Test)PyPi** and can be installed via:

```bash
pip install homelab-node-red-backup
```

## Configuration

The following arguments are available:

- `--endpoint` / `-e`: the Node-RED endpoint
- `--file` / `-f`: the JSON file
- `--jwt-token` / `-jwt`: the JWT token to authenticate with

## Credentials

Credentials are detected, retrieved, and merged to the output JSON file.
The following credential types are recognized:

- `servers`: e.g. a Home Assistant server with an access token
- `telegram bot`: Telegram bot with a token

## Usage

The following commands are available, and all commands require the arguments `--endpoint`, and, optionally, `--jwt-token` set.

- `check`: checks if data exists for a backup (return code `0` if data exists, else `1`)
- `backup`: creates a backup
  - requires: `--file`
- `restore`: restores from a backup
  - requires: `--file`
- `auto`: performs a `check` and either creates a backup to or restores a backup from the given `--file`
  - requires: `--file`

### Examples

```bash
# checking if data exists
homelab-node-red-backup check -e http://localhost:1880 -jwt <TOKEN>

# creating a backup
homelab-node-red-backup backup -e http://localhost:1880 -jwt <TOKEN> -f backup.json

# restoring from the backup
homelab-node-red-backup restore -e http://localhost:1880 -jwt <TOKEN> -f backup.json
```

---

## Supporting

If you enjoy the application and want to support my efforts, please feel free to buy me a coffe. :)

<a href="https://www.buymeacoffee.com/muhlba91" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="75" width="300"></a>
