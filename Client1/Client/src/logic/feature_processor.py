import numpy as np

def calculate_keystroke_dna(events):
    """
    Extracts 14 specific biometric features in Milliseconds (ms).
    """
    # 1. Capture Behavioral Metadata
    backspaces = len([e for e in events if e['k'] == 'BackSpace' and e['a'] == 'p'])
    
    # Filter for timing data (exclude control keys)
    clean = [e for e in events if e['k'] not in ['Return', 'BackSpace']]
    if len(clean) < 6: return None

    # 2. Timing Accumulators
    hold_times = []
    latencies = []    # P(n) to P(n+1)
    digraphs = []     # P(n) to R(n+1)
    releases = []     # R(n) to R(n+1)
    
    p_times = {} 
    last_p = last_r = None

    # Process events in ms
    for e in clean:
        k, t = e['k'], e['t'] * 1000 
        
        if e['a'] == 'p':
            if last_p is not None: latencies.append(t - last_p)
            p_times[k] = t
            last_p = t
        else:
            if k in p_times:
                hold = t - p_times[k]
                hold_times.append(hold)
                if last_p is not None: digraphs.append(t - last_p)
            if last_r is not None: releases.append(t - last_r)
            last_r = t

    # 3. Typing Speed (CPM)
    duration_min = ((clean[-1]['t'] - clean[0]['t']) / 60)
    cpm = len(clean) / duration_min if duration_min > 0 else 0

    # 4. Final 14-Feature Vector
    return [
        cpm, np.float64(backspaces),
        np.mean(hold_times), np.max(hold_times), np.min(hold_times),
        np.mean(latencies) if latencies else 0, np.max(latencies) if latencies else 0, np.min(latencies) if latencies else 0,
        np.mean(digraphs) if digraphs else 0, np.max(digraphs) if digraphs else 0, np.min(digraphs) if digraphs else 0,
        np.mean(releases) if releases else 0, np.max(releases) if releases else 0, np.min(releases) if releases else 0
    ]