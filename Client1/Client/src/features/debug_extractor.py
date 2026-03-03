import json
import os

def debug_extract(user_id):
    raw_path = f'data/raw/{user_id}_raw.json'
    if not os.path.exists(raw_path):
        print(f"❌ Error: {raw_path} not found.")
        return

    with open(raw_path, 'r') as f:
        samples = json.load(f)

    print(f"--- Debugging Timings for: {user_id} ---")
    
    for i, sample in enumerate(samples[:1]): # Let's look at the first sample
        print(f"\nSample {i+1}:")
        sample = sorted(sample, key=lambda x: x['t'])
        presses = {}
        r_hist, p_hist = [], []

        for e in sample:
            k, t, a = e['k'], e['t'], e['a']
            if a == 'p':
                if p_hist:
                    dd = t - p_hist[-1]
                    if dd > 1.0: print(f"  ⚠️ HIGH DD: {k} (after prev key) = {round(dd,4)}s")
                if r_hist:
                    fl = t - r_hist[-1]
                    if fl > 1.0: print(f"  ⚠️ HIGH FLIGHT: {k} = {round(fl,4)}s")
                presses[k] = t
                p_hist.append(t)
            elif a == 'r':
                if k in presses:
                    ho = t - presses[k]
                    print(f"  Key: {k} | Hold: {round(ho,4)}s")
                    if ho > 1.0: print(f"    🚨 ALERT: Key {k} held for > 1 second!")
                if r_hist:
                    uu = t - r_hist[-1]
                    if uu > 1.0: print(f"  ⚠️ HIGH UU: {k} = {round(uu,4)}s")
                r_hist.append(t)

if __name__ == "__main__":
    uid = input("Username to debug: ").strip()
    if uid: debug_extract(uid)