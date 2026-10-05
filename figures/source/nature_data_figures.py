"""Render the eight manuscript data figures from frozen plotting inputs.

No training, inference, resampling, hypothesis tests or source-table writes.
Approved display values follow the existing manuscript and figure generators.
Run from any directory; output defaults to build/figures.
"""
import argparse
import csv
import hashlib
import json
from itertools import combinations
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.transforms import ScaledTranslation
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    'data/figure_inputs/figdata_frozen.json',
    'data/figure_inputs/sa14_plot_data.json',
    'data/figure_inputs/drawing_data.json',
    'data/figure_inputs/corrections.json',
    'data/derived/participant_fractions.csv',
]
F, E, W, C = [json.loads((ROOT / p).read_text()) for p in INPUTS[:4]]
BLUE, ORANGE, GREEN, PINK, GREY = '#0072B2', '#D55E00', '#009E73', '#CC79A7', '#707070'
MODEL_KEYS = ['catch22_rf', 'hydra', 'minirocket', 'multirocket', 'rocket']
MODEL_NAMES = ['catch22 + RF', 'HYDRA', 'MiniRocket', 'MultiRocket', 'ROCKET']
MODEL_COLORS = [PINK, ORANGE, BLUE, GREEN, '#333333']
MODEL_MARKERS = ['s', 'D', 'o', '^', 'd']
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 7, 'axes.labelsize': 7,
    'axes.titlesize': 7, 'axes.titleweight': 'normal',
    'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.5,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': .55, 'xtick.major.width': .55, 'ytick.major.width': .55,
    'xtick.major.size': 2.5, 'ytick.major.size': 2.5,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'axes.grid': False, 'legend.frameon': False, 'lines.linewidth': .85,
    'lines.markersize': 3, 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'svg.fonttype': 'none', 'mathtext.fontset': 'custom',
    'mathtext.rm': 'Arial', 'mathtext.it': 'Arial:italic',
    'mathtext.bf': 'Arial:bold', 'mathtext.fallback': None,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
})
REPORT = {}


def panel(fig, ax, letter, title=''):
    pos = ax.get_position()
    fig.text(pos.x0 - .045, pos.y1 + .045, letter, weight='bold', size=8)
    ax.set_title(title, loc='left', pad=8)


def plot(ax, x, y, **kwargs):
    line, = ax.plot(x, y, **kwargs)
    np.testing.assert_array_equal(line.get_xdata(), x)
    np.testing.assert_array_equal(line.get_ydata(), y)
    return line


