"""Local publication-spec freeze from sealed reports. No model or raw predictions."""
from pathlib import Path
import csv
import hashlib
import io
import json
import statistics as st
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / 'reports/research/submission_mlbd2026'
SYN = BASE / 'mlbd2026_final_mechanism_synthesis_and_claim_boundary_v1_20260923T151937Z'
STAGE = 'MLBD2026_MANUSCRIPT_CLAIM_FIGURE_TABLE_FREEZE_V1'
sources = {}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def bind(eid, p, expected=None):
    p = Path(p)
    h = digest(p)
    if expected:
        assert h == expected, (eid, 'authority hash mismatch')
    sources[eid] = dict(evidence_id=eid, path=p.relative_to(ROOT).as_posix(),
        sha256=h, bytes=p.stat().st_size, verification='ASSISTANT_LOCAL_SOURCE_CHECKED',
        human_verification='NOT_RECORDED_THIS_STAGE')
    return p

def src(eid):
    return ROOT / sources[eid]['path']

def readcsv(eid):
    return list(csv.DictReader(src(eid).read_text(encoding='utf-8-sig').splitlines()))

def write(name, text):
    with (HERE/name).open('x', encoding='utf-8', newline='') as f:
        f.write(text.strip()+'\n')

def js(name, obj):
    write(name, json.dumps(obj, ensure_ascii=False, indent=2))

def outcsv(name, rows):
    assert rows
    with (HERE/name).open('x', encoding='utf-8', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

def mdtable(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(x) for x in r)+' |' for r in rows])

def signs(vals):
    return ''.join('+' if x>0 else '-' if x<0 else '0' for x in vals)

def fmt(x):
    return f'{float(x):+.6f}'

idx=json.loads((SYN/'AUTHORITY_INDEX.json').read_text(encoding='utf-8'))
needed=['GOVERNANCE','METHOD_SCOPE','MAIN_H','MAIN_MATRIX','MAIN_CHRONOLOGY','CROB_FINAL',
        'CROB_VALUES','CXL_FINAL','CXL_VALUES','BANK_CONTROL_FINAL','BANK_CONTROL_VALUES',
        'CONTROL_INVARIANTS','OUTPUT_DECOMP','STATIC_DIAGNOSTIC','PROXY_FINAL','M3_PROTOCOL',
        'M3_STATUS','M3_TABLE','M3_RECOMPUTE','M3_MATRIX','M3_FINAL']
for a in idx['inputs']:
    if a['authority_id'] in needed:
        bind(a['authority_id'], ROOT/a['path'], a['sha256'])
for name in ['FINAL_MECHANISM_SYNTHESIS_ZH.md','MECHANISM_EVIDENCE_LEVELS.md',
             'EXTREME_SEED_ADJUDICATION.md','CLAIM_BOUNDARY_MATRIX.csv',
             'MECHANISM_EXPERIMENT_COMPLETENESS.md','MECHANISM_FIGURE_STORYBOARD.md',
             'DESCRIPTIVE_SENSITIVITY_SUMMARY.csv','AUTHORITY_INDEX.json']:
    bind('SYN_'+name.split('.')[0], SYN/name)

main_dir=src('MAIN_MATRIX').parent
decomp_dir=src('OUTPUT_DECOMP').parent
clinc_dir=ROOT/'reports/research/student_consequence/real_clinc150_minimal_student_consequence_manipulation_preflight_v1_resume_execution_20260907T085125Z'
bank_dir=BASE/'mlbd2026_banking77_local_subset_and_target_construction_freeze_v2_20260921T044209Z'
extra={
 'MAIN_SEEDS':main_dir/'02_ALL_SEED_PAIRED_DELTAS.csv',
 'DECOMP_VALUES':decomp_dir/'01_FOUR_SETTING_OUTPUT_DECOMPOSITION.csv',
 'DECOMP_MEANS':decomp_dir/'02_PROBABILITY_MASS_FLOW_SUMMARY.md',
 'INPUT_BINDINGS':decomp_dir/'DIAGNOSTIC_INPUT_BINDINGS.json',
 'CLINC_PRESERVATION':clinc_dir/'PRESERVATION_VALIDATION.json',
 'CLINC_CONTRACT':ROOT/'reports/research/student_consequence/roberta_mechanism_multi_seed_confirmatory_protocol_design_and_freeze_v1_20260911T092505Z/FROZEN_ROBERTA_MULTI_SEED_CONFIRMATORY_PROTOCOL.json',
 'ENDPOINT_CONTRACT':src('CONTROL_INVARIANTS').parent/'06_ENDPOINT_CONTRACT.json',
 'BANK_PACKAGE':bank_dir/'09_FROZEN_STUDENT_INPUT_PACKAGE.json',
 'BANK_MANIPULATION':bank_dir/'RESULT_REPORT.md',
 'BANK_R1_GATE':bank_dir/'04_R1_VALIDATION_AND_DIAGNOSTICS.json',
 'BANK_R2_GATE':bank_dir/'05_R2_VALIDATION_AND_DIAGNOSTICS.json',
 'BANK_LOCAL':BASE/'mlbd2026_banking77_local_subset_and_target_construction_freeze_v1_20260921T041141Z/04_LOCAL_SUBSET_AND_GATE.json',
}
for eid,p in extra.items(): bind(eid,p)
# Open only small report/summary assets, never prediction arrays or weights.
texts={eid:src(eid).read_text(encoding='utf-8-sig') for eid in sources}
contract=json.loads(texts['CLINC_CONTRACT'])
seeds=[int(s) for s in contract['FINAL_CONFIRMATORY_SEEDS']]
assert len(seeds)==4
bank=json.loads(texts['BANK_PACKAGE'])
assert seeds==bank['student']['seeds']
assert json.loads(texts['CLINC_PRESERVATION'])['validator']=='PASS'
for eid in ['BANK_R1_GATE','BANK_R2_GATE']:
    assert all(json.loads(texts[eid])['invariants'].values())
assert bank['evaluation']['local_subset_rows']==304
assert contract['outcomes']['secondary']['subset_size']==129

matrix=readcsv('MAIN_MATRIX'); seedrows=readcsv('MAIN_SEEDS')
settings=[('CLINC150','RoBERTa'),('CLINC150','XLNet'),('BANKING77','RoBERTa'),('BANKING77','XLNet')]
endpoints=['Secondary','LocalNLL','Primary','Complement']
lookup={(r['dataset'],r['learner'],r['endpoint']):r for r in matrix}
checks=[]
def check(name, ok, detail):
    assert ok, (name, detail)
    checks.append(dict(gate=name,status='PASS',detail=detail))

table1=[]
for dataset,learner in settings:
    for comp in ['R1','R2']:
        row=dict(dataset=dataset,learner=learner,comparator=comp,n_training_seeds=4)
        rs=[next(r for r in seedrows if r['dataset']==dataset and r['learner']==learner and r['comparator']==comp and int(r['seed'])==s) for s in seeds]
        for ep in endpoints:
            vals=[float(r[ep]) for r in rs]; a=lookup[dataset,learner,ep]
            check(f'MAIN_{dataset}_{learner}_{comp}_{ep}',
                  abs(st.mean(vals)-float(a[comp+'_mean']))<1e-12 and signs(vals)==a[comp+'_signs'],
                  'seed rows reconcile to frozen 2x2 matrix; no inferential statistic')
            row[ep+'_mean']=float(a[comp+'_mean']); row[ep+'_signs']=a[comp+'_signs']
        row['evidence_ids']='MAIN_MATRIX;MAIN_SEEDS'
        table1.append(row)
outcsv('TABLE_1_DATA.csv',table1)

control=[]
for dataset,learner in settings:
    eid='CROB_VALUES' if (dataset,learner)==settings[0] else 'CXL_VALUES' if dataset=='CLINC150' else 'BANK_CONTROL_VALUES'
    rows=readcsv(eid)
    r=dict(dataset=dataset,learner=learner,n_training_seeds=4)
    for ep in ['Secondary','LocalNLL']:
        if eid=='CXL_VALUES':
            vals=[float(next(x for x in rows if int(x['seed'])==s and x['endpoint']==ep)['delta_REAL_minus_CONTROL']) for s in seeds]
        else:
            vals=[float(next(x for x in rows if int(x['seed'])==s and (eid=='CROB_VALUES' or x['learner']==learner))[ep]) for s in seeds]
        r[ep+'_mean']=st.mean(vals);r[ep+'_signs']=signs(vals)
    r['directional_status']='NON_UNANIMOUS' if (dataset,learner)==settings[1] else 'BOTH_ENDPOINTS_FOUR_POSITIVE'
    r['evidence_id']=eid;control.append(r)
