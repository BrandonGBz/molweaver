# Linux Installation

Linux support is experimental until it is tested across common distributions.

## Conda or micromamba

```bash
conda create -n pymol-agent-bridge -c conda-forge python=3.10 pymol-open-source
conda activate pymol-agent-bridge
pip install -r requirements.txt
```

With micromamba:

```bash
micromamba create -n pymol-agent-bridge -c conda-forge python=3.10 pymol-open-source
micromamba activate pymol-agent-bridge
pip install -r requirements.txt
```

## Start

```bash
uvicorn app:app --host 127.0.0.1 --port 8010
```

## Notes

Headless or remote Linux systems may require OpenGL or offscreen rendering configuration. Real render tests are currently manual.
