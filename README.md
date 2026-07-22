# Muslin

Muslin is the minimal test extension for Fab7 extension distribution. It owns
one command, `muslin start`, which invokes the public `fab7 --version` binary
and reports the observed version. It has no Fab7 imports or shared state.

Build an unpacked Fab7 extension package:

```bash
python3 scripts/build.py --output dist/muslin
```

Build the deterministic registry artifact:

```bash
python3 scripts/build.py --archive dist/muslin-0.1.0.zip
```

Install the source checkout for development with Fab7 0.2.0 or newer:

```bash
fab7 ext install --local . --host claude
muslin start --json
```

Muslin exists only to prove the Fab7 extension contract. Denim remains the
first product extension.