check('CONTROL_COVERAGE',len(control)==4 and control[1]['Secondary_signs']=='++--' and control[1]['LocalNLL_signs']=='-+--','four measured settings, not four positive conclusions')
outcsv('CONTROL_TABLE_DATA.csv',control)

m3=readcsv('M3_TABLE');summary=[]
assert len(m3)==8
for r in m3:
    for order in ['PI0','PI1']:
        check(f'M3_{r["seed"]}_{r["endpoint"]}_{order}',abs(float(r['Y_REAL_'+order])-float(r['Y_CONTROL_'+order])-float(r['D_'+order]))<1e-12,'absolute Y to paired D')
    check('I_'+r['seed']+'_'+r['endpoint'],abs(float(r['D_PI1'])-float(r['D_PI0'])-float(r['I']))<1e-12,'D_PI1 minus D_PI0')
outcsv('M3_RESULT_TABLE_DATA.csv',[dict(r,unit='nats' if r['endpoint']=='LocalNLL' else 'probability',evidence_id='M3_TABLE') for r in m3])
for ep in ['Secondary','LocalNLL']:
    rs=[next(r for r in m3 if r['endpoint']==ep and int(r['seed'])==s) for s in seeds]
    for stat in ['mean','median','sign_pattern']:
        row=dict(endpoint=ep,statistic=stat,analysis_role='POST_HOC_DESCRIPTIVE' if stat=='median' else 'FROZEN_FOUR_SEED_SUMMARY')
        for col in ['D_PI0','D_PI1','I']:
            vals=[float(r[col]) for r in rs]
            row[col]=signs(vals) if stat=='sign_pattern' else st.mean(vals) if stat=='mean' else st.median(vals)
        row['evidence_id']='M3_TABLE';summary.append(row)
outcsv('M3_SUMMARY_DATA.csv',summary)

decomp=readcsv('DECOMP_VALUES');plot=[]
assert len(decomp)==32
for dataset,learner in settings:
    for comp in ['R1','R2']:
        rs=[r for r in decomp if (r['dataset'],r['learner'],r['realization'])==(dataset,learner,comp)]
        assert len(rs)==4
        vals={x:st.mean(float(r[x]) for r in rs) for x in ['dp_true_mean','dp_shared_mean','dp_other_mean','dNLL_mean']}
        check('MASS_'+dataset+learner+comp,abs(sum(vals[x] for x in ['dp_true_mean','dp_shared_mean','dp_other_mean']))<1e-12,'mean true/shared/other accounting')
        check('MASS_ENDPOINT_'+dataset+learner+comp,abs(vals['dp_shared_mean']-float(lookup[dataset,learner,'Secondary'][comp+'_mean']))<1e-12 and abs(vals['dNLL_mean']-float(lookup[dataset,learner,'LocalNLL'][comp+'_mean']))<1e-12,'decomposition values match main endpoints')
        plot.append(dict(dataset=dataset,learner=learner,comparator=comp,**vals,evidence_id='DECOMP_VALUES',aggregation='unweighted mean of four existing seed means'))
outcsv('FIGURE_B_OUTPUT_DATA.csv',plot)

# Claim registry: manuscript labels are not new scientific hypotheses.
claims=[]
def claim(cid,old,cat,text,eids,locator,scope,verbs,banned,counter,section,display):
    claims.append(dict(claim_id=cid,prior_claim_id=old,classification=cat,paper_wording=text,
        evidence_source=eids,evidence_locator=locator,scope=scope,allowed_verbs=verbs,
        prohibited_verbs=banned,counterexample=counter,target_section=section,display=display,
        wording_sha256=hashlib.sha256(text.encode()).hexdigest(),human_approval='NOT_RECORDED_THIS_STAGE'))
claim('MC01','C01','CORE',
 'Changing wrong-label assignments to inputs can alter downstream Student behavior while preserving Source correctness identities, true-label target mass, and Source-by-truth wrong-label marginals.',
 'MAIN_H;MAIN_MATRIX;CLINC_PRESERVATION;BANK_MANIPULATION','H1; all four settings; preservation checks',
 'Tested single-generation classification settings; measured matching constraints only','can alter; demonstrates within the controlled comparisons',
 'always hurts; proves the mechanism; controls every dimension of Source quality','CLINC150 XLNet LocalNLL is not uniformly positive','1;3;5;8','Figure A;Table 1')
claim('MC02','C02','CORE',
 'REAL increased probability on the frozen shared-wrong label in all four seeds for R1 in each setting, whereas CLINC150 R2 showed mixed seed directions.',
 'MAIN_MATRIX;MAIN_SEEDS','Secondary rows; R1/R2 signs','n=4 paired training seeds per comparator; fixed local129/local304',
 'increased in the observed seeds; showed','always transfers; establishes realization invariance','CLINC R2 RoBERTa -+++ and XLNet ++-+','1;5;8','Table 1')
claim('MC03','C02;C07','CORE',
 'Local true-label NLL degradation was conditional on the learner and dataset/Source setting, and did not necessarily accompany increased shared-wrong probability.',
 'MAIN_MATRIX;OUTPUT_DECOMP;DECOMP_VALUES','LocalNLL and Secondary; CLINC XLNet R1/R2',
 'Original REAL-R1/R2; local endpoints in two dataset/Source settings','was conditional; dissociated; differed',
 'universal local degradation; every local sample worsens','CLINC XLNet LocalNLL -+-- for both R1 and R2','1;5;6.1;8','Table 1;Figure B.A')
claim('MC04','C03','NEGATIVE_RESULT',
 'Robust global degradation was not supported across settings: full-test NLL contrasts were positive across BANKING77 seeds but mixed in CLINC150.',
 'MAIN_H;MAIN_MATRIX','H4; Primary rows','Full-test mean true-label NLL; not accuracy',
 'was not supported; remained mixed','has no global effect; universally collapses','BANKING77 Primary positive in both learners; extreme M3 REAL_PI1 cell','5;7','Table 1')
claim('MC05','C06','SUPPORTING',
 'Matched-concentration CONTROL contrasts weaken a smoothness-only explanation in CLINC150 RoBERTa and both BANKING77 learners; CLINC150 XLNet remains non-unanimous.',
 'CONTROL_INVARIANTS;CROB_FINAL;CROB_VALUES;CXL_FINAL;CXL_VALUES;BANK_CONTROL_FINAL;BANK_CONTROL_VALUES',
 'Exact invariants; per-seed Secondary/LocalNLL; fourth-cell boundary','One CONTROL realization per dataset; four seeds per learner',
 'weaken; show insufficiency for the matched contrasts','smoothness has zero effect; uniquely identifies assignment mechanism; overall confirmed',
 'CLINC XLNet Secondary ++-- and LocalNLL -+--; perturbation memberships differ from R1/R2','1;6.2;8','Table 2;Figure A inset')
claim('MC06','C07','SUPPORTING',
 'Saved-output accounting shows heterogeneous redistribution among true, shared-wrong, and other-wrong probabilities; increased shared-wrong mass need not imply worse true-label NLL.',
 'OUTPUT_DECOMP;DECOMP_VALUES;DECOMP_MEANS','Eight setting/comparator groups; mass and Jensen identities',
 'Descriptive accounting of existing outputs; sample stability LOW','accounts for; shows; describes',
 'identifies internal class-competition mediation; traces physical probability flow','CLINC RoBERTa R2 mean true probability increases while LocalNLL worsens','6.1','Figure B.A')
claim('MC07','C04','SUPPORTING',
 'RoBERTa local NLL directions repeated across the two observed dataset/Source settings, without establishing dataset-independent transportability.',
 'MAIN_H;MAIN_MATRIX','RoBERTa LocalNLL R1/R2; H3/H6','Datasets, Source panels and local memberships vary jointly',
 'repeated in both observed settings','generalizes to all datasets; isolates dataset causation','XLNet LocalNLL differs between CLINC150 and BANKING77','5;7','Table 1')
