"""Read-only independent integer constraint verifier. Does not generate candidates."""
from pathlib import Path
from collections import Counter
import hashlib,json,csv
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(4194304),b''):h.update(x)
 return h.hexdigest()
def main():
 protocol=json.loads((HERE/'FROZEN_DIAGNOSTIC_CONTROL_PROTOCOL.json').read_text(encoding='utf-8'))
 freeze=json.loads((HERE/'03_CONSTRUCTION_FREEZE.json').read_text(encoding='utf-8'))
 provenance=json.loads((HERE/'CONTROL_PROVENANCE.json').read_text(encoding='utf-8'))
 assert sha(HERE/'CONTROL_SUPERVISION.npz')==protocol['supervision']['sha256']==provenance['supervision']['sha256']
 assert sha(HERE/'03_CONSTRUCTION_FREEZE.json')==provenance['construction_freeze_sha256']
 assert sha(HERE/'CONTROL_PROVENANCE.json')==protocol['control_provenance_sha256']
 assert sha(HERE/'CONSTRUCTION_PREFREEZE.md')==freeze['algorithm']['sha256']
 assert sha(HERE/'build_freeze.py')==freeze['implementation_sha256']
 receipt=json.loads((HERE/'INPUT_RECEIPT.json').read_text(encoding='utf-8'))
 for item in receipt:assert sha(ROOT/item['path'])==item['sha256'],item['path']
 realpath=next(ROOT/x['path'] for x in receipt if x['sha256']==freeze['seed_payload']['real_sha256'])
 with np.load(realpath,allow_pickle=False) as f:r={k:f[k] for k in f.files}
 with np.load(HERE/'CONTROL_SUPERVISION.npz',allow_pickle=False) as f:c={k:f[k] for k in f.files}
 mapping=list(csv.DictReader((HERE/'CONTROL_ASSIGNMENT_MAP.csv').open(encoding='utf-8')))
 assert len(mapping)==3000 and len(set(r['example_ids']))==3000
 assert c.keys()==r.keys() and c['targets'].dtype==np.float32
 for key in ['example_ids','truth_ids','source_weights']:assert np.array_equal(r[key],c[key])
 assert np.array_equal(r['source_weights'],np.ones(3)/3)
 assert Counter(map(int,r['truth_ids']))==Counter({i:20 for i in range(150)})
 idindex={str(x):i for i,x in enumerate(r['example_ids'])};donors=[];changed=0
 for i,(a,b) in enumerate(zip(r['source_predictions'],c['source_predictions'])):
  truth=int(r['truth_ids'][i]);ca=Counter(map(int,a));cb=Counter(map(int,b))
  assert sorted(ca.values())==sorted(cb.values())
  assert all((int(x)==truth)==(int(y)==truth) for x,y in zip(a,b))
  assert ca[truth]==cb[truth]
  assert len(ca)==len(cb) and sum(x*x for x in ca.values())==sum(x*x for x in cb.values())
  expected=np.zeros(150,dtype=np.float32)
  for label,count in cb.items():expected[label]=count/3
  assert np.array_equal(expected,c['targets'][i])
  row=mapping[i];assert row['example_id']==r['example_ids'][i]
  j=idindex[row['donor_example_id']];donors.append(j)
  assert np.array_equal(b,r['source_predictions'][j]) and r['truth_ids'][j]==truth
  changed+=ca!=cb
 assert sorted(donors)==list(range(3000))
 assert changed==provenance['changed_count'] and changed>0
 for source in range(3):
  for truth in range(150):
   mask=r['truth_ids']==truth
   assert Counter(map(int,r['source_predictions'][mask,source]))==Counter(map(int,c['source_predictions'][mask,source]))
 assert np.array_equal(np.sort(r['targets'],axis=1),np.sort(c['targets'],axis=1))
 assert np.array_equal(np.sort(.9*r['targets']+.1/150,axis=1),np.sort(.9*c['targets']+.1/150,axis=1))
 # Check the precise frozen deterministic donor rule without constructing any new supervision.
 groups={}
 for i,row in enumerate(r['source_predictions']):
  key=(int(r['truth_ids'][i]),tuple(int(v==r['truth_ids'][i]) for v in row),tuple(sorted(Counter(map(int,row)).values())))
  groups.setdefault(key,[]).append(i)
 def canon(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode()
 digest=hashlib.sha256(canon(freeze['seed_payload'])).hexdigest()
 assert digest==freeze['seed_digest'] and int.from_bytes(bytes.fromhex(digest)[:8],'big')==freeze['seed']
 for key,idx in groups.items():
  unique={tuple(sorted(Counter(map(int,r['source_predictions'][i])).items())) for i in idx}
  if len(unique)>1:
   order=sorted(idx,key=lambda i:(hashlib.sha256(canon([str(freeze['seed']),key,str(r['example_ids'][i])])).digest(),str(r['example_ids'][i])))
   for n,i in enumerate(order):assert donors[i]==order[(n+1)%len(order)]
  else:
   for i in idx:assert donors[i]==i
 print(json.dumps({'status':'PASS','changed_count':changed,'historical_and_bound_files_rehashed':len(receipt),'training':0,'inference':0,'GPU':0,'Git_writes':0}))
if __name__=='__main__':main()
