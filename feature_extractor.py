import numpy as np

def extract_dna_features(events):
    if not events or len(events) < 10:
        return None

    backspaces = len([e for e in events if e['k'] == 'BackSpace' and e['a'] == 'p'])

    clean = [e for e in events if e['k'] not in ['Return', 'BackSpace', 'Shift_L', 'Shift_R']]
    if len(clean) < 6:
        return None

    hold_times, latencies, digraphs, releases = [], [], [], []
    p_times = {}
    last_p = last_r = None

    for e in clean:
        k = e['k']
        t = e['t'] * 1000  # ms

        if e['a'] == 'p':
            if last_p is not None:
                latencies.append(t - last_p)
            p_times[k] = t
            last_p = t

        elif e['a'] == 'r':
            if k in p_times:
                hold_times.append(t - p_times[k])
                if last_p is not None:
                    digraphs.append(t - last_p)

            if last_r is not None:
                releases.append(t - last_r)
            last_r = t

    duration_min = ((events[-1]['t'] - events[0]['t']) / 60)
    cpm = len(events) / duration_min if duration_min > 0 else 0

    features = [
        cpm,
        backspaces,
        np.mean(hold_times), np.max(hold_times), np.min(hold_times),
        np.mean(latencies) if latencies else 0, np.max(latencies) if latencies else 0, np.min(latencies) if latencies else 0,
        np.mean(digraphs) if digraphs else 0, np.max(digraphs) if digraphs else 0, np.min(digraphs) if digraphs else 0,
        np.mean(releases) if releases else 0, np.max(releases) if releases else 0, np.min(releases) if releases else 0
    ]

    return np.round(features, 4)