claim('MC08','C05','SUPPORTING',
 'BANKING77 local NLL directions repeated across both learners; the prespecified CLINC150 cross-learner LocalNLL replication remained unsupported.',
 'MAIN_H;MAIN_MATRIX;CXL_FINAL','H6; LocalNLL rows','Learner settings jointly differ in architecture, tokenizer and recipe',
 'repeated within BANKING77; remained unsupported','pure architecture effect; M3 rescues the original replication','CLINC XLNet -+--/-+-- and non-unanimous CONTROL','5;7','Table 1;Table 2')
claim('MC09','C08','NEGATIVE_RESULT',
 'Pristine representation alignment was mixed across settings and did not provide a unified explanation.',
 'STATIC_DIAGNOSTIC','Scientific verdict; representation family','Frozen pristine representation diagnostic only',
 'was mixed; did not provide','rules out all representation mechanisms; proves representation mediation',
 'BANKING77 positive associations do not generalize consistently to CLINC150','6.3','Figure B.B')
claim('MC10','C09','NEGATIVE_RESULT',
 'Initial head-gradient alignment for shared-wrong probability was mixed across the frozen diagnostic scope.',
 'STATIC_DIAGNOSTIC','SECONDARY_GRADIENT_ALIGNMENT','Initial head-only first-order diagnostic',
 'was mixed; showed limited association','identifies full-backbone gradient mechanism; gradients are irrelevant',
 'Setting-specific associations coexist with counterpatterns','6.3','Figure B.B')
claim('MC11','C09','NEGATIVE_RESULT',
 'Initial head-gradient alignment for LocalNLL did not coherently account for the CLINC150-versus-BANKING77 XLNet difference.',
 'STATIC_DIAGNOSTIC','LOCALNLL_GRADIENT_ALIGNMENT; cross-setting explanatory power',
 'Exploratory pristine first-order scores','did not account consistently; was mixed',
 'proves an Adam mediator; excludes all gradient effects','No unified explanation of the key LocalNLL contrast','6.3','Figure B.B')
claim('MC12','C10','NEGATIVE_RESULT',
 'The fixed lexical supervision-transfer proxy did not provide a general explanation: LocalNLL prediction failed the strict compatibility rule in all eight learner-seed comparisons.',
 'PROXY_FINAL','Strict support and paired-arm misalignment sections','CLINC150 REAL-CONTROL; common fixed lexical bridge; post-outcome exploratory',
 'did not support this proxy; was incompatible under the frozen rule',
 'disproves supervision structure; requires a new kernel','Two XLNet Secondary seeds pass; LocalNLL 8/8 gain_zero<0 and misalignment lower MAE','6.3','Figure B.B')
claim('MC13','C11','CORE',
 'In CLINC150 XLNet, the prespecified optimization-path intervention increased the REAL-CONTROL LocalNLL contrast in all four formal seeds, with heterogeneous magnitudes.',
 'M3_PROTOCOL;M3_TABLE;M3_RECOMPUTE;M3_FINAL','LocalNLL I=D_PI1-D_PI0; all four seeds',
 'One deterministic batch-reversal intervention; fresh paired 2x2; not a pure component effect',
 'changed under intervention; supports setting-level path sensitivity',
 'proves the mechanism; batch order is the cause; statistically significant; universal path dependence',
 'Mean strongly influenced by seed1852328752; no other setting/order tested','1;6.4;8','Figure B.C;Table 3')
claim('MC14','C11;C07','SUPPORTING',
 'Secondary interactions were mixed-direction while LocalNLL interactions were uniformly positive, demonstrating distinct final endpoint responses to the same intervention.',
 'M3_TABLE;M3_FINAL','Secondary +-++; LocalNLL ++++','Final-only responses; no onset or separate-mediator identification',
 'differed; were heterogeneous','two causal pathways identified; one endpoint is a surrogate for the other',
 'Extreme seed has negative Secondary I and positive LocalNLL I','6.4;7','Figure B.C;Table 3')
claim('MC15','C13','LIMITATION',
 'Training-state summaries diverged under the intervention, but neither test-effect onset nor a specific optimizer or dropout mediator was identified.',
 'M3_PROTOCOL;M3_FINAL;SYN_EXTREME_SEED_ADJUDICATION','Final-only test; trajectory section',
 'Logged loss/gradient and parameter/Adam norms','documents state divergence; leaves unresolved',
 'test degradation started at epoch X; Adam causes the effect; dropout causes the effect',
 'No intermediate test responses or mediator-isolating intervention','6.4;7','Figure B.C annotation')
claim('MC16','C04;C05;C11','LIMITATION',
 'Inference is bounded by four paired training seeds, shared REAL references for R1/R2, fixed realizations, and an outcome-aware study chronology.',
 'MAIN_CHRONOLOGY;CXL_FINAL;BANK_CONTROL_FINAL;PROXY_FINAL;M3_PROTOCOL',
 'Chronology and independence limitations; later coverage supersedes old status',
 'Whole evidence program; test held out from Student training is not necessarily untouched by the project',
 'is bounded; was exploratory; was frozen before its own new outcomes',
 'fully preregistered from inception; n=129 independent experiments; independent confirmation for every extension',
 'CLINC test previously exposed in Source selection; BANK XLNet chosen after BANK RoBERTa','4;7','All captions')
claim('MC17','C12;C14','FUTURE_WORK_ONLY',
 'The single-generation findings motivate studying recursive propagation and mitigation, neither of which is established here.',
 'SYN_MECHANISM_EXPERIMENT_COMPLETENESS;SYN_FINAL_MECHANISM_SYNTHESIS_ZH',
 'Future Work; historical weighting boundary','Unmeasured future scope; no new algorithm',
 'motivates; remains to be tested','recursive collapse is demonstrated; weighting mitigates collapse; proposes a validated algorithm',
 'No multi-generation execution or demonstrated mitigation benefit','7;8','None')
claim('MC18','C11;C13','LIMITATION',
 'Seed1852328752 is retained as a technically validated extreme response; it strongly influences the mean but does not determine the positive LocalNLL interaction signs.',
 'M3_TABLE;M3_FINAL;SYN_EXTREME_SEED_ADJUDICATION;SYN_DESCRIPTIVE_SENSITIVITY_SUMMARY',
 'Extreme cell and four-seed/leave-one-out arithmetic','LOO and medians POST-HOC DESCRIPTIVE; frozen primary uses all four seeds',
 'is retained; influences; limits generality','invalid because accuracy is low; robust after excluding failure; proves mechanism by itself',
 'REAL_PI1 accuracy approximately0.67%; Secondary mean sign flips in leave-extreme description','6.4;7','Figure B.C;Table 3')
assert len(claims)==18
outcsv('FINAL_MANUSCRIPT_CLAIMS.csv',claims)

write('FINAL_CONTRIBUTION_SET.md','''# Final contribution set — publication freeze

Exactly three empirical contributions; no algorithm novelty. Wording below is a claim specification, not drafted Introduction prose. Manuscript claim IDs MC01–MC18 organize evidence and do not replace H1–H6.

## Contribution 1 — Controlled phenomenon

**Exact wording:** “We establish that controlled changes to wrong-label assignments across inputs can alter downstream Student behavior while preserving measured Source quality, per-example Source correctness, true-label target mass, and Source-by-truth wrong-label marginals.”

Evidence: MC01; MAIN_H/H1, MAIN_MATRIX, CLINC_PRESERVATION, BANK_MANIPULATION. Scope: 48 main single-generation fits in four dataset/Source–learner settings, two fixed reorganizations, four paired training seeds. Measured quality means the preserved accuracy/correctness/confusion quantities, not every semantic property. R1/R2 can also change target concentration; only CONTROL adds exact per-row concentration matching.

Prohibited: algorithmic advance; isolated global-correlation cause; “always hurts”; Source identity as a direct Student input. Strongest counterexample to a stronger directional claim: CLINC150 XLNet LocalNLL -+-- for both R1/R2.

## Contribution 2 — Conditional consequence structure

**Exact wording:** “We characterize setting-dependent local consequences of wrong-label organization: shared-wrong probability and true-label NLL can dissociate, while robust global degradation is not supported across the studied settings.”

Evidence: MC02–04, MC06–08; Table1; OUTPUT_DECOMP. Local direction is clearer than a universal global-harm claim in positive settings; do not compare probability and NLL magnitudes as if they had a shared scale. Table1 retains Complement to support the local/global distinction directly. Scope: frozen Source-defined test subsets, not a new subgroup selected from Student outcomes.

Prohibited: every local sample harmed; universal local amplification; pure dataset/architecture effects. Strongest counterexamples: CLINC XLNet Secondary R1++++ coexists with LocalNLL -+--; mixed CLINC Primary; LOW sample-level stability.

## Contribution 3 — Bounded mechanism evidence

**Exact wording:** “Concentration-matched controls weaken a smoothness-only account in three studied settings, while the tested static diagnostics provide no unified explanation; a controlled optimization-path intervention supplies direct evidence of setting-level path sensitivity in CLINC150 XLNet.”

Evidence: MC05, MC09–15, MC18; four CONTROL adjudications, STATIC_DIAGNOSTIC, PROXY_FINAL, M3_TABLE/M3_FINAL. LocalNLL interaction is positive in four seeds, Secondary is mixed-direction, and effect sizes are heterogeneous. Scope: one matched CONTROL per dataset; one frozen batch-reversal intervention in one learner setting; static analyses exploratory.

Prohibited: complete mechanism proved; smoothness irrelevant; pure batch-order/dropout/Adam cause; static MIXED/negative results upgraded by M3. Strongest counterexamples/limits: CLINC XLNet CONTROL is NON_UNANIMOUS; proxy LocalNLL 8/8 fails; M3 extreme seed dominates the mean and reverses Secondary direction.

H1 SUPPORTED; H2/H3/H5/H6 PARTIALLY_SUPPORTED; H4 NOT_SUPPORTED; original CLINC H6 LocalNLL replication NOT_SUPPORTED. All UNCHANGED. A manuscript freeze is not submission approval or a novelty/acceptance guarantee.
''')

