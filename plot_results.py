"""Plot saved aggregate bounds only; no data acquisition or strategy replay."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
matplotlib.rcParams['svg.hashsalt']='e15-option-spread-bounds'
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent


def render(destination=None):
    result=json.loads((ROOT/'aggregate_results.json').read_text(encoding='utf-8'))
    if result['classification']!='ONE_SHOT_CONDITIONAL_QUOTE_SCREEN_NOT_BACKTEST':
        raise ValueError('unexpected result type')
    target=Path(destination) if destination else ROOT/'reproduced_figures'
    target.mkdir(parents=True,exist_ok=True)
    fig,ax=plt.subplots(figsize=(8.5,5.5),layout='constrained')
    positions=list(range(3))
    for direction,offset,color in [('buy',-.18,'#2c7591'),('sell',.18,'#bd7541')]:
        values=[float(r[direction+'_bound']) for r in result['rows']]
        ax.bar([x+offset for x in positions],values,.34,label=direction.capitalize()+' bound',color=color)
    ax.axhline(0,color='#444444',linewidth=1)
    ax.set(xticks=positions,xticklabels=[r['underlying'] for r in result['rows']],
           ylabel='Direct bound, USDC before all costs',
           title='One-shot option-spread screen: no positive direct bound')
    ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);ax.legend(loc='lower left')
    fig.text(.5,-.05,'Recorded bounds at different fixed position sizes. Not realized PnL or independent trials.',ha='center',fontsize=9)
    fig.savefig(target/'bounds.png',dpi=160,bbox_inches='tight')
    fig.savefig(target/'bounds.svg',dpi=160,bbox_inches='tight',metadata={'Date':None})
    plt.close(fig)
    print('PASS: aggregate figure rendered without market data')


if __name__=='__main__':render()
