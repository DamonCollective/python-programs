import subprocess
import time
import statistics
import argparse
from datetime import datetime

HOSTS = ['8.8.8.8', '1.1.1.1']
INTERVAL = 5  # seconds between rounds


def ping_host(host):
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '2000', host],
            capture_output=True, text=True, timeout=5
        )
        out = result.stdout
        if 'TTL=' in out or 'ttl=' in out:
            for part in out.split():
                if part.lower().startswith('time='):
                    val = part.split('=')[1].replace('ms', '').strip()
                    return float(val)
                if part.lower().startswith('time<'):
                    return 1.0  # < 1ms
            return 0.0
        return None
    except Exception:
        return None


def quality_label(ms):
    if ms is None:
        return 'FAIL'
    if ms < 20:
        return 'excellent'
    if ms < 50:
        return 'good'
    if ms < 100:
        return 'fair'
    if ms < 200:
        return 'poor'
    return 'bad'


def run(count):
    latencies = {h: [] for h in HOSTS}
    losses = {h: 0 for h in HOSTS}
    totals = {h: 0 for h in HOSTS}
    events = []

    print(f"\nInternet Quality Monitor  [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print(f"Hosts: {', '.join(HOSTS)}  |  Interval: {INTERVAL}s  |  Rounds: {'inf' if count is None else count}")
    print("-" * 70)

    i = 0
    try:
        while count is None or i < count:
            ts = datetime.now().strftime('%H:%M:%S')
            parts = [ts]
            any_fail = False
            for host in HOSTS:
                totals[host] += 1
                ms = ping_host(host)
                if ms is None:
                    losses[host] += 1
                    parts.append(f"  {host}: TIMEOUT")
                    any_fail = True
                else:
                    latencies[host].append(ms)
                    label = quality_label(ms)
                    parts.append(f"  {host}: {ms:>5.0f}ms ({label})")
            line = ' |'.join(parts)
            if any_fail:
                line = '*** ' + line
                events.append(f"{ts}  packet loss detected")
            print(line)
            i += 1
            if count is None or i < count:
                time.sleep(INTERVAL)
    except KeyboardInterrupt:
        pass

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for host in HOSTS:
        total = totals[host]
        if total == 0:
            continue
        loss_pct = losses[host] / total * 100
        lats = latencies[host]
        if lats:
            avg = statistics.mean(lats)
            mn = min(lats)
            mx = max(lats)
            jitter = statistics.stdev(lats) if len(lats) > 1 else 0
            print(f"{host}:  avg={avg:.0f}ms  min={mn:.0f}ms  max={mx:.0f}ms  jitter={jitter:.0f}ms  loss={loss_pct:.0f}%  [{quality_label(avg)}]")
        else:
            print(f"{host}:  100% packet loss")
    if events:
        print(f"\nEvents ({len(events)}):")
        for e in events:
            print(f"  {e}")
    else:
        print("\nNo packet loss events detected.")
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor internet quality')
    parser.add_argument('-n', '--count', type=int, default=None,
                        help='Number of rounds (default: run forever, Ctrl+C to stop)')
    parser.add_argument('-i', '--interval', type=int, default=None,
                        help=f'Seconds between rounds (default: {INTERVAL})')
    args = parser.parse_args()
    if args.interval:
        INTERVAL = args.interval
    run(args.count)
