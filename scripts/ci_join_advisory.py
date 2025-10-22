#!/usr/bin/env python3
import json,pandas as pd
df=pd.read_csv("outcomes/join_counts.csv")
tail=df.tail(7)
ad={"window_days":7,
    "joined_sum":int(tail["n_joined"].sum()),
    "pending_sum":int(tail["n_pending"].sum()),
    "collisions_sum":int(tail["n_collisions"].sum()),
    "advisory":"ok" if tail["n_joined"].sum()>=2 else "low_coverage"}
open("join_advisory.json","w").write(json.dumps(ad))
print(json.dumps(ad))