write('TERMINOLOGY_FREEZE.md','''# Terminology and estimand freeze

Use these exact English display names consistently. 中文解释仅用于本地规划。Source和Student是角色，不以模型名称替换角色。

| Term | Frozen meaning | Avoid |
|---|---|---|
| Source | One of the fixed three label-producing classifiers in a dataset/Source setting; predictions are hard class labels | LLM generator if not actually used; a direct Student input identity |
| Student | Learner trained on input x and aggregate soft target; RoBERTa or XLNet | Source ensemble at inference; recursive generation |
| REAL | Aggregate targets formed from original Source predictions | Ground-truth training; clean supervised baseline |
| R1 / R2 | Two fixed realizations of within-truth, per-Source wrong-label reorganization; original correct decisions retained | Two training seeds; unrelated algorithms; universally lower binary error correlation |
| concentration-matched CONTROL | Frozen wrong-label/input assignment control additionally preserving each row's sorted target probabilities | New main algorithm; smoothing removed; negative-control proxy shift |
| wrong-label organization | Assignment of erroneous class identities to inputs across Sources, under frozen correctness and marginal constraints | Generic correlation reduction; all quality dimensions |
| shared-failure local subset (L) | Official-test examples where at least two ORIGINAL REAL Sources predict the same wrong label, fixed before the relevant Student outcomes | All Sources must be wrong; changed training membership; post-hoc hard cases |
| shared-wrong label (w_j) | The repeated erroneous label defining test example j's membership in L; unique with three Sources | Student top-1 label; comparator-specific redefinition |
| Primary | Mean true-label NLL on the full official test set | Accuracy; LocalNLL renamed primary |
| Secondary | Mean Student probability on w_j over L | Probability of any wrong label; NLL; accuracy |
| LocalNLL | Mean true-label NLL over L | Percentage points; log of mean probability |
| Complement | Mean true-label NLL over T\\L | A separate independent dataset; probability complement |
| optimization-path intervention | Frozen reversal of full-size minibatch blocks within each epoch, with final partial batch held last; joint presentation/LR/RNG/trajectory intervention | Full-batch training; pure order effect; optimizer-only treatment |
| interaction I | Difference of paired REAL−CONTROL contrasts across π1 and π0 | Absolute treatment-arm performance; beneficial score |

## Notation and direction

Training row i; test row j; class k; learner m; training seed s; comparator c; Source index a (avoid conflating with seed s). Raw aggregate target q^c_i,k=(1/3)Σ_a 1[z^c_ai=k]. The training target is q̃^c=0.9q^c+0.1/K. q denotes aggregate supervision, not native Source probabilities. In Figure A show the smoothing box once and bind it to the unchanged recipe. p^c_m,s(j,k) is final Student softmax probability.

Let NLL^c_j=−ln p^c(j,y_j). Absolute arm values are Y^c_Primary=mean_T NLL^c; Y^c_Secondary=mean_L p^c(j,w_j); Y^c_LocalNLL=mean_L NLL^c; Y^c_Complement=mean_(T\\L) NLL^c. Every ordinary reported contrast is ΔY=Y_REAL−Y_c, c∈{R1,R2,CONTROL}. Positive Secondary means more probability on w_j; positive NLL means worse true-label scoring in REAL. Natural logarithms: NLL in nats; Secondary in unscaled probability units, not percentage points.

M3: D_s(π)=Y_REAL,s,π−Y_CONTROL,s,π; I_s=D_s(π1)−D_s(π0). Two-sided design, no beneficial sign. A positive I_LocalNLL means the REAL−CONTROL contrast increased, not necessarily that the REAL arm alone worsened by I.

Partition identity: ΔPrimary=(|L|/|T|)ΔLocalNLL+(|T\\L|/|T|)ΔComplement. CLINC150 T/L/complement=4500/129/4371; BANKING77=3080/304/2776. Train supervision rows are3000 and3066; these are different namespaces from test memberships. CLINC test was held out from Student training but exposed in Source evaluation/selection; do not call it project-wide untouched.

Signs use the ordered formal seeds listed in SEED_ORDER.json, never sorted by effect size. n=4 denotes paired training seeds. R1/R2 share REAL; cross-learner matching of integer seed labels is not stochastic matching. No pooled sample/seed inference.

Sources: CLINC_CONTRACT.targets/outcomes; ENDPOINT_CONTRACT; BANK_PACKAGE; BANK_LOCAL; INPUT_BINDINGS; M3_PROTOCOL. Static statuses are MIXED or NOT_SUPPORTED, separate from technical PASS. Prior stage statuses are not overwritten.
''')
js('SEED_ORDER.json',dict(seeds=seeds,source='CLINC_CONTRACT.FINAL_CONFIRMATORY_SEEDS; BANK_PACKAGE.student.seeds',interpretation='ordered symbols, not four independent datasets'))

# Figure maps include exact source paths and hashes as well as field selectors.
figa=[];figb=[]
def fmap(rows,element,eid,selector,transform,label,scope):
    rows.append(dict(element_id=element,evidence_id=eid,source_path=sources[eid]['path'],source_sha256=sources[eid]['sha256'],
                     source_selector=selector,transformation=transform,display_label=label,scope_or_warning=scope))
for element,eid,selector,label in [
 ('A1','CLINC_CONTRACT','targets.manipulation_semantics; targets.N/K','Sources → labeled training inputs'),
 ('A1','BANK_PACKAGE','student_supervision.rows; targets','BANK supervision3066'),
 ('A2','CLINC_PRESERVATION','source_results; source_weights_equal','correctness and marginals fixed'),
 ('A2','BANK_MANIPULATION','Invariants paragraph','sample/text/truth/Source identities fixed'),
 ('A2','INPUT_BINDINGS','targets[*].epsilon/rows/classes','equal votes q; identical smoothing'),
 ('A2-control','CONTROL_INVARIANTS','Mathematical constraint equivalence; Constructive feasibility','CONTROL-only concentration lock'),
 ('A3','CLINC_CONTRACT','outcomes.secondary.definition; outcomes.test','4500=129+4371'),
 ('A3','BANK_LOCAL','rule; size; complement_size','3080=304+2776'),
 ('A3','ENDPOINT_CONTRACT','Primary/Secondary/LocalNLL/Complement','final p → endpoints'),
 ('A4','MAIN_MATRIX','all dataset/learner rows','Results are in Table1'),
]: fmap(figa,element,eid,selector,'semantic schematic / exact frozen count; no invented observations',label,'Source IDs retained for audit; not supplied as Student inputs')
outcsv('FIGURE_A_DATA_MAP.csv',figa)
for comp in ['R1','R2']:
    fmap(figb,'B.A.'+comp,'DECOMP_VALUES',f'realization={comp}; group(dataset,learner); dp_true_mean/dp_shared_mean/dp_other_mean',
         'unweighted mean over four existing seed rows; retain all eight groups in FIGURE_B_OUTPUT_DATA.csv','Δp_true / Δp_shared / Δp_other','descriptive net accounting; no causal flow arrows')