def save(fig, name, output, evidence):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    page = fig.bbox
    outside = []
    text_boxes = []
    for text in fig.findobj(matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            box = text.get_window_extent(renderer)
            text_boxes.append((text.get_text(), box))
            if box.x0 < -1 or box.y0 < -1 or box.x1 > page.x1 + 1 or box.y1 > page.y1 + 1:
                outside.append(text.get_text())
    if outside:
        raise ValueError(f'{name}: text outside page: {outside}')
    collisions = []
    for (first, a), (second, b) in combinations(text_boxes, 2):
        if min(a.x1, b.x1)-max(a.x0, b.x0) > .5 and min(a.y1, b.y1)-max(a.y0, b.y0) > .5:
            collisions.append((first, second))
    if collisions:
        raise ValueError(f'{name}: text collisions: {collisions}')
    for extension in ['pdf', 'svg', 'png']:
        fig.savefig(output / f'{name}.{extension}', dpi=300, facecolor='white')
    with Image.open(output / f'{name}.png') as image:
        image.convert('L').save(output / f'{name}.gray.png', dpi=(300, 300))
    REPORT[name] = {
        'width_in': float(fig.get_figwidth()), 'height_in': float(fig.get_figheight()),
        'text_outside_page': 0, 'text_collisions': 0, 'evidence': evidence,
        'pdf_sha256': hashlib.sha256((output / f'{name}.pdf').read_bytes()).hexdigest(),
    }
    plt.close(fig)


def figure07(output):
    fig = plt.figure(figsize=(7, 2.62))
    axes = [fig.add_axes([.085, .56, .89, .29]), fig.add_axes([.085, .16, .89, .29])]
    for i, (ax, example) in enumerate(zip(axes, W['examples'])):
        for start, stop in example['mask']:
            ax.axvspan(start, stop, color='#E69F00', alpha=.13, lw=0)
        for signal, color, ls in zip(example['signals'], [BLUE, GREEN, ORANGE], ['-', ':', '--']):
            plot(ax, example['time'], signal, color=color, ls=ls, lw=.8)
        for points, color, marker in zip(example['peaks'], [GREEN, BLUE, ORANGE], ['o', 'x', 'x']):
            if points:
                xy = np.array(points)
                ax.plot(xy[:, 0], xy[:, 1], ls='none', marker=marker, ms=2.9,
                        color=color, mfc='white' if marker == 'o' else color, mew=.55)
        lo, hi = np.min(example['signals']), np.max(example['signals'])
        ax.set(xlim=(0, 60), ylim=(lo - .12 * (hi - lo), hi + .12 * (hi - lo)),
               xticks=[0, 15, 30, 45, 60], yticks=[round(lo, 2), round(hi, 2)], ylabel='EDA (µS)')
        panel(fig, ax, 'ab'[i], f"{example['id']} · {'High' if i == 0 else 'Low'} artifact burden ({100 * example['fraction']:.1f}%)")
    axes[1].set_xlabel('Time within excerpt (s)', labelpad=2)
    axes[0].tick_params(axis='x', labelbottom=False)
    handles = [Line2D([], [], color=c, ls=s, label=l) for c, s, l in
               [(BLUE, '-', 'Raw'), (GREEN, ':', 'Expert reference'), (ORANGE, '--', 'Gated · CRG-A')]]
    handles += [Line2D([], [], color=GREEN, marker='o', mfc='white', ls='none', ms=3, label='Reference peak'),
                Line2D([], [], color='black', marker='x', ls='none', ms=3, label='Unmatched peak'),
                Patch(facecolor='#E69F00', alpha=.13, label='Artifact mask')]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.51, 1.015), ncol=6,
               columnspacing=1.1, handletextpad=.4, handlelength=1.8)
    save(fig, 'fig07_examples', output, 'Frozen E01/E14 signals, peak coordinates and artifact spans; no filtering or peak detection rerun.')


