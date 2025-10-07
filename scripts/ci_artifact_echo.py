#!/usr/bin/env python3
import pathlib, json
def ls(d): return sorted([str(p) for p in pathlib.Path(d).glob("**/*") if p.is_file()])
out = {"outcomes": ls("outcomes"), "edgesheet": ls(".")}
print(json.dumps(out, indent=2))