for name,label in [('representation','MIXED'),('Secondary head-gradient','MIXED'),('LocalNLL head-gradient','MIXED')]:
    fmap(figb,'B.B.'+name,'STATIC_DIAGNOSTIC','Scientific verdict; top-level diagnostic states','literal status transcription',label,'technical PASS is not mechanism support')
fmap(figb,'B.B.proxy','PROXY_FINAL','Strict support; Paired-arm misalignment; Bridge coverage',
     'literal frozen summaries; no new metric','NOT_SUPPORTED; Secondary0/4 and2/4; LocalNLL0/4 and0/4','post-outcome exploratory; local samples not independent experiments')
for ep in ['Secondary','LocalNLL']:
    fmap(figb,'B.C.'+ep,'M3_TABLE',f'endpoint={ep}; all four seeds; D_PI0/D_PI1/I',
         'identity for each seed; mean/median only in Table3; no standardization',ep+' interactions','full numeric range; zero reference; no beneficial direction')
fmap(figb,'B.C.design','M3_PROTOCOL','Main estimand; frozen π1; RNG/dropout boundaries','schematic four-cell factor layout','REAL/CONTROL × π0/π1','joint controlled path intervention; mediators unisolated')
fmap(figb,'B.C.extreme','M3_FINAL','Strongest support and counterexample: seed1852328752',
     '0.006667 accuracy fraction ×100 ≈0.67%; approximate label only','technical PASS; REALπ1 accuracy≈0.67%','do not crop, discard or call bug')
fmap(figb,'B.C.limits','SYN_EXTREME_SEED_ADJUDICATION','Sections6–10','verbatim interpretation boundary','mean sensitive; all seeds retained','LOO and median POST-HOC DESCRIPTIVE')
outcsv('FIGURE_B_DATA_MAP.csv',figb)

write('FIGURE_A_SPEC.md','''# Figure A — Controlled design and manipulation

Frozen placement: Section3; one two-column schematic, approximately0.60 page including caption. It carries methods, not a second results plot. Claims MC01–03/MC05/MC16. Exact object bindings: FIGURE_A_DATA_MAP.csv.

## Reading order and panels

**A1, left: training namespace.** Fixed three Source columns over the same input rows x_i/truth y_i. Display abstract label tokens rather than invented natural-language examples or fabricated target numbers. REAL uses original tuples. R1 and R2 show within-truth, per-Source permutation among wrong decisions. Two fixed realizations, not two algorithms. Correct cells retain padlock glyphs. Source/truth identities are audit metadata.

**A2, center: frozen conditions and aggregate interface.** Branch at the Source prediction/assignment table, then aggregate each branch into q_REAL/q_R1/q_R2. Do not transform an already trained Student. Draw q=(1/3)Σ one-hot(Source hard label), then q̃=0.9q+0.1/K. Student receives only (x_i,q̃_i) and the frozen training procedure. No arrow from Source name, Source ID, or test labels into Student optimization. Draw two learner icons without architectural causal comparison.

A common invariant bracket spans REAL/R1/R2: measured Source quality (per-Source accuracy), Source×example correctness identity, q(true), Source×truth wrong-label marginals, sample/text/truth/Source identity, source count/weights, paired initialization/order/recipe within a setting. Label the manipulated operation “wrong-label identity ↔ input assignment.” Crucial caveat: R1/R2 may change agreement/concentration as consequences of that assignment; do not draw their entropy or sorted q as fixed.

**A2 inset: concentration-matched CONTROL.** A separate diagnostic branch from original Source tuples, not from R1/R2; adds per-row sorted q/vote partition matching, hence support/entropy/sum(q²) matching. These are redundant constraints in this three-Source setting. CONTROL cannot simultaneously reduce total same-wrong pair count under these exact constraints. Same CLINC CONTROL targets across the two learners. Direct numeric outcomes are Table2; no “four positive” icons.

**A3, right: held-out Student evaluation namespace.** Official test T splits into frozen Source-defined L and complement T\\L. L requires at least two ORIGINAL Sources sharing a wrong label w_j≠y_j, not all three wrong. Membership not recomputed under R1/R2/CONTROL and not intersected with changed train rows. CLINC1504500=129+4371; BANKING773080=304+2776. The same final p feeds full-test Primary NLL, local Secondary probability, LocalNLL, and Complement NLL. No test-to-training arrow. Footnote CLINC test had prior Source selection exposure.

## Encoding and caption obligations

Solid arrows = data construction, actual training/evaluation computation. Dashed arrow only for explicitly labeled untested future relation, preferably omit all such arrows here. Locks = exact frozen constraint, not quality superiority. Shape plus text distinguish arms in grayscale; never use red/green alone. NLL nats; probability unscaled. No recursive loop, no proposed algorithm badge, no optimizer mediator chain.

Caption must state single-generation, paired contrasts REAL−comparator, fixed local subsets, R1/R2 shared REAL, and the CONTROL-only extra concentration invariant. Allocation/marginal identity should be understandable without interpreting Source IDs as model inputs. Do not render illustrative label counts as measured examples. Alt text: original and reorganized Source hard-label assignments share correctness/marginals; only aggregated targets enter Student training; final predictions are scored globally and on a frozen shared-failure subset.
''')

write('FIGURE_B_SPEC.md','''# Figure B — Output accounting, static limits, dynamic intervention

Frozen placement Section6; one two-column figure, approximately0.80 page including caption. Three labeled panels. Data map binds every panel to formal authority. No new feature, proxy, bin, or diagnostic is calculated.

## Panel A — Output consequence decomposition (about25% width)

Eight row groups in fixed order CLINC RoB R1/R2, CLINC XL R1/R2, BANK RoB R1/R2, BANK XL R1/R2. For each row, plot three signed horizontal points at the four-seed means of Δp_true, Δp_shared, Δp_other from FIGURE_B_OUTPUT_DATA.csv. Shared horizontal probability scale and zero line; distinct shapes/text legend. Do not use a Sankey/causal flow diagram or positive-only stacked bar. Annotate sum=0 within original tolerance. LocalNLL values remain in Table1: −log(mean p) is not mean NLL. These are aggregate descriptive points, not eight independent groups for inference. All underlying seed rows remain bound to DECOMP_VALUES.

## Panel B — Static diagnostics (about25% width)

Four compact text rows: pristine representation MIXED; Secondary head-gradient MIXED; LocalNLL head-gradient MIXED; fixed lexical proxy NOT_SUPPORTED. Under proxy show Secondary strict support RoB0/4, XL2/4; LocalNLL0/4 both, misalignment lower MAE8/8. Add coverage126/129 changed-row support and no empty neighborhoods; queried-direction support41/129 and32/129 can move to caption. Status is scientific, not technical PASS. Mark post-outcome exploratory. Dotted enclosure labeled “candidate accounts tested,” with no solid causal arrow to M3 or output. Omit heatmap of invented support scores.

## Panel C — Controlled path interaction (about50% width)

Top schematic: fresh REAL/CONTROL × π0/π1 × four seeds. π0=B1…B93,B94(partial); π1=B93…B1,B94(partial), within-batch order unchanged. Joint intervention label explicitly includes sample-to-LR/dropout coupling and resulting optimization trajectory.

Below: two aligned horizontal per-seed interaction plots, Secondary probability and LocalNLL nats, each with its own clearly labeled axis. All four formal seeds appear in frozen order with matching shapes across endpoints. Dπ0 and Dπ1 are given in Table3; do not add redundant slope charts if unreadable. Show I=Dπ1−Dπ0 and zero reference. Exact minimum/maximum of all four points determine ranges with small symmetric padding: no broken/cropped axes, log transform, clipping or outlier removal. The full extreme point must remain visible. If a magnified inset is ever needed in rendering, full-range plot remains primary and all points are identifiable; no new analysis.

Seed1852328752 uses an outlined star and explicit ID, not color alone. Label REALπ1 accuracy≈0.67%, technical PASS, retained. Other three seed points receive equal prominence and normal labels. Display signs Secondary+-++, LocalNLL++++. Mean/median are in Table3, not mean-only bars. No significance stars, CI, p-value, beneficial direction, or claim of general path dependence.

## Caption/interpretation freeze

Evidence types differ: PanelA output accounting, PanelB exploratory diagnostics, PanelC actual frozen intervention. Solid connections in PanelC refer only to controlled factor/contrast construction; unisolated dropout/Adam components labeled “not isolated,” never a solid mediator chain. Final-only evaluation cannot locate test-effect onset. Extreme seed is a stability/generalization limitation and not a validation failure. All four seeds remain in frozen primary summaries; medians and leave-one-out descriptions are POST-HOC DESCRIPTIVE. This figure does not upgrade M1/M2, representation/gradient, or H1–H6.

No trajectory curve in this two-figure freeze: the evidence is retained in one Section6.4 sentence about training-state divergence, with no test onset attribution. Alt text should state all eight output groups, four static statuses, and all eight M3 interaction points including the extreme negative Secondary/positive LocalNLL pair.
''')