def figure08(output):
    fig = plt.figure(figsize=(7, 2.62))
    a, b = [fig.add_axes(p) for p in [[.085, .31, .36, .53], [.585, .31, .375, .53]]]
    records = W['detector']['records']
    for center, split, color, marker in [(0, 'Train', BLUE, 'o'), (1, 'Test', ORANGE, 's')]:
        values = np.array([r['auroc'] for r in records if r['split'] == split])
        x = center + np.linspace(-.22, .22, len(values))
        points = a.scatter(x, values, s=16, marker=marker, facecolors='white',
                           edgecolors=color, linewidths=.65, zorder=3)
        np.testing.assert_array_equal(points.get_offsets(), np.column_stack([x, values]))
    a.axhline(.9, color=GREY, ls='--', lw=.55)
    a.axhline(.9409, color=ORANGE, lw=.7)
    a.text(1.58, .9409, 'median', color=ORANGE, va='center', ha='right', size=6)
    a.text(1.58, .9, '0.90', color=GREY, va='center', ha='right', size=6)
    a.set(xlim=(-.38, 1.62), ylim=(.75, 1.005), xticks=[0, 1],
          xticklabels=['Train (n=33)', 'Test (n=10)'], yticks=[.8, .9, 1],
          xlabel='Fixed record split', ylabel='AUROC')
    a.tick_params(axis='x', labelsize=6.5)
    panel(fig, a, 'a', 'Record-level discrimination · CRG-A')
    fig.text(.085, .075, 'Overall median 0.9409; 36/43 records > 0.90', size=6.5)
    fractions = W['calibration']['fractions']
    x = [(lo + hi) / 2 for lo, hi in zip(W['calibration']['edges'][:-1], W['calibration']['edges'][1:])]
    valid = [i for i, value in enumerate(fractions) if value is not None]
    bin_counts = np.array([row[0] for row in W['calibration']['counts']])
    calibration_points = b.scatter(
        [x[i] for i in valid], [fractions[i] for i in valid],
        s=8 + 30 * np.sqrt(bin_counts[valid] / bin_counts.max()),
        color=ORANGE, edgecolors='white', linewidths=.35, alpha=.88, zorder=3)
    np.testing.assert_array_equal(
        calibration_points.get_offsets(),
        np.column_stack([[x[i] for i in valid], [fractions[i] for i in valid]]))
    b.plot([0, 1], [0, 1], color=GREY, ls='--', lw=.55, zorder=0)
    b.text(.18, .48, 'Ideal calibration', color=GREY, size=6)
    b.set(xlim=(0, 1), ylim=(0, 1), xticks=[0, .5, 1], yticks=[0, .5, 1],
          xlabel='Probability-bin midpoint', ylabel='Empirical artifact fraction')
    size_handles = [
        Line2D([], [], marker='o', ls='none', markerfacecolor=ORANGE,
               markeredgecolor='white', markersize=np.sqrt(8 + 30 * np.sqrt(count / bin_counts.max())),
               label=label)
        for count, label in [(10_000, '10k'), (100_000, '100k'), (1_000_000, '1m')]
    ]
    b.legend(handles=size_handles, title='Samples / bin', loc='upper left',
             fontsize=5.5, title_fontsize=5.5, handletextpad=.35,
             labelspacing=.35, borderaxespad=.45)
    panel(fig, b, 'b', 'Fixed-bin calibration · CRG-A')
    fig.text(.585, .075, 'Record medians: 0.209 / 0.067 (3.13×)', size=6.5)
    fig.text(.585, .025, 'Pooled fraction 0.1075; bubble area shows bin count', size=6.5)
    save(fig, 'fig08_detector', output, 'One jittered point per record; all 100 frozen calibration intervals plotted at their midpoints, with bubble area proportional to frozen sample counts. Record-median and pooled summaries remain distinct.')


def figure09(output):
    fig = plt.figure(figsize=(7, 2.32))
    data = F['decoupling']
    for i, (metric, title, upper) in enumerate([('mae', 'Artifact MAE (µS)', .65), ('f1', r'SCR $F_1$', 1)]):
        ax = fig.add_axes([.08 + i * .5, .29, .385, .56])
        values = np.array([data[metric + '_raw'], data[metric + '_gated']])
        for pair in values.T:
            plot(ax, [0, 1], pair, color='#A8B2B8', alpha=.6, lw=.35)
        for j, (color, marker) in enumerate([(BLUE, 'o'), (ORANGE, 's')]):
            plot(ax, np.full(data['n'], j), values[j], ls='none', marker=marker,
                 ms=2.4, color=color, mfc='white', mew=.5)
        # Same display aggregation as the existing paired-figure generator.
        means = values.mean(axis=1)
        plot(ax, [0, 1], means, color='black', lw=1.3, marker='o', mfc='white', ms=4)
        ax.set(xlim=(-.16, 1.16), ylim=(0, upper), xticks=[0, 1], xticklabels=['Raw', 'Gated'], ylabel=title)
        panel(fig, ax, 'ab'[i], 'CRG-B reconstruction' if i == 0 else 'CRG-B event preservation')
        note = 'Mean 0.1010 → 0.0830 (−17.8%)' if i == 0 else 'Mean 0.8980 → 0.8674 (−3.05 pp)'
        fig.text(.08 + i*.5, .145, note, size=6.5)
        fig.text(.08 + i*.5, .088, '43 paired records; thick line: mean' if i == 0 else '43/43 records worse', size=6.5)
    fig.text(.08, .026, 'Excess peaks: 11,108 → 12,989 (+16.9%); detected minus reference counts.', size=6.5)
    save(fig, 'fig09_decoupling', output, '43 frozen raw/gated pairs for each metric; display means use the unchanged arithmetic from the prior plotter.')


