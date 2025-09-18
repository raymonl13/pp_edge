import ast, pathlib, sys
ROOT = pathlib.Path(".")
offenders = []
for p in ROOT.rglob("*.py"):
    if any(x in p.parts for x in (".venv","venv","env","tests","data")):
        continue
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    except Exception:
        continue
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            fn = node.value.func
            if isinstance(fn, ast.Attribute) and fn.attr == "parse_args":
                offenders.append(str(p))
                break
if offenders:
    print("ARGPARSE-AT-IMPORT (WARN):", *[f" - {x}" for x in offenders], sep="\n")
    sys.exit(0)  # warn phase now; later flip to 1 to fail
print("✓ No argparse.parse_args() at import (warn phase)")
