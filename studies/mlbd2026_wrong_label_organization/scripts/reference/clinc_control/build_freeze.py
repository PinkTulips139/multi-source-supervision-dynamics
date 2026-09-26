"""Single CPU-only constructive control and immutable report builder. No model imports."""
from pathlib import Path
import csv, json, hashlib, gzip, datetime, itertools
from collections import Counter, defaultdict
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
B=ROOT/'reports/research/student_consequence'
MASTER=ROOT/'reports/research/submission_mlbd2026/mlbd2026_submission_scope_mechanism_and_critical_experiment_master_design_v1_20260920T095157Z'
P=B/'roberta_mechanism_multi_seed_confirmatory_protocol_design_and_freeze_v1_20260911T092505Z'
M=B/'real_clinc150_minimal_student_consequence_manipulation_preflight_v1_resume_execution_20260907T085125Z'
REUSE=B/'independent_manipulation_realization_student_validation_asset_reuse_and_preflight_remediation_review_v1_20260916T012432Z'
RETR=B/'independent_manipulation_realization_remote_asset_retrieval_protocol_v1_20260916T020446Z'
SEEDS=[167174636,1852328752,1231418446,1461753708]
INPUTS={}
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def bind(p,expected=None):
 digest=sha(p)
 if expected is not None: assert digest==expected,(str(p),'hash mismatch')
 x={'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'bytes':p.stat().st_size}
 INPUTS[x['path']]=x
 return x
def read(p):
 bind(p)
 return json.loads(p.read_text(encoding='utf-8-sig'))
def canonical(x):return json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(',',':')).encode('utf-8')
def dump(name,x):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def md(name,s):
 with (OUT/name).open('x',encoding='utf-8') as f:f.write(s)
def csvout(name,rows):
 with (OUT/name).open('x',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def load(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k].copy() for k in z.files}
def votes(a):return np.stack([np.bincount(row,minlength=150) for row in a])
def pattern(row):return tuple(sorted(Counter(map(int,row)).values()))
def groupkey(row,y):return (int(y),tuple(int(v==y) for v in row),pattern(row))
def metrics(v):
 q=v/3.; log=np.zeros_like(q);np.log(q,out=log,where=q>0)
 return {'entropy':-(q*log).sum(1),'sum_q2':(q*q).sum(1),'max_probability':q.max(1),'support':(v>0).sum(1)}

def validate(real,ctl):
 a=real['source_predictions'];b=ctl['source_predictions'];y=real['truth_ids'];av=votes(a);bv=votes(b)
 checks={}
 for k in ['example_ids','truth_ids','source_weights']:checks[k]=bool(np.array_equal(real[k],ctl[k]))
 checks['source_prediction_shape']=b.shape==(3000,3)
 checks['source_label_range']=bool(((b>=0)&(b<150)).all())
 checks['correctness_identity']=bool(np.array_equal(a==y[:,None],b==y[:,None]))
 checks['truth_votes']=bool(np.array_equal(av[np.arange(3000),y],bv[np.arange(3000),y]))
 checks['integer_vote_multiplicity']=bool(np.array_equal(np.sort(av,axis=1),np.sort(bv,axis=1)))
 checks['source_truth_wrong_marginals']=all(Counter(a[(y==t)&(a[:,s]!=y),s].tolist())==Counter(b[(y==t)&(b[:,s]!=y),s].tolist()) for s in range(3) for t in range(150))
 checks['target_reconstruction']=bool(np.array_equal(ctl['targets'],(bv/3).astype(np.float32)))
 checks['raw_sorted_values']=bool(np.array_equal(np.sort(real['targets'],axis=1),np.sort(ctl['targets'],axis=1)))
 checks['runtime_smoothed_sorted_values']=bool(np.array_equal(np.sort(.9*real['targets']+.1/150,axis=1),np.sort(.9*ctl['targets']+.1/150,axis=1)))
 checks['finite_simplex']=bool(np.isfinite(ctl['targets']).all() and np.allclose(ctl['targets'].sum(1),1,rtol=0,atol=1e-7))
 checks['nontrivial']=bool(np.any(av!=bv))
 assert all(checks.values()),checks
 return checks

