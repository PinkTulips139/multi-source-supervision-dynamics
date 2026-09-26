from __future__ import annotations
import csv,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
READY=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_asset_and_split_readiness_v1_20260920T144526Z'
SUP=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_source_supervision_prediction_materialization_v1_20260921T042449Z/formal_supervision_predictions'
TEST=ROOT/'reports/research/submission_mlbd2026/mlbd2026_banking77_source_execution_v1_20260921T031659Z/formal_source_outputs'
SOURCES=('bert','roberta','deberta');SEEDS={'R1':2589517172764919847,'R2':3731049962840942663};N=3066;K=77
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def aggregate(hard):
 out=np.zeros((hard.shape[0],K),np.float32)
 for col in range(3):
  for row,label in enumerate(hard[:,col]):out[row,int(label)]=np.float32(out[row,int(label)]+np.float32(1/3))
 return out
def permute(base,truth,seed):
 result=np.array(base,copy=True)
 for source in range(3):
  for true_label in range(K):
   pool=[i for i in range(len(truth)) if int(truth[i])==true_label and int(base[i,source])!=true_label]
   generator=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,source+1,true_label])))
   values=np.asarray([base[i,source] for i in pool],dtype=np.int64); shuffled=generator.permutation(values.copy())
   for i,value in zip(pool,shuffled):result[i,source]=value
 return result
def semantic(ids,y,p,q):
 h=hashlib.sha256();h.update(b'BANKING77_TARGET_V1\n')
 for i in range(len(ids)):
  h.update(str(ids[i]).encode());h.update(b'\0');h.update(np.asarray([y[i]],dtype='<i8').tobytes());h.update(np.asarray(p[i],dtype='<i8').tobytes());h.update(np.asarray(q[i],dtype='<f4').tobytes())
 return h.hexdigest()
def same_wrong(p,y):
 total=0
 for row,t in zip(p,y):
  c=Counter(int(v) for v in row if int(v)!=int(t));total+=any(n>=2 for n in c.values())
 return total
def diagnostics(base,condition,y,q0,qc):
 changed=np.any(q0!=qc,axis=1); idx=np.where(changed)[0]
 def dm(q):
  positive=q>0; q64=q.astype(np.float64)
  return {'entropy':-np.sum(np.where(positive,q64*np.log(np.where(positive,q64,1.0)),0.0),axis=1),'sum_q2':np.sum(q64*q64,axis=1),'max_probability':np.max(q64,axis=1),'support_size':np.sum(positive,axis=1).astype(np.float64)}
 a,b=dm(q0),dm(qc)
 return {'changed_examples':int(changed.sum()),'changed_fraction':float(changed.mean()),'changed_only_mean_target_l1':float(np.mean(np.sum(np.abs(qc[idx].astype(np.float64)-q0[idx].astype(np.float64)),axis=1))),'same_wrong_count_real':same_wrong(base,y),'same_wrong_count_scrambled':same_wrong(condition,y),'same_wrong_count_delta':same_wrong(condition,y)-same_wrong(base,y),'all_example_deltas':{k:float(np.mean(b[k]-a[k])) for k in a},'changed_only_deltas':{k:float(np.mean((b[k]-a[k])[changed])) for k in a}}