table1_md=mdtable(['Setting','c','Secondary mean [signs]','LocalNLL mean [signs]','Primary mean [signs]','Complement mean [signs]'],[
    [r['dataset']+' / '+r['learner'],r['comparator']]+[fmt(r[ep+'_mean'])+' ['+r[ep+'_signs']+']' for ep in endpoints] for r in table1])
write('TABLE_1_SPEC.md',f'''# Table1 — Main2×2 REAL−R1/R2 results

One two-column table, eight rows. Six logical columns: setting, comparator, then four endpoints. To avoid width inflation, each endpoint cell uses two lines: signed mean at six decimals, then four-symbol seed pattern. Merge dataset/learner labels across R1/R2 only for display. Headers carry units: Secondary probability; LocalNLL/Primary/Complement nats. Source precision retained in TABLE_1_DATA.csv; display rounding is not a new scientific tolerance.

{table1_md}

Complement decision: retain as one compact fourth-endpoint column in this main table. No appendix, supplementary table, or fourth main table is assumed. It supplies the local/global comparison alongside the exact partition equation in Method. Target approximately0.50 page including caption. Do not reduce font below template readability to fit; use two-line cells and full two-column width.

Caption obligations: all Δ=REAL−c; n=4 paired training seeds in SEED_ORDER.json; R1/R2 share REAL; positive NLL denotes REAL worse, positive Secondary denotes more shared-wrong probability. Signs are raw values before rounding. No p-values/stars, no best-method boldface, no pooling settings. CLINC XLNet LocalNLL negative/mixed signs and CLINC Primary mixed signs remain prominent.

Sources MAIN_MATRIX exact mean/sign fields, checked against MAIN_SEEDS. Result→claim: MC01–04, MC07–08, MC16. Primary remains the historical full-test endpoint despite paper emphasis on local consequences. Mixed signs do not demonstrate zero effect or equivalence.
''')

control_md=mdtable(['Setting','Secondary mean [signs]','LocalNLL mean [signs]','Directional status'],[
 [r['dataset']+' / '+r['learner'],fmt(r['Secondary_mean'])+' ['+r['Secondary_signs']+']',fmt(r['LocalNLL_mean'])+' ['+r['LocalNLL_signs']+']',r['directional_status']] for r in control])
write('CONTROL_TABLE_SPEC.md',f'''# Table2 — Concentration-matched CONTROL

Compact table, four setting rows, two mean/sign result columns and short status label. Approximately0.25 page-equivalent including caption. Full precision and source IDs in CONTROL_TABLE_DATA.csv.

{control_md}

Δ=REAL−CONTROL; Secondary in probability, LocalNLL in nats. Four seeds in fixed order. Display the fourth cell “NON_UNANIMOUS,” not “negative” or “failed training.” Four-setting coverage means measurement complete, not overall confirmation. No pooled average across rows or vote-count argument of3-vs-1. One CONTROL realization per dataset; same realization across learners within a dataset. CONTROL preserves per-row concentration/q(true)/Source correctness/marginals; R1/R2 perturbation memberships differ. Do not calculate an effect-retained percentage or smoothness mediation fraction.

Caption or adjacent sentence: positive local matched contrasts in three settings weaken smoothness-only sufficiency in those contrasts; no smoothness-zero-effect or unique mechanism claim. CLINC XLNet is post-outcome extension using the pre-existing frozen realization. All four outcomes were not originally preregistered together. Evidence CROB_VALUES/CXL_VALUES/BANK_CONTROL_VALUES with their final adjudications; claim MC05, limitations MC08/MC16. No new inferential test.
''')

absolute=mdtable(['Endpoint','Seed','Y REALπ0','Y CONTROLπ0','Y REALπ1','Y CONTROLπ1'],[
 [r['endpoint'],r['seed']]+[fmt(r[k]) for k in ['Y_REAL_PI0','Y_CONTROL_PI0','Y_REAL_PI1','Y_CONTROL_PI1']] for r in m3])
contrast_rows=[]
for s in seeds:
    row=[str(s)]
    for ep in ['Secondary','LocalNLL']:
        r=next(r for r in m3 if int(r['seed'])==s and r['endpoint']==ep)
        row += [fmt(r[k]) for k in ['D_PI0','D_PI1','I']]
    contrast_rows.append(row)
for stat in ['mean','median','sign_pattern']:
    row=[stat+('†' if stat=='median' else '')]
    for ep in ['Secondary','LocalNLL']:
        r=next(r for r in summary if r['endpoint']==ep and r['statistic']==stat)
        row += [r[k] if stat=='sign_pattern' else fmt(r[k]) for k in ['D_PI0','D_PI1','I']]
    contrast_rows.append(row)
contrast=mdtable(['Seed/statistic','SEC Dπ0','SEC Dπ1','SEC I','NLL Dπ0','NLL Dπ1','NLL I'],contrast_rows)
write('M3_RESULT_TABLE_SPEC.md',f'''# Table3 — Full fresh path2×2, no seed excluded

One numbered two-column table with two stacked panels; target0.80 page including caption. PanelA contains the four absolute arm values, eight endpoint×seed rows. PanelB contains Dπ0/Dπ1/I for both endpoints, four seed rows plus mean/median/sign summaries. This preserves the previous extreme-seed adjudication's absolute-Y transparency without squeezing14 numeric columns into one row. FigureB.C supplies per-seed interaction points. Table1/2/3 are the only three main tables.

## A. Absolute Y values

{absolute}

## B. Paired contrasts and interaction

{contrast}

Display at six decimals, exact values retained in M3_RESULT_TABLE_DATA.csv and M3_SUMMARY_DATA.csv. Probability units for Secondary; nats for NLL. All Δ and D use REAL−CONTROL. I=Dπ1−Dπ0, two-sided. Source: M3_TABLE, M3_RECOMPUTE, M3_FINAL; no reuse of historicalπ0 as an experimental cell despite numerically matching results.

† Median is POST-HOC DESCRIPTIVE; mean/sign retain frozen four-seed primary interpretation. No seed removed from either panel or primary mean. Footnote only: “POST-HOC DESCRIPTIVE: leaving out seed1852328752 gives LocalNLL mean I=+0.193197258121 nats (three positive interactions) and Secondary mean I=+0.037523609870; no exclusion rule or primary result is changed.” Complete all-seed LOO values remain in the prior descriptive artifact; this is not a confirmatory robustness analysis.

Extreme seed label: REALπ1 full-test accuracy≈0.67%, versus REALπ0≈92.73% and CONTROLπ1≈93.29%; these rounded annotations come from M3_FINAL, not LocalNLL converted to accuracy. Technical validator PASS. Strong influence on mean and Secondary direction must be stated. The remaining three LocalNLL I values are positive; do not let the star hide their magnitudes.

Interpretation: LocalNLL++++ supports this setting's controlled path sensitivity with heterogeneous magnitudes; Secondary+-++ is mixed-direction. The combined intervention does not isolate batch order, dropout, LR coupling, or Adam mediation. No inferential significance claim. Claims MC13–16/MC18; H1–H6 remain unchanged.
''')