def main():
 # Exclusive receipt prevents any second candidate invocation.
 dump('RUN_RECEIPT.json',{'started_utc':now(),'candidate_limit':1,'training':0,'inference':0,'GPU':0,'Git_writes':0})
 summary=read(MASTER/'TARGET_SMOOTHNESS_SUMMARY.json');protocol=read(P/'FROZEN_ROBERTA_MULTI_SEED_CONFIRMATORY_PROTOCOL.json')
 assert protocol['FINAL_CONFIRMATORY_SEEDS']==SEEDS
 original=read(M/'MANIPULATION_PREFLIGHT_SPEC.json')
 assert [x['key'] for x in original['sources']]==['bert','roberta','deberta']
 z={}
 for k,r in summary['inputs'].items():
  p=ROOT/Path(r['path'].replace('\\','/'));bind(p,r['sha256']);z[k]=load(p)
 a=z['REAL']['source_predictions'];y=z['REAL']['truth_ids'];ids=z['REAL']['example_ids'];av=votes(a)
 assert a.shape==(3000,3) and len(set(ids))==3000
 assert np.array_equal(z['REAL']['targets'],(av/3).astype(np.float32))
 groups=defaultdict(list)
 for i in range(3000):groups[groupkey(a[i],y[i])].append(i)
 eligible={k:idx for k,idx in groups.items() if len({tuple(av[i]) for i in idx})>1}
 assert eligible,'FAIL_CLOSED: no witness in chosen constructive family; broader exact solver required before impossibility claim'
 eligible_rows=[{'group':json.dumps(k),'n':len(idx),'distinct_targets':len({tuple(av[i]) for i in idx}),'example_ids':'|'.join(ids[idx])} for k,idx in sorted(eligible.items())]
 csvout('ELIGIBLE_GROUPS.csv',eligible_rows)
 # This is a proof from REAL tuples, not a generated candidate.
 dump('01_EXACT_FEASIBILITY.json',{'feasible':True,'proof':'nonconstant aggregate triple groups + one-step cyclic bijection','eligible_groups':len(eligible),'eligible_rows':sum(map(len,eligible.values())),'global_maximum_support':'NOT_OPTIMIZED_NOT_CLAIMED','constraints_relaxed':[]})
 audits={};trans=[]
 am=metrics(av)
 for k in ['R1','R2']:
  v=votes(z[k]['source_predictions']);m=metrics(v);changed=np.any(v!=av,axis=1)
  assert int(changed.sum())=={'R1':70,'R2':85}[k]
  assert np.array_equal(v[np.arange(3000),y],av[np.arange(3000),y])
  assert np.array_equal(z[k]['example_ids'],ids)
  audits[k]={'changed_count':int(changed.sum()),'q_true_exact':True,'metrics':{}}
  for name in am:
   d=m[name]-am[name]
   audits[k]['metrics'][name]={'all_mean_delta':float(d.mean()),'changed_mean_delta':float(d[changed].mean()),'changed_min_delta':float(d[changed].min()),'changed_max_delta':float(d[changed].max()),'changed_positive':int((d[changed]>1e-12).sum()),'changed_negative':int((d[changed]<-1e-12).sum()),'changed_zero':int((abs(d[changed])<=1e-12).sum())}
  c=Counter((pattern(a[i]),pattern(z[k]['source_predictions'][i])) for i in np.where(changed)[0])
  trans.extend({'condition':k,'REAL_vote_partition':str(aa),'scrambled_vote_partition':str(bb),'count':n,'changed_only':True} for (aa,bb),n in sorted(c.items()))
 dump('02_CHANGED_ONLY_SMOOTHNESS.json',{'direction':'SCRAMBLED minus REAL','metric_basis':'exact integer source votes / 3 in FP64; raw pre-smoothing','conditions':audits,'legacy_warning':'master vote_pattern helper labels all-correct rows wrong2 and merges distinct wrong counts; do not use those strings. This audit uses true sorted vote partitions.'})
 csvout('VOTE_PATTERN_TRANSITIONS.csv',trans)
 seed_payload={'project':ROOT.name,'real_sha256':summary['inputs']['REAL']['sha256'],'manipulation_contract_sha256':sha(M/'MANIPULATION_PREFLIGHT_SPEC.json'),'literal':'CONCENTRATION_MATCHED_DIRECTIONAL_IDENTITY_CONTROL_V1'}
 seed_hash=hashlib.sha256(canonical(seed_payload)).hexdigest();seed=int.from_bytes(bytes.fromhex(seed_hash)[:8],'big')
 frozen={'freeze_utc':now(),'seed_payload':seed_payload,'seed_digest':seed_hash,'seed':seed,'canonicalization':'UTF8 ensure_ascii=True sort_keys=True separators comma/colon no newline','mapping':'first 8 digest bytes unsigned big-endian; no modulus','algorithm':bind(OUT/'CONSTRUCTION_PREFREEZE.md'),'implementation_sha256':sha(Path(__file__)),'eligible_set_sha256':sha(OUT/'ELIGIBLE_GROUPS.csv'),'realizations':1,'outcome_inputs':[]}
 dump('03_CONSTRUCTION_FREEZE.json',frozen)
 # One and only one materialization; no diagnostics read in this construction.
 b=a.copy();donor=np.arange(3000)
 for key,idx in sorted(eligible.items()):
  order=sorted(idx,key=lambda i:(hashlib.sha256(canonical([str(seed),key,str(ids[i])])).digest(),str(ids[i])))
  for j,i in enumerate(order):donor[i]=order[(j+1)%len(order)];b[i]=a[donor[i]]
 bv=votes(b);ctl={k:v.copy() for k,v in z['REAL'].items()};ctl['source_predictions']=b;ctl['targets']=(bv/3).astype(np.float32)
 with (OUT/'CONTROL_SUPERVISION.npz').open('xb') as f:np.savez_compressed(f,**ctl)
 checks=validate(z['REAL'],load(OUT/'CONTROL_SUPERVISION.npz'))
 changed=np.any(bv!=av,axis=1)
 csvout('CONTROL_ASSIGNMENT_MAP.csv',[{'example_id':str(ids[i]),'truth_id':int(y[i]),'donor_example_id':str(ids[donor[i]]),'REAL_sources':str(a[i].tolist()),'CONTROL_sources':str(b[i].tolist()),'target_changed':bool(changed[i])} for i in range(3000)])
 pair_counts={}
 for s,t in itertools.combinations(range(3),2):
  wrong=(a[:,s]!=y)&(a[:,t]!=y)
  pair_counts[f'{s}-{t}']={'both_wrong':int(wrong.sum()),'REAL_same_wrong':int((wrong&(a[:,s]==a[:,t])).sum()),'CONTROL_same_wrong':int((wrong&(b[:,s]==b[:,t])).sum())}
 dump('04_CONTROL_VALIDATION.json',{'status':'PASS','checks':checks,'changed_count':int(changed.sum()),'changed_fraction':float(changed.mean()),'pairwise_counts':pair_counts,'source_cell_changes':int((a!=b).sum()),'all_row_entropy_max_abs_delta':float(abs(metrics(bv)['entropy']-am['entropy']).max())})
 dump('CONTROL_PROVENANCE.json',{'created_utc':now(),'condition':'CONCENTRATION_MATCHED_DIRECTIONAL_IDENTITY_CONTROL','realization_id':'CM_DIRECTIONAL_IDENTITY_CONTROL_V1_SINGLE','seed':seed,'construction_freeze_sha256':sha(OUT/'03_CONSTRUCTION_FREEZE.json'),'supervision':bind(OUT/'CONTROL_SUPERVISION.npz'),'assignment_map_sha256':sha(OUT/'CONTROL_ASSIGNMENT_MAP.csv'),'source_order':['bert','roberta','deberta'],'raw_target':'equal mean of three one-hot labels','changed_count':int(changed.sum()),'candidate_count':1,'regeneration_count':0,'student_outcome_access_for_construction':False})
 # Reuse audit reads hashes and identity metadata only, no outcome-based control selection.
 matrixpath=REUSE/'02_REAL_ASSET_MATRIX.csv';bind(matrixpath)
 rows=list(csv.DictReader(matrixpath.open(encoding='utf-8-sig')));verified=[]
 for r in rows:
  if r['arm']=='REAL' and r['local_present']=='true' and r['expected_sha256']:
   rec=bind(ROOT/Path(r['local_path'].replace('\\','/')),r['expected_sha256']);verified.append({'seed':r['seed'],'asset_name':r['asset_name'],**rec})
 assert set(int(r['seed']) for r in verified)==set(SEEDS)
 csvout('REAL_REUSE_HASH_AUDIT.csv',verified)
 pairing=read(P/'PER_SEED_PAIRING_CONTRACT.json');orders=read(P/'PER_SEED_ORDER_INDEX.json')
 mappingpath=RETR/'06_LOCAL_PATH_MAPPING.csv';bind(mappingpath)
 mappings=list(csv.DictReader(mappingpath.open(encoding='utf-8-sig')))
 execution=[]
 for s in SEEDS:
  k=str(s);r=pairing['initial_states'][k]
  for name in ['manifest','pair_preflight','order']:
   rec=r[name];bind(ROOT/Path(rec['local_path'].replace('\\','/')),rec['sha256'])
  row=next(x for x in mappings if x['asset_id']==f'INITIAL_STATE_{s}')
  initial=bind(ROOT/row['local_path'],r['sha256'])
  realdir=B/f'roberta_mechanism_multi_seed_confirmatory_execution_v1_20260911T095254Z/SEED_{s}/REAL'
  validator=read(realdir/'VALIDATOR.json');status=read(realdir/'STATUS.json');complete=read(realdir/'TRAINING_COMPLETE.json')
  assert validator['status']=='PASS' and validator['seed']==s and validator['initial_sha256']==r['sha256']
  assert validator['initial_digest']==r['state_digest'] and validator['order_sha256']==r['order']['sha256']
  assert status['status']=='SUCCESS' and complete['status']=='SUCCESS'
  assert complete['epochs_completed']==35 and complete['optimizer_steps']==2100
  execution.append({'seed':s,'new_condition':'CONCENTRATION_MATCHED_DIRECTIONAL_IDENTITY_CONTROL','new_fits':1,'reuse_REAL_prediction':bind(realdir/'TEST_PREDICTIONS.npz'),'reuse_REAL_metrics':bind(realdir/'METRICS.json'),'validator_evidence':validator,'status_evidence':status,'completion_evidence':complete,'initial_state':initial,'state_tensor_digest':r['state_digest'],'order':r['order'],'future_output_namespace':f'NEW_AUTHORIZED_EXECUTION_STAGE/SEED_{s}/CONTROL'})
 # Bind current text/mapping assets as immutable inputs. No text or test outcomes are inspected.
 for name in ['data','mapping']:
  row=next(x for x in mappings if x['asset_id']==name);bind(ROOT/row['local_path'],row['sha256'])
 subset=protocol['outcomes']['secondary']['artifact'];subsetpath=ROOT/Path(subset['local_path'].replace('\\','/'));subsetrec=bind(subsetpath,subset['sha256'])
 with gzip.open(subsetpath,'rt',encoding='utf-8-sig') as f:subrows=list(csv.DictReader(f))
 assert len(subrows)==129
 dump('05_SEED_INIT_ORDER_REAL_REUSE.json',{'REAL_reuse':'APPROVED','new_REAL_fits':0,'new_CONTROL_fits':4,'total_new_fits':4,'pairs':execution,'same_seed_initial_RNG_rule':pairing['rng_seed_definition'],'order_rule':pairing['order_algorithm'],'optimizer':'fresh each CONTROL arm; no trained state inheritance'})
 endpoint={'Primary':'mean_test4500 NLL_REAL - mean_test4500 NLL_CONTROL','Secondary':'mean_frozen129 [p_REAL(shared_wrong)-p_CONTROL(shared_wrong)]','LocalNLL':'mean_frozen129 [NLL_REAL-NLL_CONTROL]','Complement':'mean_complement4371 [NLL_REAL-NLL_CONTROL]','positive_nll':'REAL worse','positive_secondary':'REAL allocates more to predefined shared-wrong label','main_diagnostic_estimand':'LocalNLL REAL minus CONTROL conditional on this one exact concentration-matched control, learner, dataset and four training seeds','secondary_not_interchangeable_with_localnll':True,'global_positive_gate':False,'frozen129':subsetrec,'complement_count':4371,'test_contract':protocol['outcomes']['test'],'no_new_subset':True}
 dump('06_ENDPOINT_CONTRACT.json',endpoint)
 dump('FROZEN_DIAGNOSTIC_CONTROL_PROTOCOL.json',{'status':'FROZEN','stage':'MLBD2026_DIAGNOSTIC_CONTROL_PROTOCOL_FREEZE_V1','freeze_utc':now(),'construction':frozen,'control_provenance_sha256':sha(OUT/'CONTROL_PROVENANCE.json'),'supervision':bind(OUT/'CONTROL_SUPERVISION.npz'),'seeds':SEEDS,'model':protocol['model'],'recipe':protocol['recipe'],'batch_size':protocol['batch_size'],'soft_target_runtime_authority':'q=.9*q_raw+.1/150; mean(-sum(q*log_softmax(logits))); original one_hot formula in CLEAN-related historical field is not the REAL/control target','pairing_authority':bind(P/'PER_SEED_PAIRING_CONTRACT.json'),'new_fits':4,'REAL_reuse':'APPROVED','endpoints':endpoint,'interpretation_file':'08_INTERPRETATION_AND_RECOMPUTATION_PLAN.md','training_authorized':False,'historical_master_8_fits':'superseded by current explicit REAL reuse request and rehashed saved results','model_execution_readiness':'NOT_EVALUATED_FUTURE_STAGE_REQUIRED'})
 # Validation negative tests alter only transient arrays, never serialized targets.
 tests={}
 for name in ['wrong_truth','wrong_correctness','wrong_target','wrong_identity','identity_control']:
  bad={k:v.copy() for k,v in ctl.items()}
  if name=='wrong_truth':bad['truth_ids'][0]=(bad['truth_ids'][0]+1)%150
  elif name=='wrong_correctness':bad['source_predictions'][0,0]=(int(y[0])+1)%150 if a[0,0]==y[0] else int(y[0])
  elif name=='wrong_target':bad['targets'][0,0]+=.01
  elif name=='wrong_identity':bad['example_ids'][0]='tampered'
  else:bad=z['REAL']
  try:validate(z['REAL'],bad);tests[name]='FAIL_ACCEPTED_INVALID'
  except AssertionError:tests[name]='PASS_REJECTED'
 assert all(x=='PASS_REJECTED' for x in tests.values())
 dump('VALIDATOR_NEGATIVE_TESTS.json',tests)
 # Generate a concise numerical receipt; prose reports are completed separately.
 dump('NUMERICAL_RECEIPT.json',{'control_seed':seed,'eligible_groups':len(eligible),'eligible_rows':sum(map(len,eligible.values())),'changed_count':int(changed.sum()),'control_raw_changed_mean_L1':float(np.abs((bv-av)/3).sum(1)[changed].mean()),'smoothness':audits,'pairs':pair_counts,'REAL_saved_assets_rehashed':len(verified),'frozen129_sha256':subsetrec['sha256']})
 dump('INPUT_RECEIPT.json',list(INPUTS.values()))
 print(json.dumps({'status':'CONSTRUCTION_AND_ASSETS_PASS','seed':seed,'changed':int(changed.sum()),'eligible_rows':sum(map(len,eligible.values())),'smoothness':audits,'real_assets_rehashed':len(verified),'pair_counts':pair_counts}))

if __name__=='__main__': main()
