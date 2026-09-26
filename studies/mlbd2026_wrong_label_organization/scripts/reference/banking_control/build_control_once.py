"""CPU-only single-candidate protocol construction. No model imports or outcomes."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, csv
from datetime import datetime, timezone
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=next(p for p in OUT.parents if (p/'AGENTS.md').exists())
B=ROOT/'reports/research/submission_mlbd2026'
V=B/'mlbd2026_banking77_local_subset_and_target_construction_freeze_v2_20260921T044209Z'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x): return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()
def write(name,x):
    with (OUT/name).open('x',encoding='utf-8') as f: json.dump(x,f,indent=2,ensure_ascii=True)

spec=json.loads((V/'09_FROZEN_STUDENT_INPUT_PACKAGE.json').read_text())
for name,item in spec['targets'].items(): assert sha(V/item['path'])==item['file_sha256'], name
payload={'project':ROOT.name,'real_sha256':sha(V/'REAL_TARGETS.npz'),
         'manipulation_contract_sha256':sha(V/'09_FROZEN_STUDENT_INPUT_PACKAGE.json'),
         'literal':'BANKING77_CONCENTRATION_MATCHED_DIRECTIONAL_IDENTITY_CONTROL_V1'}
seed=int.from_bytes(hashlib.sha256(canon(payload)).digest()[:8],'big')
write('CONSTRUCTION_PREFREEZE.json',{'timestamp_utc':datetime.now(timezone.utc).isoformat(),
 'seed':str(seed),'seed_payload':payload,'generation_spec_sha256':sha(OUT/'03_CONTROL_DETERMINISTIC_GENERATION_SPEC.md'),
 'builder_sha256':sha(Path(__file__)),'candidate_count_limit':1,'outcome_inputs':[],
 'scope':'RoBERTa + XLNet','expected_new_fits':8})
write('SINGLE_GENERATION_RECEIPT.json',{'seed':str(seed),'attempt':1,'no_redraw':True})
with np.load(V/'REAL_TARGETS.npz',allow_pickle=False) as z: raw={k:z[k].copy() for k in z.files}
ids=raw['canonical_sample_ids']; y=raw['truth_ids']; src=raw['source_prediction_ids']; n=len(y)
assert n==3066 and src.shape==(n,3) and raw['q_raw'].shape==(n,77)
assert len(set(map(str,ids)))==n and len(raw['source_keys'])==3
votes=np.stack([np.bincount(r,minlength=77) for r in src])
assert np.array_equal((votes/3).astype(np.float32),raw['q_raw'])
groups=defaultdict(list)
for i in range(n):
    key=(int(y[i]),tuple(map(int,src[i]==y[i])),tuple(sorted(Counter(map(int,src[i])).values())))
    groups[key].append(i)
donors=np.arange(n); eligible=[]
for key,indices in sorted(groups.items()):
    if len({tuple(votes[i]) for i in indices})<2: continue
    eligible.extend(indices)
    order=sorted(indices,key=lambda i:(hashlib.sha256(canon([str(seed),key,str(ids[i])])).digest(),str(ids[i])))
    for j,i in enumerate(order): donors[i]=order[(j+1)%len(order)]
ctrl=src[donors].copy(); cv=np.stack([np.bincount(r,minlength=77) for r in ctrl]); cq=(cv/3).astype(np.float32)
assert np.any(cv!=votes)
data=dict(raw);data['source_prediction_ids']=ctrl;data['q_raw']=cq;data['q_true']=cq[np.arange(n),y]
with (OUT/'CONTROL_TARGETS.npz').open('xb') as f: np.savez_compressed(f,**data)
with (OUT/'CONTROL_DONOR_MAP.csv').open('x',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['sample_id','donor_sample_id','eligible','aggregate_changed'])
    for i,j in enumerate(donors):w.writerow([ids[i],ids[j],i in eligible,bool(np.any(cv[i]!=votes[i]))])
write('CONTROL_PROVENANCE.json',{'seed':str(seed),'artifact_sha256':sha(OUT/'CONTROL_TARGETS.npz'),
 'real_sha256':payload['real_sha256'],'source_keys':raw['source_keys'].tolist(),
 'sample_rows':n,'eligible_rows':len(eligible),'eligible_groups':sum(len({tuple(votes[i]) for i in ix})>1 for ix in groups.values()),
 'candidate_count':1,'generation_inputs':[str((V/'REAL_TARGETS.npz').relative_to(ROOT)),str((V/'09_FROZEN_STUDENT_INPUT_PACKAGE.json').relative_to(ROOT))],
 'student_outcome_used_in_generation':False,'historical_student_outcomes_known_before_design':True})
print(json.dumps({'seed':str(seed),'changed':int(np.any(cv!=votes,axis=1).sum()),'eligible':len(eligible),'sha256':sha(OUT/'CONTROL_TARGETS.npz')}))
