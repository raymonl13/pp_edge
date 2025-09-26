import xml.etree.ElementTree as ET, sys, os
p = sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"
if not os.path.exists(p):
    print("coverage.xml not found"); sys.exit(0)
tree = ET.parse(p); root = tree.getroot()
files = []
for cls in root.iter("class"):
    fn = cls.attrib.get("filename","")
    lines = cls.find("lines")
    if not lines: continue
    total = len(list(lines))
    miss = sum(1 for l in lines if l.attrib.get("hits","0") == "0")
    if total == 0: continue
    cov = 100.0*(total-miss)/total
    files.append((cov, miss, total, fn))
files.sort(key=lambda x:(x[0], -x[2]))
for cov, miss, total, fn in files[:15]:
    print(f"{cov:5.1f}%  missed={miss:3d}/{total:3d}  {fn}")
