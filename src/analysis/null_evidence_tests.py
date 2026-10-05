"""Equivalence tests (TOST), Bayes factors and design sensitivity for the VR05 null.

Answers the question a reviewer of a null result will ask: is this absence of
evidence, or evidence of absence?  Run:  python3 null_evidence_tests.py
"""
import numpy as np, pandas as pd, json, os
from scipy import stats, integrate

FOLD_METRICS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/derived/vr05_fold_metrics.csv')
ORACLE_EFFECT = 3.32   # pp, oracle-localisation repair benefit measured by the injection suite
MDE           = 1.44   # pp, 80%-power minimum detectable effect from the cluster bootstrap

def per_participant_deltas(path=FOLD_METRICS):
    v = pd.read_csv(path)
    w = v.pivot_table(index=['model','held_out','seed'], columns='arm',
                      values='balanced_accuracy').reset_index()
    w['delta'] = w['gated'] - w['raw']
    # protocol: average the three seeds *within* each participant first
    return w.groupby(['model','held_out'])['delta'].mean().unstack(0) * 100   # percentage points

def jzs_bf10(x, r=0.707):
    """Default JZS Bayes factor for a one-sample t-test (Rouder et al. 2009, PBR)."""
    n = len(x); t = stats.ttest_1samp(x, 0).statistic; df = n - 1
    f = lambda g: ((1+n*g)**-0.5 * (1+t**2/((1+n*g)*df))**(-(df+1)/2)
                   * (2*np.pi)**-0.5 * r * g**-1.5 * np.exp(-r**2/(2*g)))
    num, _ = integrate.quad(f, 0, np.inf)
    return num / (1 + t**2/df)**(-(df+1)/2)

def tost_p(x, bound):
    """Two one-sided tests: p for rejecting |true effect| >= bound."""
    n = len(x); m = x.mean(); se = x.std(ddof=1)/np.sqrt(n); df = n - 1
    return max(stats.t.sf((m+bound)/se, df), stats.t.cdf((m-bound)/se, df))

def equivalence_bound(x, alpha=0.05, lo=0.01, hi=15.0):
    """Smallest symmetric bound at which equivalence is established."""
    for _ in range(80):
        mid = (lo+hi)/2
        lo, hi = (lo, mid) if tost_p(x, mid) < alpha else (mid, hi)
    return hi

def main():
    pp = per_participant_deltas(); out = []
    for m in pp.columns:
        x = pp[m].dropna().values
        t, p = stats.ttest_1samp(x, 0)
        se = x.std(ddof=1)/np.sqrt(len(x)); bf10 = jzs_bf10(x)
        out.append(dict(model=m, n=len(x), mean_pp=x.mean(), se_pp=se,
                        t=t, p=p, cohen_dz=x.mean()/x.std(ddof=1),
                        bf10=bf10, bf01=1/bf10,
                        tost_p_at_mde=tost_p(x, MDE),
                        tost_p_at_oracle=tost_p(x, ORACLE_EFFECT),
                        equivalence_bound_pp=equivalence_bound(x)))
    df = pd.DataFrame(out)
    pd.set_option('display.width', 200)
    print(df.round(3).to_string(index=False)); print()
    print(f'Largest equivalence bound across models : +/-{df.equivalence_bound_pp.max():.2f} pp')
    print(f'Oracle-repair benefit (injection suite) : {ORACLE_EFFECT:.2f} pp')
    print(f'All five equivalent at the oracle bound : {bool((df.tost_p_at_oracle < .05).all())}')
    print(f'Any model with BF01 > 3 (null support)  : {bool((df.bf01 > 3).any())}'
          f'   [max BF01 = {df.bf01.max():.2f}]')
    output = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '../../data/derived/null_evidence_tests_recomputed.csv')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    df.to_csv(output, index=False)

if __name__ == '__main__':
    main()
