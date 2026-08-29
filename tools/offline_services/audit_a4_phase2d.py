#!/usr/bin/env python3
import json,sys
r=json.load(open(sys.argv[1],encoding="utf-8"))
out={
 "schemaVersion":1,
 "route":r["route"],
 "status":"phase2d-a4-certification",
 "certifiedA4":r["certifiedA4"],
 "total":r["total"],
 "wrongMotorway":r["wrongMotorway"],
 "needsDirectionOrientation":True,
 "note":"This phase certifies A4 topology and cleans duplicate ramp IDs. Paris/Strasbourg semantic direction is intentionally not guessed from coordinates."
}
json.dump(out,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False))
