import numpy as np
def extract_14_features(events):
    backspaces = len([e for e in events if e['k'] == 'BackSpace' and e['a'] == 'p'])
    clean = [e for e in events if e['k'] not in ['Return', 'BackSpace']]
    if len(clean) < 6: return None
    h, l, d, r, p_times, lp, lr = [], [], [], [], {}, None, None
    for e in clean:
        k, t = e['k'], e['t'] * 1000 
        if e['a'] == 'p':
            if lp is not None: l.append(t - lp)
            p_times[k], lp = t, t
        else:
            if k in p_times:
                h.append(t - p_times[k])
                if lp is not None: d.append(t - lp)
            if lr is not None: r.append(t - lr)
            lr = t
    cpm = len(clean) / ((clean[-1]['t'] - clean[0]['t']) / 60000) if len(clean) > 1 else 0
    return [cpm, float(backspaces), np.mean(h), np.max(h), np.min(h), 
            np.mean(l), np.max(l), np.min(l), np.mean(d), np.max(d), np.min(d), 
            np.mean(r), np.max(r), np.min(r)]