def figure10(output):
    fig = plt.figure(figsize=(7, 1.95))
    ax = fig.add_axes([.18, .28, .53, .64])
    ax.axvspan(-2.37, 2.37, color='#F2F2F2', zorder=0)
    ax.axvspan(-1.44, 1.44, color='#DCE9F0', zorder=0)
    ax.axvline(0, color='black', lw=.7)
    for x in [-2.37, 2.37]: ax.axvline(x, color=GREY, ls='--', lw=.55)
    rows = E['forest_whitelist']
    for i, (point, lo, hi) in enumerate(rows):
        ax.errorbar(point, 4-i, xerr=[[point-lo], [hi-point]], fmt='s' if i < 2 else MODEL_MARKERS[i],
                    color='black', mfc='black' if i < 2 else 'white', ms=3.5, lw=.7, capsize=2, mew=.6)
        ax.text(1.04, 4-i, f'{point:+.2f}  [{lo:+.2f}, {hi:+.2f}]'.replace('-', '−'),
                transform=ax.get_yaxis_transform(), va='center', size=7)
    ax.set(xlim=(-3, 3), ylim=(-.55, 4.55), yticks=range(5), yticklabels=MODEL_NAMES[::-1],
           xticks=[-3, -2, -1, 0, 1, 2, 3], xlabel='ΔBA, gated − raw (pp)')
    ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0, pad=7)
    ax.text(1.04, 1.045, 'Estimate [95% CI], pp', transform=ax.transAxes, size=7)
    fig.legend(handles=[Patch(facecolor='#DCE9F0', label='Mean design MDE ±1.44 pp'),
                        Patch(facecolor='#F2F2F2', edgecolor=GREY, lw=.4, label='Common equivalence boundary ≈ ±2.37 pp')],
               loc='lower center', bbox_to_anchor=(.52, -.015), ncol=2, handlelength=1.3, columnspacing=2)
    save(fig, 'fig10_forest', output, 'Exact accepted forest display whitelist, not newly rounded frozen endpoints. Shaded design/equivalence bounds are not CIs.')


def figure11(output):
    fig = plt.figure(figsize=(7, 2.15))
    a = fig.add_axes([.08, .29, .405, .54]); b = fig.add_axes([.675, .29, .295, .54])
    for i, curve in enumerate(E['curves']):
        plot(a, curve['margin'], curve['p'], color=MODEL_COLORS[i], marker=MODEL_MARKERS[i],
             mfc=MODEL_COLORS[i] if i < 2 else 'white', mew=.55, markevery=[35+i*10, 110+i*8, 190+i*8],
             label=MODEL_NAMES[i], ms=2.5)
    a.axhline(.05, color=GREY, ls='--', lw=.55)
    for x, label in [(2.37, '≈2.37'), (3.32, '3.32')]:
        a.axvline(x, color=GREY, ls='--', lw=.55)
        a.text(x, 1.035, label, ha='center', size=6.5)
    a.set(xlim=(0, 4), ylim=(0, 1), xticks=[0, 1, 2, 3, 4], yticks=[0, .5, 1],
          xlabel='Equivalence half-width δ (pp)', ylabel='TOST p-value')
    fig.legend(*a.get_legend_handles_labels(), loc='lower center', bbox_to_anchor=(.52, -.01),
               ncol=5, handlelength=1.8, columnspacing=1.8, fontsize=6.5)
    a.text(.03, .075, 'p = 0.05', transform=a.transAxes, size=6, color=GREY)
    panel(fig, a, 'a', 'Equivalence sensitivity')
    b.axvline(3, color=GREY, ls='--', lw=.55)
    for i, key in enumerate(MODEL_KEYS):
        value = C['bf'][key]['bf01']
        b.hlines(4-i, 0, value, color=MODEL_COLORS[i], lw=.8)
        b.plot(value, 4-i, marker=MODEL_MARKERS[i], color=MODEL_COLORS[i],
               mfc=MODEL_COLORS[i] if i < 2 else 'white', mew=.6, ms=3.5)
        b.text(3.15 if value > 2.5 else value+.14, 4-i, f'{value:.2f}', va='center', size=6.5)
    b.set(xlim=(0, 4), ylim=(-.55, 4.55), yticks=range(5), yticklabels=MODEL_NAMES[::-1],
          xticks=[0, 1, 2, 3, 4], xlabel=r'$\mathrm{BF}_{01}$')
    b.spines['left'].set_visible(False); b.tick_params(axis='y', length=0)
    panel(fig, b, 'b', 'Point-null evidence')
    save(fig, 'fig11_evidence', output, 'Frozen TOST curves plus accepted normalized-prior BF corrections; no tests or numerical integration rerun.')


