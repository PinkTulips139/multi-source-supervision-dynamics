"""Deterministic vector figures from frozen display summaries; no new analysis."""
from pathlib import Path
import csv, json, hashlib, os
from collections import Counter
S=Path(__file__).resolve().parent.parent
os.environ['MPLCONFIGDIR']=str(S/'toolchain/matplotlib_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Arc
import numpy as np
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'xtick.labelsize':7,'ytick.labelsize':7,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','svg.hashsalt':'mlbd2026-frozen-figures-v1'})
P=(S/'project' if (S/'project/main.tex').exists() else S)/'figures'
V=S/'preview';P.mkdir(exist_ok=True);V.mkdir(exist_ok=True)
C={'blue':'#275b82','orange':'#b35e28','green':'#31756b','ink':'#172734','line':'#71808c','pale':'#f2f5f7'}
def save(fig,name):
    fig.savefig(P/f'{name}.pdf',metadata={'CreationDate':None,'ModDate':None,'Creator':'Frozen MLBD figure script'})
    fig.savefig(P/f'{name}.svg',metadata={'Date':None})
    fig.savefig(V/f'{name}.png',dpi=200)
    plt.close(fig)

fig=plt.figure(figsize=(7.16,5.2));ax=fig.add_axes([.015,.015,.97,.97]);ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
def box(x,y,w,h,color='white',edge=C['line'],dashed=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.35,rounding_size=1',linewidth=.7,edgecolor=edge,facecolor=color,linestyle='--' if dashed else '-'))
def txt(x,y,s,size=7.5,weight='normal',ha='left',va='top',color=C['ink']):
    ax.text(x,y,s,fontsize=size,fontweight=weight,ha=ha,va=va,color=color,linespacing=1.28)
def arrow(x,y,u,v):
    ax.annotate('',(u,v),(x,y),arrowprops={'arrowstyle':'-|>','lw':.8,'color':C['line']})
txt(1,99,'TRAINING  |  fixed inputs and supervision construction',9,'bold')
# Two invented rows, never a project target or scientific observation.
# This legal example preserves even CONTROL's extra locks; R1/R2 need not do so.
before=[('t','a','c'),('t','b','c')];after=[before[1],before[0]]
assert all([x=='t' for x in a]==[x=='t' for x in b] for a,b in zip(before,after))
assert all(Counter(a[s] for a in before)==Counter(a[s] for a in after) for s in range(3))
assert all(sorted(Counter(a).values())==sorted(Counter(b).values()) for a,b in zip(before,after))
assert all(Counter(a)['t']==Counter(b)['t'] for a,b in zip(before,after))
box(1,66,60,28,C['pale'])
txt(2.5,92.5,'Schematic reassignment in one truth block (not observations)',7.6,'bold')
txt(2.5,88.5,r'Same truth $\tau$; distinct wrong classes $a,b,c\ne\tau$',7)
txt(17,84,'REAL: before',7.5,'bold',ha='center')
txt(47,84,'Legal after',7.5,'bold',ha='center')
for y,sid,old,new in [(79,r'$x_i$',r'$(\tau, a, c)$',r'$(\tau, b, c)$'),(73.5,r'$x_{i^{\prime}}$',r'$(\tau, b, c)$',r'$(\tau, a, c)$')]:
    txt(2.5,y,sid,9);txt(17,y,old,10,ha='center');txt(47,y,new,10,ha='center');arrow(28,y-1.8,35,y-1.8)
txt(2.5,68.6,'Tuple order: Source 1, 2, 3. Correct cells and marginals stay fixed.',6.6)
txt(1,64.3,'R1/R2: permute wrong cells. CONTROL: cycle eligible whole tuples.',6.7)
box(66,82,33,12,C['pale']);txt(82.5,92,'Equal-vote aggregate',8,'bold',ha='center')
txt(82.5,87,r'$q_{ik}=\frac{1}{3}\sum_a\mathbf{1}\{z_{ai}=k\}$',10,ha='center')
arrow(61.5,87.5,65.3,87.5)
box(66,67.5,33,10.5,C['pale']);txt(82.5,76.5,'Smoothing (once)',8,'bold',ha='center');txt(82.5,72,r'$\widetilde q=0.9q+0.1/K$',9,ha='center');arrow(82.5,81.5,82.5,78.5)
box(66,49,33,14.5,'#edf4f4');txt(82.5,62,'Student receives only',8,'bold',ha='center');txt(82.5,57.5,r'$(x_i,\widetilde q_i)$',10,ha='center');txt(82.5,53,'RoBERTa  |  XLNet',7.5,ha='center');arrow(82.5,67,82.5,64)
txt(66,47,'No Source-ID or test-truth input.',7)
box(1,42,60,18.5);txt(2.5,59,'COMMON LOCKS: REAL / R1 / R2 (and CONTROL)',7.7,'bold')
txt(2.5,55,'Per-Source accuracy and per-example correctness; q(true)\nSource × truth wrong-label marginals; sample/text/truth/Source IDs\nThree equal-weight Sources; paired init/order/recipe within setting',7)
txt(2.5,44.3,'R1/R2 agreement and concentration may change.',7,'bold')
box(1,28,60,11.2,'#fcf5ed');txt(2.5,38,'CONTROL EXTRA LOCK: sorted target row / vote partition',7.5,'bold')
txt(2.5,34,'Raw-target support size, entropy and sum(q²); same-wrong total fixed.\nNot a fixed class set; CONTROL shared by learners within each dataset.',6.6)
txt(66,39,'REAL ≠ ground-truth baseline.\nSingle generation; no recursion.\nSource/truth IDs are audit metadata.',6.9)
ax.plot([0,100],[25.7,25.7],color=C['line'],lw=.8)
txt(1,24.5,'TEST / EVALUATION  |  fixed before relevant Student outcomes',8.5,'bold')
box(1,1,60,19);txt(2.5,19,'Official test T = local L + complement T \\ L',7.5,'bold')
txt(2.5,15.2,'L: ≥2 original Sources share wrong label wⱼ ≠ yⱼ.\nMembership fixed; not changed training rows or Student errors.\nCLINC150: 4500 = 129 + 4371\nBANKING77: 3080 = 304 + 2776',7)
box(66,1,33,19,C['pale']);txt(67.5,19,'Final p → four endpoints',7.5,'bold')
txt(67.5,15.2,'Primary: NLL on T\nSecondary: p(wⱼ) on L\nLocalNLL: NLL on L\nComplement: NLL on T \\ L',7)
arrow(98.8,49,98.8,21)
arrow(61.5,10,65.3,10)
save(fig,'figure_a')

data=list(csv.DictReader((S/'figure_sources/frozen_inputs/FIGURE_B_OUTPUT_DATA.csv').open(encoding='utf-8-sig')))
m3=list(csv.DictReader((S/'figure_sources/frozen_inputs/M3_RESULT_TABLE_DATA.csv').open(encoding='utf-8-sig')))
assert len(data)==8 and len(m3)==8
seeds=list(dict.fromkeys(r['seed'] for r in m3))
fig=plt.figure(figsize=(7.16,6.25))
fig.text(.02,.977,'A  Output consequence accounting',fontsize=9,fontweight='bold',va='top')
fig.text(.02,.95,'REAL − comparator; frozen local subsets',fontsize=7.5,va='top')
a=fig.add_axes([.175,.615,.315,.27]);a.axvline(0,color=C['line'],lw=.7,zorder=0)
for key,label,marker,color,offset in [('dp_true_mean','True','o',C['blue'],-.17),('dp_shared_mean','Shared-wrong','s',C['orange'],0),('dp_other_mean','Other-wrong','^',C['green'],.17)]:
    a.scatter([float(x[key]) for x in data],np.arange(8)+offset,s=24,marker=marker,color=color,label=label,zorder=3)
a.set_yticks(range(8),[f"{'CLINC' if x['dataset']=='CLINC150' else 'BANK'} {'RoB' if x['learner']=='RoBERTa' else 'XL'} {x['comparator']}" for x in data]);a.invert_yaxis();a.set_xlim(-.105,.135);a.set_xticks([-.1,0,.1]);a.set_xlabel('Mean probability difference');a.grid(axis='x',alpha=.16)
a.spines[['top','right']].set_visible(False)
a.legend(loc='lower left',bbox_to_anchor=(-.51,1.0),ncol=3,frameon=False,fontsize=6.8,handletextpad=.3,columnspacing=.9)
fig.text(.025,.535,'True + shared + other = 0 (frozen tolerance).\nOutput accounting; no causal flow or seed-level inference.',fontsize=7.1,va='top')

b=fig.add_axes([.55,.535,.425,.435]);b.axis('off')
b.add_patch(Rectangle((0,0),1,1,transform=b.transAxes,fill=False,linestyle=':',edgecolor=C['line']))
b.text(.035,.98,'B  Candidate accounts tested',fontsize=9,fontweight='bold',va='top')
b.text(.035,.89,'Post-outcome exploratory diagnostics',fontsize=7.2,va='top')
rows=[('Pristine representation','MIXED'),('Secondary head-gradient','MIXED'),('LocalNLL head-gradient','MIXED'),('Fixed lexical proxy','NOT_SUPPORTED')]
for y,(label,status) in zip([.77,.64,.51,.38],rows):
    b.text(.035,y,label,fontsize=7.2,va='top');b.text(.96,y-.049,status,fontsize=7.2,fontweight='bold',va='top',ha='right')
b.text(.035,.235,'Proxy strict support:\nSecondary: RoB 0/4; XL 2/4\nLocalNLL: 0/4 both; misalignment lower MAE 8/8\nChanged-row coverage 126/129; empty = 0',fontsize=6.9,va='top',linespacing=1.35)
fig.text(.02,.465,'C  Controlled optimization-path interaction  |  CLINC150 × XLNet',fontsize=9,fontweight='bold')
fig.text(.02,.439,'Fresh REAL/CONTROL × π₀/π₁ × four seeds;  I = D(π₁) − D(π₀)',fontsize=8)
fig.text(.02,.415,'π₀: B₁ … B₉₃, B₉₄(partial24) → π₁: B₉₃ … B₁, B₉₄(partial24); within-batch order fixed.',fontsize=7.2)
fig.text(.02,.393,'Joint presentation, sample-to-LR/dropout coupling and resulting trajectory; mediators not isolated.',fontsize=7.1)
markers=['o','*','s','^']
for endpoint,rect,unit,sign in [('Secondary',[.175,.145,.315,.205],'probability','+-++'),('LocalNLL',[.67,.145,.305,.205],'nats','++++')]:
    ax=fig.add_axes(rect);vals=[float(next(x for x in m3 if x['seed']==seed and x['endpoint']==endpoint)['I']) for seed in seeds]
    lo=min(0,min(vals));hi=max(0,max(vals));pad=(hi-lo)*.12
    ax.set_xlim(lo-pad,hi+pad);ax.set_ylim(3.55,-.55);ax.axvline(0,color=C['line'],lw=.8)
    for y,(v,marker) in enumerate(zip(vals,markers)):
        ax.scatter([v],[y],s=95 if y==1 else 35,marker=marker,facecolor='white' if y==1 else C['blue'],edgecolor=C['orange'] if y==1 else C['blue'],linewidth=1.1,zorder=3)
    ax.set_yticks(range(4),seeds);ax.tick_params(axis='y',labelsize=7);ax.set_title(f'{endpoint}  |  signs {sign}',fontsize=8.5,pad=7)
    ax.set_xlabel(f'Interaction I ({unit})',fontsize=8);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.15)
fig.text(.02,.055,'Outlined star: seed 1852328752, REAL π₁ accuracy ≈0.67%; technical validator PASS, retained.',fontsize=7.4)
fig.text(.02,.028,'All seeds shown at full range. Final-only evaluation: no test-effect onset or identified Adam/dropout mediator.',fontsize=7.1)
save(fig,'figure_b')
receipt={'data_source':'Frozen display CSVs only; no results recomputed','ordered_seed_ids':seeds,'decomposition_rows':len(data),'M3_endpoint_rows':len(m3),'layout_adjustment':'A/B above, C full width below; Figure A training above evaluation to preserve legibility. Same frozen content, groups, seeds and endpoints.','minimum_designed_font_pt':6.5}
receipt['v2_revision']='Figure A paired before/after schematic and raw-target support size clarification; Figure B unchanged.'
receipt['schematic_validation']={'invented_only':True,'source_correctness':True,'source_truth_marginals':True,'truth_votes':True,'sorted_vote_multiplicity':True,'text_sample_ids_fixed':True,'real_observations_used':False,'not_a_general_R1_R2_concentration_constraint':True}
(S/'figure_sources/FIGURE_GENERATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print('FIGURES_CREATED_VECTOR_PDF_SVG_AND_PNG')
