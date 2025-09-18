import sys, re, xml.etree.ElementTree as ET, pathlib
collect_log = pathlib.Path("pytest_collect.txt")
if not collect_log.exists():
    print("FATAL: pytest_collect.txt missing (collection step didn’t run)"); sys.exit(1)
text = collect_log.read_text()
m = re.search(r"collected\s+(\d+)\s+items", text)
if not m or int(m.group(1)) == 0:
    print("FATAL: collected 0 tests in unit lane"); sys.exit(1)

cov = pathlib.Path("coverage.xml")
if not cov.exists():
    print("FATAL: coverage.xml missing"); sys.exit(1)
root = ET.parse(str(cov)).getroot()
rate = root.attrib.get("line-rate")
pct = 0.0 if rate is None else float(rate)*100.0
if pct <= 0.0 + 1e-9:
    print("FATAL: coverage line-rate is 0.0%"); sys.exit(1)
print(f"Sanity OK: collected {int(m.group(1))} tests; coverage {pct:.1f}%")