def figure13(output):
    fig = plt.figure(figsize=(7, 2.42))
    a = fig.add_axes([.14, .60, .31, .20])
    detail = fig.add_axes([.14, .26, .31, .23])
    b = fig.add_axes([.58, .25, .39, .55])
    shares = [92.83, 3.46, 3.71]
    a.barh([0], [shares[0]], height=.55, color='#707070', linewidth=0)
    a.text(shares[0] - 1.5, 0, f'{shares[0]:.2f}%', va='center', ha='right',
           color='white', size=7, weight='bold')
    a.set(xlim=(0, 100), xticks=[0, 50, 100], ylim=(-.55, .55), yticks=[0],
          yticklabels=['Unchanged (%)'])
    a.spines['left'].set_visible(False); a.tick_params(axis='y', length=0, pad=5)
    detail.barh([1, 0], shares[1:], height=.48, color=[GREEN, PINK], linewidth=0)
    for y, value in zip([1, 0], shares[1:]):
        detail.text(value + .08, y, f'{value:.2f}%', va='center', size=6.5)
    detail.set(xlim=(0, 4.8), xticks=[0, 2, 4], ylim=(-.55, 1.55), yticks=[1, 0],
               yticklabels=['Corrected', 'Corrupted'], xlabel='Corrected / corrupted share (%)')
    detail.spines['left'].set_visible(False); detail.tick_params(axis='y', length=0, pad=4)
    panel(fig, a, 'a', 'Decision outcomes')
    fig.text(.14, .035, 'Model-mean percentages; N = 14,760', size=6.5)
    offsets = {'catch22_rf':(-7,-12), 'hydra':(7,-11), 'minirocket':(-7,8), 'multirocket':(7,8), 'rocket':(7,8)}
    for row in F['decision']['models']:
        i = MODEL_KEYS.index(row['model'])
        b.plot(row['crossed'], row['dacc'], marker=MODEL_MARKERS[i], color=MODEL_COLORS[i],
               mfc='white', ls='none', ms=4, mew=.65)
        dx,dy = offsets[row['model']]
        b.annotate(MODEL_NAMES[MODEL_KEYS.index(row['model'])], (row['crossed'],row['dacc']),
                   xytext=(dx,dy), textcoords='offset points', ha='right' if dx < 0 else 'left', fontsize=6.5)
    b.axhline(0, color=GREY, ls='--', lw=.55)
    b.set(xlim=(0, 12), ylim=(-2.5, 2.5), xticks=[0, 4, 8, 12], yticks=[-2, 0, 2],
          xlabel='Crossing rate (%)', ylabel='ΔACC (pp)')
    panel(fig, b, 'b', 'Crossing versus pooled accuracy')
    fig.text(.58, .035, 'ρ = −0.90; exact p = 0.083; n = 5 model families', size=6.5)
    save(fig, 'fig13_decision', output, 'Same approved model-mean shares and frozen crossed/dacc coordinates; exact p and n=5 retained. Small shares use a separate labeled detail axis; no trend line or new inference is added.')