write('MANUSCRIPT_SECTION_EVIDENCE_MAP.md','''# Section evidence allocation — frozen planning, no prose draft

Keep Sections6 and7 separate. Section6 reports distinct evidence types; Section7 makes limitations visible so they are not buried in figure captions. Narrow Related Work and omit historical pilot tables to fit10 pages. No appendix/supplement is required to state any core counterexample. Word ceilings below exclude captions/tables/references and are planning estimates, not simultaneous fill targets.

| Section | Purpose / claims | Figures / tables | Authority allocation | Page-equivalent ceiling including floats | English word ceiling |
|---|---|---|---|---:|---:|
| Abstract | Evidence skeleton only now; MC01/03/05/13/14/18 | none | MAIN_MATRIX, control sources, M3_TABLE |0.25|170|
|1 Introduction | Motivation and exactly3 empirical contributions; no algorithm claim; MC01–03/05/13 | refer ahead only | MAIN_H, final contribution freeze |0.80|430|
|2 Related Work | Position controlled error organization, multi-source supervision and optimization sensitivity; distinguish recursive motivation from evidence | none | No external literature assertions frozen here; primary-source bibliography to be verified in later authorized drafting |0.60|300|
|3 Problem Setup / Method | Source/Student roles; q vs smoothed q; R1/R2 manipulation; invariants; frozen endpoints and REAL−c; MC01/16 | FigureA | CLINC_CONTRACT, CLINC_PRESERVATION, BANK_PACKAGE/MANIPULATION/LOCAL, ENDPOINT_CONTRACT, CONTROL_INVARIANTS |1.15|350|
|4 Experimental Setup | dataset/Source split roles, two learners, four paired seeds, target identities, condition-specific budgets and final-only scoring; no main-recipe conflation | no extra setup table | CLINC_CONTRACT; BANK_PACKAGE; INPUT_BINDINGS links exact learner recipe contracts; MAIN_CHRONOLOGY; CXL_FINAL; M3_PROTOCOL |0.75|380|
|5 Main Results | eight comparator rows; conditional local/global effect and failure of uniform generalization; MC01–04/07–08 | Table1 incl Complement | MAIN_MATRIX, MAIN_SEEDS, MAIN_H |1.35|470|
|6 Mechanism Analysis |6.1 accounting;6.2 matched CONTROL;6.3 static diagnostics;6.4 path intervention | FigureB; Table2; Table3 | see allocation below |2.65|650|
|7 Discussion / Limitations | extreme seed, chronology, dependence, test exposure, no isolated mediator, future-only recursive/mitigation; MC15–18 | no new display | M3_FINAL; SYN_EXTREME_SEED_ADJUDICATION; MAIN_CHRONOLOGY; CXL_FINAL; BANK_CONTROL_FINAL; ENDPOINT_CONTRACT |0.65|350|
|8 Conclusion | bounded empirical consequence and path sensitivity; no H upgrade/new result | none | MC01/03/13/17 |0.15|80|
|References | verified primary bibliography within cap, not free pages | none | external metadata not supplied/fabricated by this freeze |1.15|not a prose quota|

## Section6 fixed allocation

6.1 Output redistribution: MC06; DECOMP_VALUES/OUTPUT_DECOMP; FigureB.A. Keep mass conservation and log nonlinearity; sample stability LOW and contribution MIXED. No new decomposition of M3.

6.2 Concentration-matched CONTROL: MC05; all4 adjudications/seed CSVs; Table2. Include fourth NON_UNANIMOUS cell and one-realization boundary. No mediation ratio.

6.3 Static diagnostics: MC09–12; STATIC_DIAGNOSTIC/PROXY_FINAL; FigureB.B. One compact paragraph each for pristine/head diagnostics and lexical falsification. Technical PASS does not establish mechanism. Proxy0/4 vs2/4 Secondary and LocalNLL8/8 negative gains retained.

6.4 Optimization-path intervention: MC13–15/18; M3_PROTOCOL/TABLE/RECOMPUTE/FINAL; Table3 and FigureB.C. Define D/I, fresh16 fits, frozen reversal and joint treatment, final-only test. Report all seed signs/magnitudes, extreme validity, both endpoint patterns. Trajectory gets one bounded state-divergence sentence, not a new curve/onset narrative.

## Evidence chronology and review roles

Whole2×2/CONTROL program was not fully preregistered. BANK XLNet followed BANK RoB outcomes; CONTROL and static diagnostics have documented post-outcome chronology. CLINC XL CONTROL reused the existing frozen realization after main outcomes. M3 protocol preceded its16 new outcomes within this outcome-aware program. Current median/LOO are POST-HOC DESCRIPTIVE. R1/R2 share REAL and local rows do not increase training replication count.

Authority index SOURCE_MANIFEST.json contains exact paths/hashes; data maps give selectors/transformations. Human author verification is NOT_RECORDED_THIS_STAGE, not falsely marked complete; this freeze authorizes only the next outline stage. No full manuscript, bibliography fabrication, submission certification, or source disclosure. Future citation/author/template checks are later editorial responsibilities, not an experimental blocker or reason for new training.
''')

budget=[('Title/author block',0.25),('Abstract',0.25),('Introduction',0.80),('Related Work',0.60),('Method',1.15),('Setup',0.75),('Results',1.35),('Mechanism',2.65),('Discussion',0.65),('Conclusion',0.15),('References',1.15),('Layout reserve',0.25)]
check('PAGE_BUDGET',abs(sum(x[1] for x in budget)-10.0)<1e-10,'10.00 inclusive pages; no appendix')
write('PAGE_BUDGET_PLAN.md','''# IEEE two-column10-page allocation

This freeze uses the user's supplied hard constraint: maximum10 pages, references included, no appendix. It does not assert a fresh verification of official2026 venue policy or template. No external manuscript material was transmitted. Page-equivalents account for two-column floats and captions; actual pagination awaits later layout.

'''+mdtable(['Component','Page-equivalent'],[[n,f'{v:.2f}'] for n,v in budget])+'''

**Total 10.00**: content/reference target 9.75 plus 0.25 reserve. Title/author area included; author names/affiliations are not invented. Prose ceilings total 3180 words; this is a compact empirical paper with space for displays, not an invitation to fill every maximum.

Display envelope already inside section budgets, not added again: Figure A 0.60 (Method); Table 1 0.50 (Results); Figure B 0.80, Table 2 0.25, Table 3 0.80 (Mechanism). Total display envelope 2.95 page-equivalents includes captions. References receive 1.15 pages; no assumed free reference overflow. Keep Section 7 separate with 0.65 pages to ensure chronology/extreme-seed/mediator boundaries remain legible.

If later typesetting overruns: consume0.25 reserve, shorten historical motivation/Related Work and repeated prose, then remove redundant textual summaries already in tables. Do not remove extreme seed, fourth CONTROL counterpattern, units/sign definitions, dependence/chronology limitations, or references; do not shrink below template readability. No appendix or undocumented supplement fallback. No fourth table or third main figure. No layout is rendered this turn; final font/line/float fit requires human-visible typeset review in an authorized later stage.
''')

write('ABSTRACT_EVIDENCE_SKELETON.md','''# Abstract evidence skeleton — not a drafted abstract

- **Problem [MC01/16]:** Common quality summaries do not specify how wrong-label identities align with inputs. The question is whether reorganizing those assignments changes single-generation Student behavior under matched correctness/marginal constraints. [CLINC_PRESERVATION; BANK_MANIPULATION]
- **Design [MC01]:** Controlled REAL/R1/R2 comparisons cover two dataset/Source settings and two learners with paired training seeds; separate concentration controls and a fresh path2×2 test alternatives. Do not call the entire program originally preregistered. [MAIN_H; MAIN_MATRIX; M3_PROTOCOL]
- **Main controlled finding [MC01/02]:** Wrong-label/input organization can change downstream outputs despite preserved measured correctness/quality and marginals. Direction depends on endpoint and realization. [MAIN_MATRIX]
- **Conditionality [MC03/04/08]:** Specific shared-wrong transfer and true-label NLL can dissociate, and robust global degradation is unsupported across settings. CLINC XLNet remains a counterpattern. [MAIN_MATRIX; OUTPUT_DECOMP]
- **Mechanism evidence [MC05/09–14]:** Matched-concentration findings in three settings weaken a smoothness-only explanation; tested static diagnostics do not unify the outcomes. The controlled CLINC XLNet path intervention changes the LocalNLL contrast in the same direction across four seeds, with heterogeneous magnitudes. [CONTROL sources; STATIC_DIAGNOSTIC; PROXY_FINAL; M3_TABLE]
- **Limitation [MC15–18]:** One extreme but technically valid seed strongly affects the interaction mean; the intervention does not isolate a mediator. Evidence is single-generation and setting-bounded, without recursive or mitigation claims. [M3_FINAL; SYN_EXTREME_SEED_ADJUDICATION]

Final abstract target≤170 words in the next authorized stage; no prose abstract generated here. No algorithm naming, statistical significance wording, or excessive numeric inventory.
''')

