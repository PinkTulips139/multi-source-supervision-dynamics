"""Frozen-spec CPU manipulation only. No model/network imports or outcome inputs.
Modes: fixtures (invented arrays only), generate (exclusive one-shot).
"""
import argparse
import copy
import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = HERE.parent / "independent_manipulation_realization_protocol_freeze_and_preflight_v1_20260915T103632Z"
ORIG = HERE.parent / "real_clinc150_minimal_student_consequence_manipulation_preflight_v1_resume_execution_20260907T085125Z"
SOURCES = ["bert", "roberta", "deberta"]
SEED = 6837507672092454859

def now():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_new(name, obj):
    dest = (HERE / name).resolve()
    if dest.parent != HERE:
        raise ValueError("Output escape")
    with dest.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")

def load_npz(path):
    with np.load(path, allow_pickle=False) as a:
        return {k:a[k].copy() for k in a.files}

def targets(pred, k):
    q = np.zeros((len(pred), k), dtype=np.float32)
    for j in range(3):
        q[np.arange(len(pred)), pred[:,j]] += np.float32(1/3)
    return q

def checks(real, cand, source_order, k):
    """No diagnostic values enter this validator."""
    required = {"example_ids","truth_ids","source_predictions","targets","source_weights","control_seed"}
    out = {"required_keys":required.issubset(cand)}
    if not out["required_keys"]:
        return out
    n = len(real["truth_ids"])
    out["shapes_dtypes"] = all(cand[x].shape==real[x].shape and cand[x].dtype==real[x].dtype for x in real)
    out["seed_shape_dtype"] = cand["control_seed"].shape==(1,) and cand["control_seed"].dtype==np.int64
    out["source_order"] = source_order==SOURCES
    out["ids"] = np.array_equal(real["example_ids"],cand["example_ids"]) and len(set(cand["example_ids"].tolist()))==n
    out["truth"] = np.array_equal(real["truth_ids"],cand["truth_ids"])
    out["weights"] = np.array_equal(real["source_weights"],cand["source_weights"]) and np.array_equal(cand["source_weights"],np.array([1/3]*3))
    if not out["shapes_dtypes"]:
        return {x:bool(y) for x,y in out.items()}
    y, rp, cp = real["truth_ids"],real["source_predictions"],cand["source_predictions"]
    out["ranges"] = bool(((cp>=0)&(cp<k)).all())
    out["correct_error_identity"] = np.array_equal(rp==y[:,None],cp==y[:,None])
    out["correct_assignments"] = bool((cp[rp==y[:,None]]==rp[rp==y[:,None]]).all())
    out["wrong_multisets"] = all(Counter(rp[(y==t)&(rp[:,j]!=t),j].tolist())==Counter(cp[(y==t)&(cp[:,j]!=t),j].tolist()) for j in range(3) for t in range(k))
    out["quality_counts"] = np.array_equal((rp==y[:,None]).sum(0),(cp==y[:,None]).sum(0))
    out["confusion_counts"] = out["ranges"] and all(np.array_equal(np.bincount(y*k+rp[:,j],minlength=k*k),np.bincount(y*k+cp[:,j],minlength=k*k)) for j in range(3))
    out["both_wrong_counts"] = all(np.sum((rp[:,a]!=y)&(rp[:,b]!=y))==np.sum((cp[:,a]!=y)&(cp[:,b]!=y)) for a,b in ((0,1),(0,2),(1,2)))
    q=cand["targets"]
    out["finite_nonnegative_normalized"] = bool(np.isfinite(q).all() and (q>=0).all() and np.all(np.abs(q.sum(1)-1)<=1e-6))
    out["raw_aggregation"] = out["ranges"] and np.array_equal(q,targets(cp,k))
    return {x:bool(y) for x,y in out.items()}

