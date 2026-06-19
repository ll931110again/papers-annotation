# MIT 6.858 — Computer Systems Security (Fall 2012)

Lab solutions and Docker grading environment for [MIT 6.858](https://css.csail.mit.edu/6.858/2012/).

## Layout

| Path | Contents |
|------|----------|
| `lab-solutions/lab1/` | Buffer overflows — bugs, exploits, `http.c` fixes |
| `lab-solutions/lab2/` | Privilege separation — RPC services, chroot |
| `lab-solutions/lab3/` | PyPy sandbox |
| `lab-solutions/lab5/` | Browser attack answers |
| `lab-solutions/lab6/` | JS sandbox (`htmlfilter.py`, `lab6visitor.py`) |
| `lab4/` | Code review writeups |
| `lab/` | Working copy (lab2 base) for Docker volume mount |
| `grade-native.sh` | Grade all labs on native x86_64 Docker |

## Quick start

```bash
docker compose -f docker-compose.native.yml build
./grade-native.sh all
```

See [README.md](README.md) for full grading notes.