def figure15(output):
    fig = plt.figure(figsize=(7, 3.75))
    arms = ['contaminated', 'oracle_localize', 'gate', 'matched_noise', 'oracle_exact']
    labels = ['Contaminated', 'Oracle localize', 'Gate', 'Matched noise', 'Exact oracle (input)']
    colors = [PINK, GREEN, ORANGE, BLUE, '#333333']; markers=['o', 's', 'x', 's', 'o']
    styles = ['-', '-', '--', '--', ':']
    for k, model in enumerate(['catch22_rf', 'minirocket']):
        ax = fig.add_axes([.08 + k*.50, .625, .385, .285])
        for i, arm in enumerate(arms):
            curve = next(row for row in F['injection']['curves'] if row['model'] == model and row['arm'] == arm)
            x,y,lo,hi=[np.array(curve[key]) for key in ['eff','ba','lo','hi']]
            # Offset only CI stems in display units. Curve coordinates stay exact.
            shift = ScaledTranslation((i-2)*2.0/72, 0, fig.dpi_scale_trans)
            bars = ax.errorbar(x, y, yerr=[y-lo, hi-y], fmt='none', ecolor=colors[i],
                              elinewidth=.5, capsize=1.5, capthick=.5,
                              transform=ax.transData + shift, alpha=.80)
            for segment, xx, lower, upper in zip(bars[2][0].get_segments(), x, lo, hi):
                np.testing.assert_allclose(segment, [[xx,lower],[xx,upper]], rtol=0, atol=1e-12)
            plot(ax,x,y,color=colors[i],ls=styles[i],marker=markers[i],mfc='white',mew=.6,ms=2.8,label=labels[i])
        ax.set(xlim=(-.8, 17.5), ylim=(54, 75), yticks=[55, 60, 65, 70, 75],
               xticks=[0, 4.42, 8.94, 16.7], xticklabels=['0 (0)', '4.42 (5)', '8.94 (20)', '16.70 (40)'],
               xlabel='Effective fraction % (nominal %)', ylabel='BA (%)')
        ax.tick_params(axis='x', labelsize=6.2)
        pos = ax.get_position()
        fig.text(pos.x0 - .045, pos.y1 + .022, 'ab'[k], weight='bold', size=8)
        ax.set_title('catch22 + RF' if k == 0 else 'MiniRocket', loc='left', pad=8)
    handles = [Line2D([],[],color=c,ls=s,marker=m,ms=3,mfc='white',label=l) for c,s,m,l in zip(colors,styles,markers,labels)]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.52,1.005),ncol=5,
               handlelength=2.2,columnspacing=1.4,handletextpad=.4)
    fig.text(.08,.525,'Dose intervals are participant-cluster CIs; stems are offset in legend order, curves use exact doses.',size=6)
    fig.text(.08,.445,'c',weight='bold',size=8)
    fig.text(.12,.445,'Prespecified validity endpoint and selected pooled contrasts',size=7)
    ax = fig.add_axes([.34,.115,.39,.285])
    rows=[('Validity endpoint · failed',-4.13,-8.33,.57,'#333333'),
          ('catch22 · oracle localized',3.32,1.86,4.76,GREEN),
          ('catch22 · gate',1.16,-1.13,3.31,ORANGE),
          ('catch22 · matched noise',-2.11,-3.82,-.08,BLUE),
          ('MiniRocket · oracle localized',-.29,-1.81,1.06,GREEN)]
    ax.axvline(0,color=GREY,ls='--',lw=.55)
    ax.axhline(3.5,color='#C9CED1',lw=.45)
    for i,(name,value,low,high,color) in enumerate(rows):
        y=4-i
        ax.errorbar(value,y,xerr=[[value-low],[high-value]],fmt='D' if i==0 else ('s' if i==4 else 'o'),
                    color=color,mfc='white',ms=3.5,mew=.6,lw=.75,capsize=2)
        ax.text(1.045,y,f'{value:+.2f}  [{low:+.2f}, {high:+.2f}]'.replace('-','−'),
                transform=ax.get_yaxis_transform(),va='center',size=6.1)
    ax.set(xlim=(-9,5),ylim=(-.55,4.55),xticks=[-8,-4,0,4],yticks=range(5),
           yticklabels=[r[0] for r in rows[::-1]],xlabel='Change versus contaminated input (pp)')
    ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0,labelsize=6.1,pad=5)
    save(fig,'fig15_injection',output,'All ten frozen curves and 40 original dose CIs retained. The prespecified validity endpoint and four approved pooled contrasts show the manuscript values and full display intervals; the unresolved oracle-CI provenance is unchanged. Only dose-CI stem display positions are offset, explicitly labelled.')