def construct(real, seed, k):
    """One candidate construction; exactly one permutation call per group."""
    rp=real["source_predictions"]
    cp=rp.copy()
    y=real["truth_ids"]
    transcript=[]
    for j in range(3):
        for t in range(k):
            idx=np.flatnonzero((y==t)&(rp[:,j]!=t))
            values=rp[idx,j].copy()
            rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,j+1,t])))
            assigned=rng.permutation(values)
            cp[idx,j]=assigned
            # Canonical occurrence matching records a bijection even with duplicate labels.
            positions=defaultdict(deque)
            for row,value in zip(idx.tolist(),values.tolist()):
                positions[value].append(row)
            donors=[positions[v].popleft() for v in assigned.tolist()]
            transcript.append({"source":SOURCES[j],"source_index":j+1,"truth_id":t,
                               "destination_rows":idx.tolist(),"donor_rows":donors})
    candidate={x:real[x].copy() for x in real}
    candidate["source_predictions"]=cp
    candidate["targets"]=targets(cp,k)
    candidate["control_seed"]=np.array([seed],dtype=np.int64)
    return candidate,transcript

def replay_check(real,cand,transcript,seed,k):
    """Read-only exact identity replay. Never writes or selects a candidate."""
    if len(transcript)!=3*k or cand["control_seed"].tolist()!=[seed]:
        return False
    y,rp,cp=real["truth_ids"],real["source_predictions"],cand["source_predictions"]
    for j in range(3):
        for t in range(k):
            tr=transcript[j*k+t]
            idx=np.flatnonzero((y==t)&(rp[:,j]!=t))
            donors=tr["donor_rows"]
            if tr["source"]!=SOURCES[j] or tr["source_index"]!=j+1 or tr["truth_id"]!=t:
                return False
            if tr["destination_rows"]!=idx.tolist() or sorted(donors)!=idx.tolist():
                return False
            rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed,j+1,t])))
            expected=rng.permutation(rp[idx,j].copy())
            if not np.array_equal(expected,cp[idx,j]) or not np.array_equal(rp[np.array(donors,dtype=np.int64),j],cp[idx,j]):
                return False
    return True