# Freeze gate: every claim/figure reference resolves; numerical sources unchanged.
for r in claims:
    for eid in r['evidence_source'].split(';'):
        assert eid in sources, (r['claim_id'],eid)
for r in figa+figb:
    assert r['evidence_id'] in sources
for eid,a in sources.items():
    check('INPUT_UNCHANGED_'+eid,digest(ROOT/a['path'])==a['sha256'],'read-only authority')
check('EXTREME_RETAINED',sum(int(r['seed'])==1852328752 for r in m3)==2,'both endpoints and all four absolute arm values retained')
check('CLAIM_CLASSES',set(r['classification'] for r in claims)=={'CORE','SUPPORTING','NEGATIVE_RESULT','LIMITATION','FUTURE_WORK_ONLY'},'all required classes present')

gates=[
 ('Figure/table provenance','PASS','A/B maps and three exact data exports bind paths, hashes, field selectors and transformations; schematic panels use no invented observations.'),
 ('Every claim has authority','PASS','18 manuscript claims resolve SOURCE_MANIFEST IDs; wording hash recorded. Human approval not fabricated.'),
 ('Counterexamples visible','PASS','CLINC XLNet; mixed CLINC Primary; negative proxy; heterogeneous M3 shown.'),
 ('Extreme seed retained','PASS','Both M3 panels, FigureB.C star and approximate accuracy label, all4 primary seeds retained.'),
 ('Post-hoc vs pre-outcome freeze','PASS','CONTROL/program chronology distinguished; M3 frozen before its new outcomes; median/LOO post-hoc descriptive.'),
 ('No causal overclaim','PASS','Controlled path contrast direct; mediators unknown; no pure order/dropout/Adam/architecture claim.'),
 ('No recursive overclaim','PASS','MC17 FUTURE_WORK_ONLY; no recursive experiment.'),
 ('No algorithm novelty overclaim','PASS','Exactly3 empirical contributions; R1/R2 controls not optimization algorithms.'),
 ('Sign convention','PASS','REAL−comparator; I=Dπ1−Dπ0; fixed seed order; signs before rounding.'),
 ('Endpoint definitions','PASS','Primary full-test NLL; Secondary local shared-wrong probability; LocalNLL local truth NLL; Complement NLL.'),
 ('REAL−comparator consistency','PASS','Table1/2/3, map, terminology and abstract skeleton use same direction.'),
 ('NLL units','PASS','Natural-log nats; no percentage-point NLL; probability scale kept unscaled.'),
 ('Numerical reconciliation','PASS',f'{len(checks)} arithmetic/identity/reference checks; threshold1e-12 only for re-reading/reconciling, not a new effect-size gate.'),
 ('Page budget','PASS','10.00 inclusive pages,3 tables,2 figures, no appendix; layout estimate not final render.'),
]
write('FREEZE_VALIDATION_REPORT.md','''# Manuscript claim/figure/table freeze validation

**A — READY_FOR_ABSTRACT_AND_OUTLINE.** No current scientific evidence conflict; no new scientific result. H1–H6 UNCHANGED. No additional mechanism training recommended. This is a local publication-spec freeze, not a human-approved submission or final typeset manuscript.

'''+mdtable(['Gate','Status','Evidence/check'],gates)+'''

## Historical status differences resolved by chronology

MAIN_CHRONOLOGY and BANK_CONTROL_FINAL contain old “CONTROL missing” sentences; later CXL_FINAL and final synthesis supersede coverage only. OUTPUT_DECOMP/STATIC_DIAGNOSTIC/PROXY_FINAL next-stage suggestions are historical, not current authority. METHOD_SCOPE's old “no Student yet” phase is preserved and superseded for present status by explicit later authorities. No numeric conflict requiring outcome re-adjudication was found; different raw/runner last bits in CXL are within the original tolerance and exact source values were retained in export.

## Evidence/access and editorial boundaries

M3 formal per-cell validity is cited from sealed execution/final authorities; no fresh remote per-cell revalidation, model load or weight read. M3 absolute/D/I arithmetic checked from saved summary CSV, not logits. File hashes checked locally. FigureB accounting means use existing seed-summary rows only, with no new subgroup or proxy analysis.

The scientific-writing skill requires human evidence verification before submission: this stage records assistant checks and leaves human verification unclaimed. It does not stop the user-authorized freeze or add an approval request. Current10-page restriction is user-supplied; official venue policy/template, citation bibliography, authorship/declarations and final rendering remain later editorial tasks, not evidence conflicts. No external literature claim is fabricated in Related Work.

Training/forward/backward/GPU/SSH/Git write all0. Old files remain unchanged. No manuscript prose/full abstract was drafted. Only permitted wording specifications, evidence skeleton and section allocation were written. Sole next stage MLBD2026_MANUSCRIPT_ABSTRACT_AND_OUTLINE_V1, NOT_STARTED.
''')
js('SOURCE_MANIFEST.json',dict(stage=STAGE,sources=list(sources.values()),human_verification='NOT_RECORDED_THIS_STAGE',scope='local reports/CSV/JSON only; no raw predictions, weights or remote audit'))
js('NUMERICAL_AND_IDENTITY_CHECKS.json',dict(status='PASS',checks=checks,training_runs=0,model_calls=0))
js('STAGE_STATUS.json',dict(stage=STAGE,run_id=HERE.name,status='COMPLETE',
    final_readiness='A — READY_FOR_ABSTRACT_AND_OUTLINE',contributions=3,manuscript_claims=len(claims),
    core_claims=sum(r['classification']=='CORE' for r in claims),main_figures=2,main_tables=3,
    page_budget_including_references=10.0,no_appendix=True,H1_H6='UNCHANGED',
    scientific_conflict='NONE',new_training_runs=0,new_forward=0,new_backward=0,new_gpu_use=0,ssh_use=0,git_write=0,
    new_predictions=0,new_proxy_analysis=0,full_manuscript_drafting=0,submission_ready=False,
    next_stage='MLBD2026_MANUSCRIPT_ABSTRACT_AND_OUTLINE_V1',next_stage_started=False))
outcsv('REGISTRY_ROWS.csv',[dict(run_id=HERE.name,stage=STAGE,status='COMPLETE',mode='LOCAL_PUBLICATION_SPEC_FREEZE',new_fits=0,git_write=0)])
write('RUN_LOG.md',f'''# Run log

UTC completion {datetime.now(timezone.utc).isoformat()}. Read designated synthesis and scoped original authorities. Reconciled existing main/control/M3 numbers; generated3 contribution specifications,18 claims,2 figures,3 tables and10-page allocation. Preserved all old files and negative/extreme results. No experiment or next-stage execution. Inputs and outputs hashed in stage_manifest.json.
''')
required=['FINAL_CONTRIBUTION_SET.md','FINAL_MANUSCRIPT_CLAIMS.csv','TERMINOLOGY_FREEZE.md','FIGURE_A_SPEC.md','FIGURE_A_DATA_MAP.csv','FIGURE_B_SPEC.md','FIGURE_B_DATA_MAP.csv','TABLE_1_SPEC.md','CONTROL_TABLE_SPEC.md','M3_RESULT_TABLE_SPEC.md','MANUSCRIPT_SECTION_EVIDENCE_MAP.md','PAGE_BUDGET_PLAN.md','ABSTRACT_EVIDENCE_SKELETON.md','FREEZE_VALIDATION_REPORT.md','STAGE_STATUS.json']
assert all((HERE/n).is_file() for n in required)
outputs=[dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='stage_manifest.json']
js('stage_manifest.json',dict(stage=STAGE,run_id=HERE.name,utc=datetime.now(timezone.utc).isoformat(),status='COMPLETE',
    inputs=list(sources.values()),files=outputs,artifact_check='PASS',required_deliverables=required+['stage_manifest.json'],
    git_write=0,git_commit='not captured; no code/config training snapshot or Git operation',
    validation_script='build_freeze.py',allowed_action='read-only evidence and new local publication specifications'))
print(json.dumps(dict(status='A — READY_FOR_ABSTRACT_AND_OUTLINE',claims=len(claims),checks=len(checks),sources=len(sources),outputs=len(outputs)+1),ensure_ascii=True))
