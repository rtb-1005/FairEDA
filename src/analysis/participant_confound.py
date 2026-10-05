"""Discussion 4.2: is the artifact-to-downstream association confounded by participant?

Naive analysis  : split all windows at the global median of a label-blind artifact
                  proxy, compare downstream accuracy between halves.
Stratified      : split within each participant at that participant's own median.
The difference between the two is the participant confound.
"""
import numpy as np, pandas as pd, json, os
PKG=os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/derived')
c1=np.load(f'{PKG}/C1_vrbd_windows.npz',allow_pickle=True)
raw=c1['raw'].astype(float); gat=c1['gated'].astype(float)
wid=c1['window_id']; part=c1['participant']; scale=c1['record_scale'].astype(float)

# label-blind artifact proxy: gate correction magnitude, scale-normalised
proxy=np.abs(gat-raw).mean(axis=1)/scale
W=pd.DataFrame(dict(window_id=wid,participant=part,proxy=proxy))

b=pd.read_csv(f'{PKG}/B1_window_scores.csv')
r=b[b.arm=='raw'].copy()
r['correct']=(r.predicted_label==r.label).astype(float)
acc=r.groupby('window_id')['correct'].mean().rename('acc')      # over models x seeds
W=W.merge(acc,on='window_id',how='inner')
print(f'{len(W)} windows, {W.participant.nunique()} participants\n')

rng=np.random.default_rng(20260825)
def cluster_boot(df, fn, n=20000):
    ps=df.participant.unique(); k=len(ps)
    obs=fn(df); draws=[]
    for _ in range(n):
        pick=rng.choice(ps,size=k,replace=True)
        d=pd.concat([df[df.participant==participant].assign(_bootstrap_cluster=cluster)
                     for cluster,participant in enumerate(pick)],ignore_index=True)
        v=fn(d)
        if v==v: draws.append(v)
    lo,hi=np.quantile(draws,[.025,.975])
    return 100*obs,100*lo,100*hi

def gap_naive(df):
    m=df.proxy.median()
    return df.loc[df.proxy<=m,'acc'].mean()-df.loc[df.proxy>m,'acc'].mean()

def gap_strat(df):
    g=[]
    for p,d in df.groupby('_bootstrap_cluster' if '_bootstrap_cluster' in df else 'participant'):
        m=d.proxy.median()
        lo,hi=d.loc[d.proxy<=m,'acc'],d.loc[d.proxy>m,'acc']
        if len(lo) and len(hi): g.append(lo.mean()-hi.mean())
    return float(np.mean(g)) if g else np.nan

n=cluster_boot(W,gap_naive); s=cluster_boot(W,gap_strat)
print('=== low-artifact minus high-artifact downstream accuracy (pp) ===')
print(f'  naive (pooled median split)      {n[0]:+6.2f}  95% CI [{n[1]:+.2f}, {n[2]:+.2f}]')
print(f'  within-participant median split  {s[0]:+6.2f}  95% CI [{s[1]:+.2f}, {s[2]:+.2f}]')
print(f'  confound-attributable inflation  {n[0]-s[0]:+6.2f} pp\n')

med=W.proxy.median(); hi=W[W.proxy>med]
conc=hi.participant.value_counts(normalize=True).sort_values(ascending=False)
print('=== concentration of high-artifact windows by participant ===')
print(f'  top participant holds {100*conc.iloc[0]:.1f}% of them; top 3 hold {100*conc.iloc[:3].sum():.1f}%')
print(f'  participants contributing 0 high-artifact windows: {(W.participant.nunique()-conc[conc>0].size)}')
pf=W.groupby('participant').apply(lambda d:(d.proxy>med).mean(),include_groups=False)
print(f'  per-participant share of windows above the global median: '
      f'min {100*pf.min():.1f}%  max {100*pf.max():.1f}%')
output = os.path.join(PKG, 'participant_confound_recomputed.json')
json.dump(dict(naive_pp=n[0],naive_ci=[n[1],n[2]],strat_pp=s[0],strat_ci=[s[1],s[2]],
               inflation_pp=n[0]-s[0],n_windows=int(len(W)),
               top1_share=float(conc.iloc[0]),top3_share=float(conc.iloc[:3].sum()),
               per_participant_share_min=float(pf.min()),per_participant_share_max=float(pf.max())),
          open(output,'w'),indent=1)