def fixtures():
    # Six invented rows, three classes; no frozen project asset is loaded.
    rp=np.array([[0,0,0],[1,2,1],[2,1,2],[1,1,1],[0,2,0],[2,0,2]],dtype=np.int64)
    real={"example_ids":np.array([f"fixture:{i}" for i in range(6)]),"truth_ids":np.array([0,0,0,1,1,1],dtype=np.int64),
          "source_predictions":rp,"targets":targets(rp,3),"source_weights":np.array([1/3]*3,dtype=np.float64)}
    identity={**{k:v.copy() for k,v in real.items()},"control_seed":np.array([SEED],dtype=np.int64)}
    results={"valid_identity_zero_contrast":all(checks(real,identity,SOURCES,3).values())}
    bad=copy.deepcopy(identity); bad["source_predictions"][0,0]=1; bad["targets"]=targets(bad["source_predictions"],3)
    results["correct_label_tamper_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    bad=copy.deepcopy(identity); bad["source_predictions"][1,0]=2; bad["targets"]=targets(bad["source_predictions"],3)
    results["foreign_multiset_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    for name,edit in (("duplicate_id",lambda a:a.__setitem__(1,a[0])),("swapped_ids",lambda a:a.__setitem__(slice(0,2),a[:2][::-1]))):
        bad=copy.deepcopy(identity); edit(bad["example_ids"])
        results[name+"_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    bad={k:v[:-1].copy() if k in ("example_ids","truth_ids","source_predictions","targets") else v.copy() for k,v in identity.items()}
    results["missing_id_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    results["source_order_rejected"]=not all(checks(real,identity,SOURCES[::-1],3).values())
    bad=copy.deepcopy(identity); bad["targets"]=np.float32(.9)*bad["targets"]+np.float32(.1/3)
    results["smoothed_target_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    bad=copy.deepcopy(identity); bad["targets"][1]=bad["targets"][0]
    results["misaggregation_rejected"]=not all(checks(real,bad,SOURCES,3).values())
    inc=copy.deepcopy(identity); inc["source_predictions"][[1,2],1]=inc["source_predictions"][[2,1],1]; inc["targets"]=targets(inc["source_predictions"],3)
    old_same=int(((rp[:,0]==rp[:,1])&(rp[:,0]!=real["truth_ids"])&(rp[:,1]!=real["truth_ids"])).sum())
    new_same=int(((inc["source_predictions"][:,0]==inc["source_predictions"][:,1])&(rp[:,0]!=real["truth_ids"])&(rp[:,1]!=real["truth_ids"])).sum())
    results["increased_alignment_valid"]=new_same>old_same and all(checks(real,inc,SOURCES,3).values())
    cand,tr=construct(real,SEED,3)
    results["fixture_replay_pass"]=replay_check(real,cand,tr,SEED,3)
    bad=copy.deepcopy(cand); bad["control_seed"][0]-=1
    results["wrong_seed_rejected"]=not replay_check(real,bad,tr,SEED,3)
    badtr=copy.deepcopy(tr); badtr[0]["source_index"]=2
    results["wrong_transcript_rejected"]=not replay_check(real,cand,badtr,SEED,3)
    try:
        with np.load(io.BytesIO(b"not-a-valid-npz"),allow_pickle=False) as a:
            list(a.files)
        results["corrupt_archive_rejected"]=False
    except Exception:
        results["corrupt_archive_rejected"]=True
    b=io.BytesIO(); np.savez_compressed(b,**cand); b.seek(0)
    with np.load(b,allow_pickle=False) as a:
        results["fixture_serialization_roundtrip"]=all(np.array_equal(a[k],cand[k]) for k in cand)
    return {"status":"PASS" if all(results.values()) else "FAIL","checks":results,
            "project_candidates_generated":0,"fixture_rows":6,"fixture_only":True,"numpy":np.__version__}

def safe_input(rel):
    p=(ROOT/rel).resolve()
    if not p.is_relative_to(ROOT):
        raise ValueError("Input path escape")
    return p

def authority_check():
    status=read_json(FREEZE/"STAGE_STATUS.json")
    assert status["PROTOCOL_FREEZE"]=="PASS" and status["SECOND_REALIZATION_SEED"]==str(SEED)
    assert status["REALIZATION_2_GENERATED"]=="NO" and status["INVARIANTS_READY"]=="PASS"
    for name,key in (("STAGE_MANIFEST.json","artifacts"),("PROTOCOL_FREEZE_RECORD.json","files")):
        for item in read_json(FREEZE/name)[key]:
            p=(FREEZE/item["path"]).resolve()
            assert p.is_relative_to(FREEZE) and sha(p)==item["sha256"],str(p)
    assets=read_json(FREEZE/"INPUT_ASSET_IDENTITY.json")["files"]
    assert all(sha(safe_input(a["path"]))==a["sha256"] for a in assets)
    rule=read_json(FREEZE/"FROZEN_SEED_RULE.json")
    payload="".join(k+"="+v+"\n" for k,v in rule["fields_in_exact_order"]).encode("utf-8")
    digest=hashlib.sha256(payload).digest()
    assert len(payload)==248 and digest.hex()=="dee3b50048142fcbb7f4975a7cefb9153690d007b0da0da80a0d9f9a30ea6820"
    assert int.from_bytes(digest[:8],"big")%(2**63)==SEED
    assert np.__version__==rule["numpy_version"]=="2.3.5"
    return assets

def stats(x):
    if len(x)==0:
        return {"n":0,"mean":None,"mean_fp64_reduction":None,"min":None,"p25":None,"median":None,"p75":None,"p90":None,"p95":None,"max":None}
    q=np.quantile(x,[0,.25,.5,.75,.9,.95,1],method="linear")
    return {"n":len(x),"mean":float(x.mean()),"mean_fp64_reduction":float(x.astype(np.float64).mean()),
            **{k:float(v) for k,v in zip(["min","p25","median","p75","p90","p95","max"],q)}}

def diagnostics(real,old,new):
    y,rp=real["truth_ids"],real["source_predictions"]
    changed=[]
    conditions={}
    for name,ar in (("R1",old),("R2",new)):
        mask=np.any(real["targets"]!=ar["targets"],axis=1)
        changed.append(mask)
        l1=np.abs(real["targets"]-ar["targets"]).sum(axis=1)
        edits=rp!=ar["source_predictions"]
        conditions[name]={"changed_count":int(mask.sum()),"changed_fraction":float(mask.mean()),
            "all_3000_L1":stats(l1),"changed_only_L1":stats(l1[mask]),
            "source_edits":dict(zip(SOURCES,map(int,edits.sum(0)))),
            "source_edit_multiplicity":{str(i):int((edits.sum(1)==i).sum()) for i in range(4)}}
    overlap=int((changed[0]&changed[1]).sum()); union=int((changed[0]|changed[1]).sum())
    pairs={}
    for a,b,name in ((0,1,"bert_roberta"),(0,2,"bert_deberta"),(1,2,"roberta_deberta")):
        pairs[name]={}
        for label,ar in (("REAL",real),("R1",old),("R2",new)):
            pred=ar["source_predictions"]; both=(pred[:,a]!=y)&(pred[:,b]!=y)
            n=int(both.sum()); same=int(((pred[:,a]==pred[:,b])&both).sum())
            pairs[name][label]={"both_wrong":n,"same_wrong":same,"same_wrong_fraction":same/n if n else None}
    per_intent=[{"truth_id":t,"pool_count":int((y==t).sum()),"R1_changed":int((changed[0]&(y==t)).sum()),
                 "R2_changed":int((changed[1]&(y==t)).sum()),"overlap":int((changed[0]&changed[1]&(y==t)).sum())} for t in range(150)]
    return {"metric":"PRE_SMOOTHING_RAW_AGGREGATE_TARGET","descriptive_only":True,"used_for_validity":False,
        "precision":"float32 subtraction/class-sum/primary mean; linear quantiles; labeled FP64 reduction supplementary",
        "conditions":conditions,"pairwise":pairs,"changed_support_overlap":{"intersection":overlap,"union":union,
        "jaccard":overlap/union if union else None,"unique_R1":int((changed[0]&~changed[1]).sum()),"unique_R2":int((~changed[0]&changed[1]).sum())},
        "per_intent":per_intent}

def generate():
    # All checks below precede first formal PRNG call.
    assets=authority_check()
    pre=read_json(HERE/"INPUT_PREFLIGHT_VALIDATION.json")
    assert pre["status"]=="PASS" and all(pre["checks"].values())
    eng=read_json(HERE/"ENGINEERING_TEST_REPORT.json")
    assert eng["status"]=="PASS" and all(eng["checks"].values())
    lock=read_json(HERE/"IMPLEMENTATION_FREEZE.json")
    assert lock["code_sha256"]==sha(Path(__file__)) and lock["tests_sha256"]==sha(HERE/"ENGINEERING_TEST_REPORT.json")
    assert lock["authority_manifest_sha256"]==sha(FREEZE/"STAGE_MANIFEST.json")
    assert lock["preflight_sha256"]==sha(HERE/"INPUT_PREFLIGHT_VALIDATION.json")
    # Refuse prior attempts across sibling stage directories, not only this directory.
    for directory in HERE.parent.glob("independent_manipulation_realization_generation_and_validation_v1_*"):
        assert not (directory/"ATTEMPT_STARTED.json").exists(),"Prior attempt exists; STOP"
        assert not any(directory.glob("*.npz")),"Candidate/partial archive exists; STOP"
        assert not any(directory.glob("*.partial")),"Partial artifact exists; STOP"
        assert not (directory/"PERMUTATION_TRANSCRIPT.json").exists(),"Prior transcript exists; STOP"
    real=load_npz(ORIG/"supervision/CONDITION_REAL_SUPERVISION.npz")
    assert list(real["example_ids"])==[f"clinc150:dev:{i:06d}" for i in range(3000)]
    assert Counter(real["truth_ids"].tolist())==Counter({i:20 for i in range(150)})
    # Write-once token is durable before the formal draw.
    token={"utc":now(),"seed":str(SEED),"candidate_budget":1,"attempt":1,
           "authority_manifest_sha256":sha(FREEZE/"STAGE_MANIFEST.json"),
           "implementation_freeze_sha256":sha(HERE/"IMPLEMENTATION_FREEZE.json"),"code_sha256":sha(Path(__file__))}
    write_new("ATTEMPT_STARTED.json",token)
    try:
        candidate,transcript=construct(real,SEED,150)
        with (HERE/"SECOND_REALIZATION_SUPERVISION.npz").open("xb") as f:
            np.savez_compressed(f,**candidate)
        write_new("PERMUTATION_TRANSCRIPT.json",{"seed":str(SEED),"groups":transcript,"construction_calls":450})
        # Read back persisted bytes; never replace/regenerate the candidate.
        del candidate
        loaded=load_npz(HERE/"SECOND_REALIZATION_SUPERVISION.npz")
        tr=read_json(HERE/"PERMUTATION_TRANSCRIPT.json")
        valid=checks(real,loaded,SOURCES,150)
        valid["seed_exact"]=loaded["control_seed"].tolist()==[SEED]
        valid["deterministic_transcript_replay"]=replay_check(real,loaded,tr["groups"],SEED,150)
        valid["source_hashes_unchanged"]=all(sha(safe_input(a["path"]))==a["sha256"] for a in assets)
        inv=read_json(FREEZE/"03_FROZEN_INVARIANTS.json")
        valid["frozen129_hash_unchanged"]=sha(safe_input(inv["frozen129"]["path"]))==inv["frozen129"]["sha256"]
        valid["frozen129_membership_preflight"]=pre["checks"]["frozen129_membership"] and valid["frozen129_hash_unchanged"]
        report={"status":"PASS" if all(valid.values()) else "FAIL","checks":valid,"candidate_count":1,
                "generation_permutation_calls":450,"validation_replay_calls":450,
                "replay_is_same_candidate_identity_check":True,"diagnostics_used":False,"utc":now()}
        write_new("INVARIANT_VALIDATION.json",report)
        if not all(valid.values()):
            raise RuntimeError("Hard invariant validation failed; STOP, no regeneration")
        old=load_npz(ORIG/"supervision/CONDITION_DIRECTION_SCRAMBLED_SUPERVISION.npz")
        diag=diagnostics(real,old,loaded)
        write_new("05_MANIPULATION_DIAGNOSTICS.json",diag)
        prov={"stage":HERE.name,"seed":str(SEED),"authority":FREEZE.relative_to(ROOT).as_posix(),
              "authority_manifest_sha256":sha(FREEZE/"STAGE_MANIFEST.json"),"implementation_sha256":sha(Path(__file__)),
              "candidate_sha256":sha(HERE/"SECOND_REALIZATION_SUPERVISION.npz"),"candidate_file":"SECOND_REALIZATION_SUPERVISION.npz",
              "transcript_sha256":sha(HERE/"PERMUTATION_TRANSCRIPT.json"),"source_order":SOURCES,
              "source_identities":read_json(ORIG/"PROVENANCE.json")["sources"],
              "dataset_sha256":inv["dataset_sha256"],"label_mapping_sha256":inv["label_mapping_raw_sha256"],
              "raw_text_access":"Not read or changed; historical hash binding retained; future Student binding must reverify raw text.",
              "input_identity_index":(FREEZE/"INPUT_ASSET_IDENTITY.json").relative_to(ROOT).as_posix(),
              "real_archive_sha256":sha(ORIG/"supervision/CONDITION_REAL_SUPERVISION.npz"),
              "original_scrambled_archive_sha256":sha(ORIG/"supervision/CONDITION_DIRECTION_SCRAMBLED_SUPERVISION.npz"),
              "numpy":np.__version__,"python":sys.version.split()[0],"PRNG":"PCG64(SeedSequence([seed, source_index_1based, truth_id]))",
              "candidate_generation_count":1,"regeneration_count":0,"selection_based_on_diagnostics":False,
              "student_training":0,"student_inference":0,"source_training":0,"source_inference":0,"new_training_seeds":0,
              "inferential_statistics":0,"autodl":0,"ssh":0,"gpu":0,"git_writes":0,"recursive":0,"utc":now(),"return_code":0}
        write_new("02_SECOND_REALIZATION_PROVENANCE.json",prov)
        write_new("EXECUTION_RESULT.json",{"status":"PASS","return_code":0,"generated":True,"valid":"PASS","candidate_count":1,"utc":now()})
        print(json.dumps({"status":"PASS","return_code":0,"R2":diag["conditions"]["R2"],"overlap":diag["changed_support_overlap"],"pairwise":diag["pairwise"]},indent=2))
        return 0
    except Exception as exc:
        write_new("EXECUTION_FAILURE.json",{"status":"FAIL","return_code":1,"error":str(exc),"utc":now(),
                  "attempt_consumed":True,"automatic_retry":False,"next_stage":"INDEPENDENT_MANIPULATION_REALIZATION_FAILURE_REVIEW_V1"})
        raise

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["fixtures","generate"])
    args=parser.parse_args()
    if args.mode=="fixtures":
        result=fixtures()
        print(json.dumps(result,indent=2))
        raise SystemExit(0 if result["status"]=="PASS" else 1)
    raise SystemExit(generate())
