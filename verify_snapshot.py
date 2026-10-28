"""Check curated aggregates and regenerate a figure with networking disabled."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parent
FILES={'README.md','AUDIT.md','aggregate_results.json','plot_results.py','verify_snapshot.py',
       'requirements.txt','.gitattributes','.gitignore','figures/bounds.png','figures/bounds.svg'}


def aggregate(result):
    if result['classification']!='ONE_SHOT_CONDITIONAL_QUOTE_SCREEN_NOT_BACKTEST':raise ValueError('invalid label')
    if (result['book_requests'],result['tested_sides'],result['positive_before_cost_bounds'])!=(3,6,0):raise ValueError('count drift')
    for name in ('fees_financing_modelled','execution_qualified','historical_backtest','independent_confirmation','verified_edge'):
        if result[name] is not False:raise ValueError('unsupported qualification')
    expected={'ETH':('-6.62','-33.64'),'SOL':('-44.00','-177.00'),'XRP':('-11.00','-89.50')}
    if len(result['rows'])!=3 or {r['underlying'] for r in result['rows']}!=set(expected):raise ValueError('cohort drift')
    for row in result['rows']:
        if (row['buy_bound'],row['sell_bound'])!=expected[row['underlying']]:raise ValueError('aggregate drift')
        if any(not Decimal(row[k]).is_finite() or Decimal(row[k])>=0 for k in ('buy_bound','sell_bound')):raise ValueError('invalid recorded bound')


def main():
    def blocked(event,args):
        if event in {'socket.__new__','socket.connect','socket.getaddrinfo'}:raise RuntimeError('network disabled')
    sys.addaudithook(blocked)
    manifest=json.loads((ROOT/'SNAPSHOT_MANIFEST.json').read_text(encoding='utf-8'))
    if set(manifest['files'])!=FILES:raise ValueError('exact snapshot allowlist required')
    actual={str(p.relative_to(ROOT)).replace('\\','/') for p in ROOT.rglob('*') if p.is_file()
            and not any(part in {'.git','.venv','__pycache__','reproduced_figures'} for part in p.relative_to(ROOT).parts)}
    if actual!=FILES|{'SNAPSHOT_MANIFEST.json'}:raise ValueError('unexpected or missing snapshot files')
    for name,digest in manifest['files'].items():
        path=(ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('artifact drift')
    result=json.loads((ROOT/'aggregate_results.json').read_text(encoding='utf-8'));aggregate(result)
    altered=copy.deepcopy(result);altered['rows'][0]['buy_bound']='1.00'
    try:aggregate(altered)
    except ValueError:pass
    else:raise AssertionError('altered result accepted')
    import plot_results
    with tempfile.TemporaryDirectory(prefix='option-bounds-render-') as temp:
        plot_results.render(temp)
        for ext in ('png','svg'):
            if (Path(temp)/('bounds.'+ext)).stat().st_size<1000:raise ValueError('empty rendering')
    print('PASS: exact curated files, six recorded bounds, altered-value rejection and offline rendering')
    print('This verifies snapshot consistency, not original quote acquisition or trading performance.')


if __name__=='__main__':main()