def main():
 members=list(csv.DictReader((READY/'03_SPLIT_MEMBERSHIP_MANIFEST.csv').open(encoding='utf-8')))
 sr=sorted((x for x in members if x['role']=='STUDENT_SUPERVISION'),key=lambda x:x['canonical_sample_id']);ids=np.asarray([x['canonical_sample_id'] for x in sr]);y=np.asarray([int(x['label_id']) for x in sr],np.int64)
 hard=[]
 for key in SOURCES:
  z=np.load(SUP/f'SOURCE_{key.upper()}'/'STUDENT_SUPERVISION_PREDICTIONS.npz',allow_pickle=False);hard.append(z['predicted_ids'].astype(np.int64))
 real=np.column_stack(hard);r1=permute(real,y,SEEDS['R1']);r2=permute(real,y,SEEDS['R2']);qr=aggregate(real);q1=aggregate(r1);q2=aggregate(r2)
 manifest=json.loads((OUT/'03_TARGET_ARTIFACT_MANIFEST.json').read_text());checks={}
 for key,pred,q,filename in [('REAL',real,qr,'REAL_TARGETS.npz'),('R1',r1,q1,'DIRECTION_SCRAMBLED_R1_TARGETS.npz'),('R2',r2,q2,'DIRECTION_SCRAMBLED_R2_TARGETS.npz')]:
  z=np.load(OUT/filename,allow_pickle=False);entry=manifest['artifacts'][key]
  checks[key]={'ids_exact':bool(np.array_equal(z['canonical_sample_ids'].astype(str),ids)),'truth_exact':bool(np.array_equal(z['truth_ids'],y)),'source_predictions_exact':bool(np.array_equal(z['source_prediction_ids'],pred)),'targets_exact':bool(np.array_equal(z['q_raw'],q)),'q_true_exact':bool(np.array_equal(z['q_true'],q[np.arange(N),y])),'file_hash_exact':sha(OUT/filename)==entry['file_sha256'],'semantic_hash_exact':semantic(ids,y,pred,q)==entry['semantic_sha256']}
 # Independently reconstruct V1 local subset using pair equalities.
 tests=[]
 for key in SOURCES:
  z=np.load(TEST/f'SOURCE_{key.upper()}'/'OFFICIAL_TEST_PREDICTIONS.npz',allow_pickle=False);tests.append(z)
 tid=tests[0]['canonical_sample_ids'].astype(str);ty=tests[0]['truth_ids'];tp=np.column_stack([z['predicted_ids'] for z in tests]);local=[];comp=[]
 for i in range(3080):
  row=tp[i];t=int(ty[i]);shared=-1
  if row[0]==row[1] and row[0]!=t:shared=int(row[0])
  elif row[0]==row[2] and row[0]!=t:shared=int(row[0])
  elif row[1]==row[2] and row[1]!=t:shared=int(row[1])
  base={'canonical_sample_id':str(tid[i]),'truth_id':t}
  if shared>=0:
   agreeing='|'.join(SOURCES[j] for j in range(3) if int(row[j])==shared);local.append({**base,'shared_wrong_id':shared,'agreeing_sources':agreeing,'bert_prediction':int(row[0]),'roberta_prediction':int(row[1]),'deberta_prediction':int(row[2])})
  else:comp.append(base)
 def rh(rows):return hashlib.sha256((''.join(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n' for x in rows)).encode()).hexdigest()
 checks['local_subset']={'size':len(local)==304,'hash':rh(local)=='99eee351c028201b80f68635cc16cfdb2b7cfb5bb082f325afb646a82ef538c1','complement_size':len(comp)==2776,'complement_hash':rh(comp)=='8781c77284d4a6bd858c4f65b66f8d122800482a8e16503c764c0e3301e94153'}
 changed1=set(ids[np.any(qr!=q1,axis=1)].tolist());changed2=set(ids[np.any(qr!=q2,axis=1)].tolist());rel=json.loads((OUT/'06_R1_R2_RELATIONSHIP.json').read_text())
 checks['changed_memberships']={'r1_count':len(changed1)==rel['r1_changed']==517,'r2_count':len(changed2)==rel['r2_changed']==518,'overlap':len(changed1&changed2)==rel['changed_overlap']==421,'r1_only':len(changed1-changed2)==rel['r1_only'],'r2_only':len(changed2-changed1)==rel['r2_only'],'jaccard':abs(len(changed1&changed2)/len(changed1|changed2)-rel['jaccard'])<1e-15}
 for key,pred,q,file in [('R1',r1,q1,'04_R1_VALIDATION_AND_DIAGNOSTICS.json'),('R2',r2,q2,'05_R2_VALIDATION_AND_DIAGNOSTICS.json')]:
  expected=json.loads((OUT/file).read_text())['diagnostics']; actual=diagnostics(real,pred,y,qr,q)
  scalar_keys=('changed_examples','changed_fraction','changed_only_mean_target_l1','same_wrong_count_real','same_wrong_count_scrambled','same_wrong_count_delta')
  checks[f'{key}_diagnostics']={k:(actual[k]==expected[k] if isinstance(actual[k],int) else abs(actual[k]-expected[k])<1e-15) for k in scalar_keys}
  checks[f'{key}_diagnostics'].update({f'all_{k}':abs(actual['all_example_deltas'][k]-expected['all_example_deltas'][k])<1e-15 for k in actual['all_example_deltas']})
  checks[f'{key}_diagnostics'].update({f'changed_{k}':abs(actual['changed_only_deltas'][k]-expected['changed_only_deltas'][k])<1e-15 for k in actual['changed_only_deltas']})
 status='PASS' if all(all(v.values()) for v in checks.values()) else 'FAIL'
 result={'status':status,'implementation':'independent scalar-loop aggregation and permutation reconstruction','checks':checks,'numpy':np.__version__,'formal_artifact_hashes':{k:v['file_sha256'] for k,v in manifest['artifacts'].items()},'training':0,'student_inference':0,'gpu':0}
 (OUT/'08_INDEPENDENT_RECOMPUTATION.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(result,indent=2));raise SystemExit(0 if status=='PASS' else 1)
if __name__=='__main__':main()
