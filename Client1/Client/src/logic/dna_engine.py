import numpy as np

def extract_dna_features(events):
    """
    Extracted 14-Feature Advanced Biometric Model.
    Units: Milliseconds (ms)
    Features: [CPM, Backspaces, Hold(Mean, Max, Min), Latency(Mean, Max, Min), 
               Digraph(Mean, Max, Min), Release(Mean, Max, Min)]
    """
    if not events or len(events) < 10:
        return None

    # 1. Behavioral Metadata (Error correction)
    backspaces = len([e for e in events if e['k'] == 'BackSpace' and e['a'] == 'p'])
    
    # Filter for rhythm analysis (exclude control keys to keep timing pure)
    clean = [e for e in events if e['k'] not in ['Return', 'BackSpace', 'Shift_L', 'Shift_R']]
    if len(clean) < 6: 
        return None

    hold_times, latencies, digraphs, releases = [], [], [], []
    p_times = {}
    last_p = last_r = None

    for e in clean:
        k = e['k']
        t = e['t'] * 1000  # Convert to ms for higher precision

        if e['a'] == 'p':
            if last_p is not None:
                latencies.append(t - last_p)
            p_times[k] = t
            last_p = t

        elif e['a'] == 'r':
            if k in p_times:
                hold = t - p_times[k]
                hold_times.append(hold)
                if last_p is not None:
                    # Digraph: P(n) to R(n+1)
                    digraphs.append(t - last_p)
            
            if last_r is not None:
                releases.append(t - last_r)
            last_r = t

    # 2. Typing Speed (Characters Per Minute)
    # Total session duration in minutes
    duration_min = ((events[-1]['t'] - events[0]['t']) / 60)
    cpm = len(events) / duration_min if duration_min > 0 else 0

    # 3. Vector Assembly
    try:
        features = [
            float(cpm), 
            float(backspaces),
            np.mean(hold_times), np.max(hold_times), np.min(hold_times),
            np.mean(latencies) if latencies else 0, np.max(latencies) if latencies else 0, np.min(latencies) if latencies else 0,
            np.mean(digraphs) if digraphs else 0, np.max(digraphs) if digraphs else 0, np.min(digraphs) if digraphs else 0,
            np.mean(releases) if releases else 0, np.max(releases) if releases else 0, np.min(releases) if releases else 0
        ]
        # Return as a clean list of floats rounded to 4 decimals
        return [float(round(x, 4)) for x in features]
    except Exception:
        return None