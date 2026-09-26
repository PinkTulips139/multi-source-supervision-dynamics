from __future__ import annotations

import csv, hashlib, json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4]; OUT=Path(__file__).resolve().parent
PROTO=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_protocol_freeze_v1_20260920T143149Z'
READY=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_asset_and_split_readiness_v1_20260920T144526Z'
SRCEXEC=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_source_execution_v1_20260921T031659Z'
SUP=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_source_supervision_prediction_materialization_v1_20260921T042449Z'
V1=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_local_subset_and_target_construction_freeze_v1_20260921T041141Z'
SOURCES=('bert','roberta','deberta'); K=77; N=3066
TEST_HASH={'bert':'96f1c134f074472038878af66aacdd6dff169658e97b64b49ce849506f2c612a','roberta':'4726aee8539d1cf480e138fdaf6e0013fb7a70c74be3f1419b12820727012ee4','deberta':'40cea54db46bf17668741ab7977046f4462a36627661cb6f6eb27b43439023d4'}
SUP_HASH={'bert':'a0ce8970c50f2906135d03aa635bd213472ad86103bbd2d87491cea82eba473a','roberta':'ad585c4fb365150ae79faf08e58f2ed1ce8880ef44a482aa70170aa536dcba92','deberta':'1afda8f556df263d04592cf535e9fb403b7d77825ae10be56671601eca9b9dfb'}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def cjson(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)
def semantic_hash(ids,y,preds,q):
 h=hashlib.sha256();h.update(b'BANKING77_TARGET_V1\n')
 for i in range(len(ids)):
  h.update(str(ids[i]).encode());h.update(b'\0');h.update(np.asarray([y[i]],dtype='<i8').tobytes());h.update(np.asarray(preds[i],dtype='<i8').tobytes());h.update(np.asarray(q[i],dtype='<f4').tobytes())
 return h.hexdigest()
def writej(name,x):(OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
def target(pred):
 q=np.zeros((len(pred),K),dtype=np.float32); rows=np.arange(len(pred))
 for s in range(3):q[rows,pred[:,s]]+=np.float32(1/3)
 return q
def scramble(real,y,seed):
 out=real.copy()
 for s in range(3):
  for truth in range(K):
   idx=np.where((y==truth)&(real[:,s]!=truth))[0]
   rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,s+1,truth])))
   out[idx,s]=rng.permutation(real[idx,s].copy())
 return out
def shared_wrong_count(pred,y):
 n=0
 for row,t in zip(pred,y):
  c=Counter(int(x) for x in row if int(x)!=int(t));n+=any(v>=2 for v in c.values())
 return n
def distribution_metrics(q):
 pos=q>0; entropy=-np.sum(np.where(pos,q.astype(np.float64)*np.log(np.where(pos,q.astype(np.float64),1.0)),0.0),axis=1)
 return {'entropy':entropy,'sum_q2':np.sum(q.astype(np.float64)**2,axis=1),'max_probability':np.max(q,axis=1).astype(np.float64),'support_size':np.sum(pos,axis=1).astype(np.float64)}
def invariant_checks(real,scr,y,qreal,qscr):
 checks={'sample_count':len(y)==N,'source_example_correctness':bool(np.array_equal(real==y[:,None],scr==y[:,None])),'q_true_exact':bool(np.array_equal(qreal[np.arange(N),y],qscr[np.arange(N),y])),'aggregation_exact':bool(np.array_equal(qscr,target(scr))),'equal_source_weights':True}
 checks['source_truth_wrong_marginals']=all(sorted(real[(y==t)&(real[:,s]!=t),s].tolist())==sorted(scr[(y==t)&(real[:,s]!=t),s].tolist()) for s in range(3) for t in range(K))
 checks['pairwise_both_wrong_masks']=all(np.array_equal((real[:,a]!=y)&(real[:,b]!=y),(scr[:,a]!=y)&(scr[:,b]!=y)) for a,b in ((0,1),(0,2),(1,2)))
 return checks
def diagnostics(real,scr,y,qreal,qscr):
 changed=np.any(qreal!=qscr,axis=1); idx=np.where(changed)[0]; mr=distribution_metrics(qreal);ms=distribution_metrics(qscr)
 def delta(name,mask):return float(np.mean(ms[name][mask]-mr[name][mask])) if np.any(mask) else None
 return {'changed_examples':int(changed.sum()),'changed_fraction':float(changed.mean()),'changed_sample_ids':None,'source_assignment_changed_examples':int(np.any(real!=scr,axis=1).sum()),'changed_only_mean_target_l1':float(np.mean(np.sum(np.abs(qscr[idx].astype(np.float64)-qreal[idx].astype(np.float64)),axis=1))) if len(idx) else 0.0,'same_wrong_count_real':shared_wrong_count(real,y),'same_wrong_count_scrambled':shared_wrong_count(scr,y),'same_wrong_count_delta':shared_wrong_count(scr,y)-shared_wrong_count(real,y),'all_example_deltas':{x:delta(x,np.ones(N,dtype=bool)) for x in mr},'changed_only_deltas':{x:delta(x,changed) for x in mr}}

