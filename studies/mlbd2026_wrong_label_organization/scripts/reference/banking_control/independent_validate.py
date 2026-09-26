"""Independent Counter/list reconstruction; reads, never regenerates candidate artifact."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,json,hashlib,math
import numpy as np
O=Path(__file__).resolve().parent
R=next(p for p in O.parents if (p/'AGENTS.md').exists())
V=R/'reports/research/submission_mlbd2026/mlbd2026_banking77_local_subset_and_target_construction_freeze_v2_20260921T044209Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode('utf-8')
with np.load(V/'REAL_TARGETS.npz',allow_pickle=False) as z:a={k:z[k] for k in z.files}
with np.load(O/'CONTROL_TARGETS.npz',allow_pickle=False) as z:b={k:z[k] for k in z.files}
freeze=json.loads((O/'CONSTRUCTION_PREFREEZE.json').read_text()); seed=str(int.from_bytes(hashlib.sha256(enc(freeze['seed_payload'])).digest()[:8],'big'))
assert seed==freeze['seed']
ids=a['canonical_sample_ids'].tolist();truth=a['truth_ids'].tolist();sources=a['source_prediction_ids'].tolist(); actual=b['source_prediction_ids'].tolist()
assert set(a)==set(b)
for k in ['canonical_sample_ids','truth_ids','source_keys']:assert np.array_equal(a[k],b[k]),k
g=defaultdict(list)
for i,(y,row) in enumerate(zip(truth,sources)):
    g[(y,tuple(int(v==y) for v in row),tuple(sorted(Counter(row).values())))].append(i)
expected=[list(row) for row in sources];donor=list(range(len(ids)))
for key,rows in g.items():
    if len({tuple(sorted(Counter(sources[i]).items())) for i in rows})<=1:continue
    tagged=[(hashlib.sha256(enc([seed,key,ids[i]])).hexdigest(),ids[i],i) for i in rows]
    sequence=[t[2] for t in sorted(tagged)]
    for left,right in zip(sequence,sequence[1:]+sequence[:1]):expected[left]=list(sources[right]);donor[left]=right
assert expected==actual
maps=list(csv.DictReader((O/'CONTROL_DONOR_MAP.csv').open(encoding='utf-8')))
assert all(m['sample_id']==ids[i] and m['donor_sample_id']==ids[donor[i]] for i,m in enumerate(maps))
metrics={'entropy':[],'sum_q2':[],'support':[],'max_probability':[]};l1=[];changed=[]
pair_before=pair_after=unique_before=unique_after=0
for i,(y,r,c) in enumerate(zip(truth,sources,actual)):
    cr,cc=Counter(r),Counter(c)
    assert [v==y for v in r]==[v==y for v in c]
    assert sorted(cr.values())==sorted(cc.values())
    assert cr[y]==cc[y]
    eq=np.asarray([cc[k]/3 for k in range(77)],dtype=np.float32)
    assert np.array_equal(eq,b['q_raw'][i]) and b['q_true'][i]==eq[y]
    assert a['q_true'][i]==b['q_true'][i]
    assert np.array_equal(np.sort(a['q_raw'][i]),np.sort(eq))
    assert np.array_equal(np.sort(.9*a['q_raw'][i]+.1/77),np.sort(.9*eq+.1/77))
    ischanged=cr!=cc
    if ischanged:changed.append(ids[i]);l1.append(sum(abs(cr[k]-cc[k])/3 for k in set(cr)|set(cc)))
    def vals(count):
        p=[v/3 for v in sorted(count.values()) if v]
        return [-sum(z*math.log(z) for z in p),sum(z*z for z in p),len(p),max(p)]
    for key,u,v in zip(metrics,vals(cr),vals(cc)):metrics[key].append(v-u)
    pr=sum(r[s]==r[t] and r[s]!=y for s in range(3) for t in range(s+1,3));pc=sum(c[s]==c[t] and c[s]!=y for s in range(3) for t in range(s+1,3))
    pair_before+=pr;pair_after+=pc;unique_before+=pr>0;unique_after+=pc>0
for s in range(3):
    for y in set(truth):
        assert Counter(row[s] for row,t in zip(sources,truth) if t==y and row[s]!=y)==Counter(row[s] for row,t in zip(actual,truth) if t==y and row[s]!=y)
assert changed
assert sha(O/'CONTROL_TARGETS.npz')==json.loads((O/'CONTROL_PROVENANCE.json').read_text())['artifact_sha256']
result={'status':'PASS','independent_recomputation':'PASS_EXACT_ARRAY_AND_DONOR_EQUAL',
 'rows':len(ids),'seed':seed,'changed_examples':len(changed),'changed_fraction':len(changed)/len(ids),
 'changed_only_mean_L1_exact_votes':sum(l1)/len(l1),
 'changed_only_mean_L1_serialized_float32':float(np.abs(a['q_raw'].astype(float)-b['q_raw'].astype(float)).sum(1)[np.any(a['q_raw']!=b['q_raw'],axis=1)].mean()),
 'maximum_absolute_residual':{k:max(map(abs,v)) for k,v in metrics.items()},
 'changed_only_mean_delta':{k:float(np.asarray(v)[np.any(a['q_raw']!=b['q_raw'],axis=1)].mean()) for k,v in metrics.items()},
 'wrong_label_marginal_residual':0,'vote_multiplicity_residual':0,'correctness_residual':0,'q_true_residual':0,
 'same_wrong_source_pair_events':{'REAL':pair_before,'CONTROL':pair_after},
 'examples_with_at_least_one_same_wrong_pair':{'REAL':unique_before,'CONTROL':unique_after},
 'invariants':'ALL_EXACT_PASS','raw_and_smoothed_sorted_probabilities':'EXACT_PASS',
 'changed_sample_ids':changed,'CONTROL_sha256':sha(O/'CONTROL_TARGETS.npz')}
with (O/'02_CONTROL_INVARIANTS.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='changed_sample_ids'},indent=2))
