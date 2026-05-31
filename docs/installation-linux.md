# Linux Installation

Linux support is experimental until it is tested across common distributions.

## Conda or micromamba

```bash
conda create -n pymol-figure-agent -c conda-forge python=3.10 pymol-open-source
conda activate pymol-figure-agent
pip install -r requirements.txt
```

With micromamba:

```bash
micromamba create -n pymol-figure-agent -c conda-forge python=3.10 pymol-open-source
micromamba activate pymol-figure-agent
pip install -r requirements.txt
```

## Start

```bash
uvicorn app:app --host 127.0.0.1 --port 8010
```

## Notes

Headless or remote Linux systems may require OpenGL or offscreen rendering configuration. Real render tests are currently manual.