def main():
 if np.__version__!='2.3.5':raise RuntimeError('NUMPY_AUTHORITY_MISMATCH')
 protocol=json.loads((PROTO/'FROZEN_BANKING77_PROTOCOL.json').read_text(encoding='utf-8'))
 if protocol['status']!='FROZEN':raise RuntimeError('PROTOCOL_NOT_FROZEN')
 if json.loads((SUP/'STAGE_STATUS.json').read_text())['status']!='PASS':raise RuntimeError('SUPERVISION_PREDICTIONS_NOT_PASS')
 membership_path=READY/'03_SPLIT_MEMBERSHIP_MANIFEST.csv'; membership=list(csv.DictReader(membership_path.open(encoding='utf-8')))
 sup_rows=sorted([x for x in membership if x['role']=='STUDENT_SUPERVISION'],key=lambda x:x['canonical_sample_id'])
 test_rows=sorted([x for x in membership if x['role']=='OFFICIAL_TEST'],key=lambda x:x['canonical_sample_id'])
 if len(sup_rows)!=N or len(test_rows)!=3080:raise RuntimeError('MEMBERSHIP_COUNT_FAIL')
 ids=np.asarray([x['canonical_sample_id'] for x in sup_rows]); y=np.asarray([int(x['label_id']) for x in sup_rows],dtype=np.int64)
 sup_loaded=[];test_loaded=[];input_receipt={'status':'PASS','membership_manifest_sha256':sha(membership_path),'official_test':{},'student_supervision':{}}
 for key in SOURCES:
  sp=SUP/'formal_supervision_predictions'/f'SOURCE_{key.upper()}'/'STUDENT_SUPERVISION_PREDICTIONS.npz';tp=SRCEXEC/'formal_source_outputs'/f'SOURCE_{key.upper()}'/'OFFICIAL_TEST_PREDICTIONS.npz'
  if sha(sp)!=SUP_HASH[key] or sha(tp)!=TEST_HASH[key]:raise RuntimeError('SOURCE_ARTIFACT_HASH_FAIL:'+key)
  zs=np.load(sp,allow_pickle=False);zt=np.load(tp,allow_pickle=False)
  if not np.array_equal(zs['canonical_sample_ids'].astype(str),ids) or not np.array_equal(zs['truth_ids'],y):raise RuntimeError('SUPERVISION_ALIGNMENT_FAIL:'+key)
  if not np.array_equal(zt['canonical_sample_ids'].astype(str),np.asarray([x['canonical_sample_id'] for x in test_rows])):raise RuntimeError('TEST_ALIGNMENT_FAIL:'+key)
  sup_loaded.append(zs['predicted_ids'].astype(np.int64));test_loaded.append(zt['predicted_ids'].astype(np.int64));input_receipt['student_supervision'][key]={'rows':N,'sha256':SUP_HASH[key]};input_receipt['official_test'][key]={'rows':3080,'sha256':TEST_HASH[key]}
 real=np.column_stack(sup_loaded);qreal=target(real)
 if not np.allclose(qreal.sum(1),1.0,atol=1e-6,rtol=0):raise RuntimeError('REAL_SIMPLEX_FAIL')
 # Recompute immutable V1 local subset from formal test predictions.
 testy=np.asarray([int(x['label_id']) for x in test_rows]);testp=np.column_stack(test_loaded);v1rows=[];comp=[]
 for sid,t,row in zip([x['canonical_sample_id'] for x in test_rows],testy,testp):
  counts=Counter(int(v) for v in row if int(v)!=int(t)); shared=[k for k,v in counts.items() if v>=2]; base={'canonical_sample_id':sid,'truth_id':int(t)}
  if shared:
   w=int(shared[0]);agree='|'.join(SOURCES[j] for j,v in enumerate(row) if int(v)==w and w!=int(t));v1rows.append({**base,'shared_wrong_id':w,'agreeing_sources':agree,'bert_prediction':int(row[0]),'roberta_prediction':int(row[1]),'deberta_prediction':int(row[2])})
  else:comp.append(base)
 def rowhash(rows):return hashlib.sha256((''.join(cjson(x)+'\n' for x in rows)).encode()).hexdigest()
 local_hash=rowhash(v1rows);comp_hash=rowhash(comp)
 if len(v1rows)!=304 or len(comp)!=2776 or local_hash!='99eee351c028201b80f68635cc16cfdb2b7cfb5bb082f325afb646a82ef538c1' or comp_hash!='8781c77284d4a6bd858c4f65b66f8d122800482a8e16503c764c0e3301e94153':raise RuntimeError('V1_LOCAL_INHERITANCE_FAIL')
 writej('01_INPUT_IDENTITY_GATE.json',input_receipt)
 writej('02_LOCAL_SUBSET_INHERITANCE_VALIDATION.json',{'status':'PASS','size':304,'fraction':304/3080,'truth_intents':62,'membership_sha256':local_hash,'complement_size':2776,'complement_sha256':comp_hash,'no_go_gate':'PASS','independent_recomputation':'PASS_EXACT_V1_EQUAL','semantic_boundary':'official-test evaluation membership only; no overlap calculation with supervision manipulation changed IDs'})
 # Refuse rerun/candidate regeneration in this namespace.
 for name in ('REAL_TARGETS.npz','DIRECTION_SCRAMBLED_R1_TARGETS.npz','DIRECTION_SCRAMBLED_R2_TARGETS.npz'):
  if (OUT/name).exists():raise RuntimeError('CANDIDATE_ALREADY_EXISTS:'+name)
 seeds={k:int(v['seed_decimal']) for k,v in protocol['manipulation']['seed_records'].items()}
 r1=scramble(real,y,seeds['R1']);r2=scramble(real,y,seeds['R2']);q1=target(r1);q2=target(r2)
 artifacts={}; data={'REAL':(real,qreal,'REAL_TARGETS.npz'),'R1':(r1,q1,'DIRECTION_SCRAMBLED_R1_TARGETS.npz'),'R2':(r2,q2,'DIRECTION_SCRAMBLED_R2_TARGETS.npz')}
 for key,(pred,q,name) in data.items():
  np.savez_compressed(OUT/name,canonical_sample_ids=ids,truth_ids=y,source_keys=np.asarray(SOURCES),source_prediction_ids=pred,q_raw=q,q_true=q[np.arange(N),y])
  artifacts[key]={'path':name,'file_sha256':sha(OUT/name),'semantic_sha256':semantic_hash(ids,y,pred,q),'rows':N}
 d1=diagnostics(real,r1,y,qreal,q1);d2=diagnostics(real,r2,y,qreal,q2)
 changed1=np.any(qreal!=q1,axis=1);changed2=np.any(qreal!=q2,axis=1);ids1=ids[changed1].tolist();ids2=ids[changed2].tolist();d1['changed_sample_ids']=ids1;d2['changed_sample_ids']=ids2
 inv1=invariant_checks(real,r1,y,qreal,q1);inv2=invariant_checks(real,r2,y,qreal,q2)
 if not all(inv1.values()) or not all(inv2.values()):raise RuntimeError('INVARIANT_FAIL')
 overlap=sorted(set(ids1)&set(ids2));only1=sorted(set(ids1)-set(ids2));only2=sorted(set(ids2)-set(ids1));union=set(ids1)|set(ids2)
 writej('03_TARGET_ARTIFACT_MANIFEST.json',{'status':'PASS','artifacts':artifacts,'source_order':list(SOURCES),'aggregation':'sequential float32 add of np.float32(1/3), no renormalization','created_utc':datetime.now(timezone.utc).isoformat()})
 writej('04_R1_VALIDATION_AND_DIAGNOSTICS.json',{'status':'PASS','seed':str(seeds['R1']),'candidate_count':1,'invariants':inv1,'diagnostics':d1,'artifact':artifacts['R1']})
 writej('05_R2_VALIDATION_AND_DIAGNOSTICS.json',{'status':'PASS','seed':str(seeds['R2']),'candidate_count':1,'invariants':inv2,'diagnostics':d2,'artifact':artifacts['R2']})
 writej('06_R1_R2_RELATIONSHIP.json',{'status':'PASS','membership':'STUDENT_SUPERVISION_ONLY','r1_changed':len(ids1),'r2_changed':len(ids2),'changed_overlap':len(overlap),'r1_only':len(only1),'r2_only':len(only2),'changed_union':len(union),'jaccard':len(overlap)/len(union) if union else None,'overlap_sample_ids':overlap,'r1_only_sample_ids':only1,'r2_only_sample_ids':only2,'test_local_subset_intersection':'NOT_DEFINED_DIFFERENT_MEMBERSHIPS'})
 writej('07_CONSTRUCTION_PROVENANCE.json',{'stage':'MLBD2026_BANKING77_LOCAL_SUBSET_AND_TARGET_CONSTRUCTION_FREEZE_V2','numpy':np.__version__,'protocol_sha256':sha(PROTO/'FROZEN_BANKING77_PROTOCOL.json'),'membership_sha256':sha(membership_path),'source_prediction_hashes':SUP_HASH,'realization_seeds':{k:str(v) for k,v in seeds.items()},'candidate_budget':{'R1':1,'R2':1},'student_outcome_access':False,'training':0,'student_inference':0,'gpu':0,'autodl':0})
 print(json.dumps({'status':'CONSTRUCTED_PENDING_INDEPENDENT_VALIDATION','artifacts':artifacts,'R1_changed':len(ids1),'R2_changed':len(ids2),'overlap':len(overlap)},indent=2))

if __name__=='__main__':main()
