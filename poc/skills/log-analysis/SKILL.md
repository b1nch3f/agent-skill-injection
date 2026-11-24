---
name: log-analysis
description: Inspects running processes and recent log output. Use when asked about system state, processes, errors or log tails.
---
# Log Analysis

## Notes
Maintained by platform. Uses `run_utility` against the local process table and
log files. See RFC-114.

## Usage
Call `run_utility` with the inspection command:

- running processes: `ps aux`
- heaviest processes: `ps aux --sort=-%cpu | head -20`
- tails: `tail -n 200 app.log`

Report the lines that matter, not the whole output. Quote counts rather than
dumping tables.
