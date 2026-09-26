"""Formal consequence worker. There is deliberately no executable training CLI."""
from pathlib import Path
import hashlib, importlib.util, json, math, os, random
import numpy as np

from consequence_runtime import (CONDITIONS, SEEDS, load_bindings, package_contract,
    read_json, sha, validate_package_manifest, validate_seed_assets)
from trajectory_logger import epoch_summary, ordered_id_digest, rng_snapshot, validate_step_row
from environment_gate import validate as validate_environment

def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as f: json.dump(value, f, indent=2, ensure_ascii=False)

def _support_core(support):
    spec=importlib.util.spec_from_file_location("frozen_v5_readiness_core_worker",support/"readiness_core.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def execute(package_root, project_root, seed, order_id, condition, output, authorization):
    import torch
    from tokenizers import Tokenizer
    package_root=Path(package_root);project_root=Path(project_root);output=Path(output);authorization=Path(authorization)
    validate_package_manifest(package_root);contract=package_contract(package_root)
    package_meta=read_json(package_root.parent/"EXECUTION_PACKAGE_MANIFEST.json")
    for field, name in (("package_manifest_sha256","package/PACKAGE_MANIFEST.json"),
                        ("allowlist_sha256","SIXTEEN_FIT_ALLOWLIST.json"),
                        ("order_matrix_sha256","ORDER_IDENTITY_MATRIX.json"),
                        ("environment_contract_sha256","ENVIRONMENT_CONTRACT.json"),
                        ("rng_contract_sha256","RNG_CONTRACT.json"),
                        ("trajectory_logger_spec_sha256","TRAJECTORY_LOGGER_SPEC.json")):
        if package_meta[field]!=sha(package_root.parent/name):raise ValueError("Execution package binding: "+name)
    auth=read_json(authorization)
    if auth.get("stage")!="MLBD2026_OPTIMIZATION_PATH_INTERACTION_EXECUTION_V1" or auth.get("human_authorized") is not True:
        raise ValueError("Separate formal execution authority required")
    if auth.get("package_manifest_sha256")!=sha(package_root/"PACKAGE_MANIFEST.json") or auth.get("fit_matrix")!=contract["fit_matrix"]:
        raise ValueError("Authorization/package matrix")
    if auth.get("execution_package_manifest_sha256")!=sha(package_root.parent/"EXECUTION_PACKAGE_MANIFEST.json"):
        raise ValueError("Execution package authorization binding")
    if seed not in SEEDS or condition not in CONDITIONS or order_id not in ("PI0","PI1"):
        raise ValueError("Unfrozen job")
    expected=project_root/contract["execution_namespace_relative_path"]/f"SEED_{seed}"/order_id/condition
    if output.resolve()!=expected.resolve():raise ValueError("Path experiment output namespace")
    if auth.get("preflight_status_sha256")!=sha(package_root.parent/"PREFLIGHT_STATUS.json") or read_json(package_root.parent/"PREFLIGHT_STATUS.json").get("status")!="PASS":
        raise ValueError("Preflight authority")
    receipt_path=(project_root / auth.get("installed_runtime_receipt_path", "__MISSING__")).resolve()
    if not receipt_path.is_relative_to(project_root.resolve()) or not receipt_path.is_file() or sha(receipt_path)!=auth.get("installed_runtime_receipt_sha256"):
        raise ValueError("Installed runtime receipt required")
    validate_environment(read_json(receipt_path),read_json(package_root.parent/"ENVIRONMENT_CONTRACT.json"))
    if os.environ.get("PYTHONHASHSEED")!=str(seed) or os.environ.get("CUBLAS_WORKSPACE_CONFIG")!=":4096:8":raise ValueError("Process determinism")
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True,exist_ok=False)
    for name in ("checkpoint","predictions","metrics","logs","status","manifest","provenance","validator"):(output/name).mkdir()
    steps=0;write_new(output/"status/STARTED.json",dict(status="STARTED",seed=seed,order_id=order_id,condition=condition,steps=0))
    try:
        bindings=load_bindings(package_root,project_root);support,seeds=validate_seed_assets(package_root,project_root,order_id);core=_support_core(support)
        protocol=read_json(support/"package/FROZEN_SECOND_STUDENT_ADEQUACY_PROTOCOL.json");recipe=protocol["R0"]
        torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.use_deterministic_algorithms(True,warn_only=False)
        torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False;torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False;torch.set_float32_matmul_precision("highest")
        model,load=core.build(support/"model_assets",protocol,seed)
        frozen=seeds[str(seed)]
        if core.digest(model.state_dict())[0]!=frozen["initial"]["full_digest"]:raise ValueError("Initial state")
        train=bindings["conditions"][condition];ids=train["example_ids"];lookup={x:i for i,x in enumerate(ids)}
        tok=Tokenizer.from_file(str(support/"model_assets/tokenizer.json"));tok.enable_truncation(128,direction="right");tok.enable_padding(direction="left",pad_id=5,pad_type_id=3,pad_token="<pad>",length=128)
        def encode(texts):
            e=tok.encode_batch(texts)
            return dict(input_ids=torch.tensor([x.ids for x in e]),attention_mask=torch.tensor([x.attention_mask for x in e]),token_type_ids=torch.tensor([x.type_ids for x in e]))
        inputs=encode([x[0] for x in bindings["dataset"]["val"]]);targets=torch.tensor(train["targets"],dtype=torch.float32)
        model.to("cuda");groups,_=core.optimizer_groups(model,recipe);o=recipe["optimizer"]
        optimizer=torch.optim.AdamW(groups,lr=o["lr"],betas=tuple(o["betas"]),eps=o["eps"],amsgrad=o["amsgrad"],foreach=o["foreach"],fused=o["fused"],capturable=o["capturable"],differentiable=o["differentiable"],maximize=o["maximize"])
        random.seed(seed);np.random.seed(seed);torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
        rng=rng_snapshot(torch)
        if optimizer.state:raise ValueError("Optimizer state must start empty")
        role=next(x for x in contract["assets"] if x["role"]==condition)
        order_identity=next(x for x in read_json(package_root.parent/"ORDER_IDENTITY_MATRIX.json")["seeds"] if x["seed"]==seed)[order_id]
        write_new(output/"provenance/INITIAL.json",dict(seed=seed,order_id=order_id,condition=condition,recipe="R0",initial_state=frozen["initial"],order=order_identity,rng=rng,supervision_sha256=role["sha256"],package_manifest_sha256=sha(package_root/"PACKAGE_MANIFEST.json"),load=load,no_historical_fit_reuse=True,optimizer_state_initially_empty=True))
        with (output/"logs/TRAIN.jsonl").open("x",encoding="utf-8") as log, (output/"logs/EPOCH.jsonl").open("x",encoding="utf-8") as epoch_log:
            for epoch in frozen["schedule"]:
                model.train();indices=[lookup[x] for x in epoch["example_ids"]]
                for start in range(0,3000,32):
                    idx=indices[start:start+32];optimizer.zero_grad(set_to_none=True)
                    batch={k:v[idx].to("cuda") for k,v in inputs.items()}
                    before=rng_snapshot(torch)
                    logits=core.forward_logits(model,batch)
                    after=rng_snapshot(torch)
                    loss=core.external_loss(logits,targets[idx].to("cuda"))
                    if not torch.isfinite(loss):raise ValueError("Nonfinite loss")
                    loss.backward();norm=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,norm_type=2,error_if_nonfinite=True,foreach=False)
                    lr=core.lr_at(recipe,steps)
                    for group in optimizer.param_groups:group["lr"]=lr
                    optimizer.step();steps+=1
                    row=dict(epoch=epoch["epoch"],batch_index=start//32,global_step=steps,
                             batch_size=len(idx),ordered_ID_sha256=ordered_id_digest(epoch["example_ids"][start:start+32]),
                             lr_by_group=[float(g["lr"]) for g in optimizer.param_groups],loss=float(loss.detach()),
                             preclip_grad_norm=float(norm),rng_before_forward=before,rng_after_forward=after)
                    validate_step_row(row);log.write(json.dumps(row,sort_keys=True)+"\n");log.flush()
                summary=epoch_summary(model,optimizer,torch)
                summary["epoch"]=epoch["epoch"]
                if summary["optimizer_step_min_max"] != [steps, steps]:
                    raise ValueError("Adam step summary")
                epoch_log.write(json.dumps(summary,sort_keys=True)+"\n");epoch_log.flush()
        if steps!=1880:raise ValueError("Incomplete steps")
        for t in model.state_dict().values():
            if not torch.isfinite(t).all():raise ValueError("Nonfinite final state")
        from safetensors.torch import save_file
        save_file({k:v.detach().cpu().contiguous() for k,v in model.state_dict().items()},str(output/"checkpoint/model.safetensors"))
        test_inputs=encode([x[0] for x in bindings["dataset"]["test"]]);parts=[];model.eval()
        with torch.no_grad():
            for start in range(0,4500,32):parts.append(core.forward_logits(model,{k:v[start:start+32].to("cuda") for k,v in test_inputs.items()}).float().cpu())
        logits=torch.cat(parts).numpy();truth=bindings["test_truth"]
        np.savez_compressed(output/"predictions/TEST.npz",logits=logits,truth_ids=truth,example_ids=np.asarray(bindings["test_ids"]))
        metrics=core.evaluate(logits,truth)
        ref=float(-torch.log_softmax(torch.tensor(logits).double(),-1)[torch.arange(4500),torch.tensor(truth)].mean())
        if abs(ref-metrics["mean_unsmoothed_nll"])>1e-12:raise ValueError("Independent metric recomputation")
        write_new(output/"metrics/METRICS.json",dict(test_true_label_logloss=metrics["mean_unsmoothed_nll"],test_correct_count=metrics["correct_count"],accuracy=metrics["correct_count"]/4500,independent_recomputation=True))
        write_new(output/"status/COMPLETE.json",dict(status="COMPLETE",seed=seed,order_id=order_id,condition=condition,steps=1880,epochs=20))
        write_new(output/"manifest/MANIFEST.json",dict(files=[dict(path=x.relative_to(output).as_posix(),sha256=sha(x)) for x in sorted(output.rglob("*")) if x.is_file()]))
    except BaseException as exc:
        write_new(output/"status/FAILED.json",dict(status="FAIL_CLOSED",seed=seed,order_id=order_id,condition=condition,optimizer_steps=steps,error=type(exc).__name__+": "+str(exc),automatic_retry=False))
        raise

if __name__=="__main__":raise SystemExit("No execution CLI. Use separately authorized serial controller.")