def figure16(output):
    fig = plt.figure(figsize=(7, 2.25))
    a=fig.add_axes([.08,.25,.385,.56]); b=fig.add_axes([.625,.25,.29,.56])
    values=[(11.25,1.52,17.31),(C['strat_pp'],*C['strat_ci'])]
    a.axvline(0,color=GREY,lw=.55,ls='--')
    for i,(value,low,high) in enumerate(values):
        y=1-i
        a.errorbar(value,y,xerr=[[value-low],[high-value]],fmt='s' if i==0 else 'o',
                    color=ORANGE if i==0 else '#333333',mfc=ORANGE if i==0 else 'white',ms=4,capsize=2,lw=.8,mew=.65)
        a.text(-4.5,y+.22,'Pooled split' if i==0 else 'Within-participant split',size=7,
               bbox={'facecolor':'white','edgecolor':'none','pad':.8})
        a.text(-4.5,y-.23,f'{value:+.2f} [{low:+.2f}, {high:+.2f}]'.replace('-','−'),size=6.5,
               bbox={'facecolor':'white','edgecolor':'none','pad':.8})
    a.set(xlim=(-5,20),ylim=(-.45,1.45),xticks=[-5,0,5,10,15,20],yticks=[],xlabel='Low − high proxy accuracy (pp)')
    a.spines['left'].set_visible(False)
    panel(fig,a,'a','Accuracy association')
    with (ROOT/INPUTS[4]).open() as handle: rows=sorted(csv.DictReader(handle),key=lambda r:float(r['within_participant_pct']),reverse=True)
    y=np.arange(len(rows))
    percentages=[float(row['within_participant_pct']) for row in rows]
    b.barh(y,percentages,color='#9CBBCB',height=.65,lw=0)
    for yy,value in zip(y,percentages):b.text(103,yy,f'{value:.1f}',va='center',size=6)
    b.set(xlim=(0,118),ylim=(10.7,-.7),yticks=y,yticklabels=[r['participant'] for r in rows],
          xticks=[0,50,100],xlabel='Above global proxy median (%)')
    b.tick_params(axis='y',length=0,labelsize=6);b.spines['left'].set_visible(False)
    panel(fig,b,'b','Participant heterogeneity')
    fig.text(.625,.035,'Top 3: 50.4% of all high-proxy windows',size=6.5)
    save(fig,'fig16_confound',output,'Accepted pooled and multiplicity-preserving within-person CIs; unchanged per-participant percentages from frozen CSV.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('figures',nargs='*',type=int,default=[7,8,9,10,11,13,15,16])
    parser.add_argument('--output',type=Path,default=ROOT/'build/figures')
    parser.add_argument('--publish',action='store_true',help='Synchronize verified outputs into the active figure and manuscript directories.')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS}
    for number in args.figures: globals()[f'figure{number:02d}'](args.output)
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS}
    manifest=args.output/'data_figure_manifest.json'
    previous=json.loads(manifest.read_text()).get('figures',{}) if manifest.exists() else {}
    previous.update(REPORT)
    manifest.write_text(json.dumps({'source_sha256':before,'figures':previous},indent=2)+'\n')
    if args.publish:
        for name in REPORT:
            for src,destination in [
                (args.output/f'{name}.pdf',ROOT/'paper/figures'/f'{name}.pdf'),
                (args.output/f'{name}.svg',ROOT/'build/figures'/f'{name}.svg'),
                (args.output/f'{name}.png',ROOT/'build/figures'/f'{name}.png'),
                (args.output/f'{name}.gray.png',ROOT/'build/figures'/f'{name}.gray.png')]:
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(src,destination)
    print(json.dumps(REPORT,indent=2))
