#!/usr/bin/env python3
import os,glob
d=os.environ.get("DAY","")
print("DAY=",d)
print("joined_files=", sorted(glob.glob("outcomes/day=*/joined.csv"))[-5:])
