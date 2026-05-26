import json
import math
import argparse
import os
import random
import csv
from collections import defaultdict

# Delivery simulator for FastBox

def euclidean(a, b):
    """Return Euclidean distance between two 2D points a and b."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def load_data(path):
    """Load simulation input JSON from path."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assign_packages(data):
    """(Legacy) Assign each package to the nearest agent (agent -> warehouse distance).

    Returns a mapping agent_id -> list of package dicts.
    """
    agents = data['agents']
    warehouses = data['warehouses']
    assignments = defaultdict(list)

    for pkg in data['packages']:
        wh = warehouses[pkg['warehouse']]
        # find nearest agent to warehouse
        nearest = None
        best_dist = float('inf')
        for aid, apos in agents.items():
            d = euclidean(apos, wh)
            if d < best_dist:
                best_dist = d
                nearest = aid
        assignments[nearest].append(pkg)

    return assignments


def simulate(assignments, data):
    """Simulate deliveries and compute total distance per agent.

    For each agent: start at agent position, go to the package's warehouse,
    then to the destination; continue from the last delivery location.
    """
    agents = data['agents']
    warehouses = data['warehouses']

    report = {}

    for aid, pkgs in assignments.items():
        current_pos = agents[aid][:]  # start at agent location
        total_dist = 0.0
        delivered = 0

        for pkg in pkgs:
            wh_pos = warehouses[pkg['warehouse']]
            dest = pkg['destination']

            # travel to warehouse
            d1 = euclidean(current_pos, wh_pos)
            # travel from warehouse to destination
            d2 = euclidean(wh_pos, dest)

            total_dist += d1 + d2
            delivered += 1

            # agent ends up at the delivery destination
            current_pos = dest

        avg = round(total_dist / delivered, 2) if delivered else 0.0

        report[aid] = {
            'packages_delivered': delivered,
            'total_distance': round(total_dist, 2),
            'efficiency': avg
        }

    return report


def simulate_dynamic(data, mid_join=None, max_delay=0.0, ascii_routes=False):
    """Process packages sequentially, allowing mid-day agent joins and random delays.

    mid_join: tuple (agent_id, x, y, after_n) or None
    max_delay: maximum random delay (in minutes) added per delivery
    ascii_routes: if True, produce a text file describing routes
    """
    agents = {aid: list(pos) for aid, pos in data['agents'].items()}  # mutable positions
    warehouses = data['warehouses']

    stats = {aid: {'packages_delivered': 0, 'total_distance': 0.0, 'total_delay': 0.0, 'route': []}
             for aid in agents}

    mid_added = False
    processed = 0

    for pkg in data['packages']:
        # check mid-join
        if mid_join and (not mid_added) and processed >= mid_join[3]:
            # add new agent
            aid_new, x_new, y_new, _ = mid_join
            agents[aid_new] = [x_new, y_new]
            stats[aid_new] = {'packages_delivered': 0, 'total_distance': 0.0, 'total_delay': 0.0, 'route': []}
            mid_added = True

        wh_pos = warehouses[pkg['warehouse']]

        # find nearest active agent to warehouse
        nearest = None
        best_dist = float('inf')
        for aid, apos in agents.items():
            d = euclidean(apos, wh_pos)
            if d < best_dist:
                best_dist = d
                nearest = aid

        # travel distances
        d1 = euclidean(agents[nearest], wh_pos)
        d2 = euclidean(wh_pos, pkg['destination'])
        stats[nearest]['total_distance'] += d1 + d2
        stats[nearest]['packages_delivered'] += 1

        # random delay
        if max_delay > 0:
            delay = random.uniform(0, max_delay)
            stats[nearest]['total_delay'] += delay
        else:
            delay = 0.0

        # record route step
        stats[nearest]['route'].append((list(agents[nearest]), wh_pos, pkg['destination'], round(d1, 2), round(d2, 2), round(delay, 2)))

        # update agent position to destination
        agents[nearest] = list(pkg['destination'])

        processed += 1

    # build report
    report = {}
    for aid, s in stats.items():
        delivered = s['packages_delivered']
        total_dist = round(s['total_distance'], 2)
        total_delay = round(s['total_delay'], 2)
        efficiency = round(total_dist / delivered, 2) if delivered else 0.0
        report[aid] = {
            'packages_delivered': delivered,
            'total_distance': total_dist,
            'efficiency': efficiency,
            'total_delay': total_delay
        }

    # pick best agent by lowest efficiency
    best = pick_best_agent(report)
    report['best_agent'] = best

    # optional ASCII routes
    if ascii_routes:
        base = 'report_routes'
        with open(f'{base}.txt', 'w', encoding='utf-8') as f:
            for aid, s in stats.items():
                f.write(f'Agent {aid}:\n')
                for step in s['route']:
                    start, wh, dest, d1, d2, delay = step
                    f.write(f'  Start {start} -> Warehouse {wh} (d={d1}) -> Dest {dest} (d={d2}) Delay={delay}\n')
                f.write('\n')

    # return both report and full stats (including routes) for plotting/export
    return report, stats


def pick_best_agent(report):
    """Choose the best agent based on lowest average distance per package (efficiency).

    If an agent delivered zero packages, they are ignored for best-agent selection.
    """
    best = None
    best_val = float('inf')
    for aid, stats in report.items():
        if stats['packages_delivered'] == 0:
            continue
        if stats['efficiency'] < best_val:
            best_val = stats['efficiency']
            best = aid
    return best


def plot_routes(stats, out_path):
    """Plot routes from stats dict and save PNG to out_path."""
    try:
        import matplotlib.pyplot as plt
    except Exception:
        raise SystemExit('Matplotlib is required for plotting. Install with: pip install matplotlib')

    plt.figure(figsize=(8, 8))

    # assign a color to each agent
    colors = {}
    cmap = plt.get_cmap('tab10')
    for i, aid in enumerate(stats.keys()):
        colors[aid] = cmap(i % 10)

    # plot each agent's steps
    for aid, s in stats.items():
        route = s.get('route', [])
        xs = []
        ys = []
        for step in route:
            start, wh, dest, d1, d2, delay = step
            # start -> warehouse -> dest
            xs.extend([start[0], wh[0], dest[0]])
            ys.extend([start[1], wh[1], dest[1]])

        if xs:
            plt.plot(xs, ys, '-o', color=colors[aid], label=f'{aid} ({s.get("packages_delivered",0)})')

    plt.title('Agent Routes')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.grid(True)
    plt.savefig(out_path)
    plt.close()


def save_report(report, path):
    """Save the simulation report to path in JSON format."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description='FastBox delivery simulator')
    parser.add_argument('input', nargs='?', default='data.json', help='Input JSON file')
    parser.add_argument('-o', '--output', help='Output report JSON file')
    parser.add_argument('--random-delays', type=float, default=0.0,
                        help='Enable random delays (max minutes) added per delivery')
    parser.add_argument('--ascii-routes', action='store_true', help='Generate ASCII route file')
    parser.add_argument('--plot', action='store_true', help='Generate PNG route plot')
    parser.add_argument('--mid-join', type=str,
                        help='Add new agent mid-day using format AGENT:X,Y:AFTER where AFTER is number of processed packages')
    parser.add_argument('--export-csv', type=str, help='Export top performer to CSV file path')
    args = parser.parse_args()

    data = load_data(args.input)

    # If any bonus features requested, run dynamic simulator
    if args.random_delays > 0.0 or args.ascii_routes or args.mid_join or args.plot:
        mid = None
        if args.mid_join:
            # expected format: AGENT:X,Y:AFTER  e.g. A5:50,50:3
            try:
                parts = args.mid_join.split(':')
                aid = parts[0]
                xy = parts[1].split(',')
                x = float(xy[0]); y = float(xy[1])
                after = int(parts[2])
                mid = (aid, x, y, after)
            except Exception as e:
                raise SystemExit(f'Invalid --mid-join format: {e}')

        report, stats = simulate_dynamic(data, mid_join=mid, max_delay=args.random_delays, ascii_routes=args.ascii_routes)

        # Sanity check: total delivered equals total packages (sum over agents)
        total_delivered = sum(v['packages_delivered'] for k, v in report.items() if k != 'best_agent')
        assert total_delivered == len(data['packages']), "Delivered count mismatch"
    else:
        # assign packages to nearest agents
        assignments = assign_packages(data)

        # simulate deliveries
        report = simulate(assignments, data)

        # determine best agent
        best = pick_best_agent(report)
        report['best_agent'] = best

        # Sanity check: total delivered equals total packages
        total_delivered = sum(v['packages_delivered'] for v in report.values() if isinstance(v, dict))
        assert total_delivered == len(data['packages']), "Delivered count mismatch"

        # if user requested plotting but no dynamic flags, run dynamic to get per-step stats
        stats = None
        if args.plot:
            # run dynamic to obtain route-level stats (no delays unless requested)
            _, stats = simulate_dynamic(data, mid_join=None, max_delay=0.0, ascii_routes=False)

    # determine output path
    if args.output:
        out_path = args.output
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_path = f'report_{base}.json'

    save_report(report, out_path)
    print(f'Simulation complete. Report written to {out_path}')

    # export top performer to CSV if requested
    if args.export_csv:
        best = report.get('best_agent')
        if best:
            stats = report[best]
            with open(args.export_csv, 'w', newline='', encoding='utf-8') as csvf:
                writer = csv.writer(csvf)
                writer.writerow(['agent', 'packages_delivered', 'total_distance', 'efficiency', 'total_delay'])
                writer.writerow([best, stats.get('packages_delivered', 0), stats.get('total_distance', 0), stats.get('efficiency', 0), stats.get('total_delay', 0)])
            print(f'Top performer {best} exported to {args.export_csv}')
        else:
            print('No best agent to export')

    # plotting if requested
    if args.plot:
        # stats should be available when dynamic path used; else we generated stats above
        try:
            if 'stats' not in locals() or stats is None:
                _, stats = simulate_dynamic(data, mid_join=None, max_delay=args.random_delays, ascii_routes=False)
            out_png = os.path.splitext(out_path)[0] + '.png'
            plot_routes(stats, out_png)
            print(f'Route plot saved to {out_png}')
        except Exception as e:
            print(f'Plotting failed: {e}')


if __name__ == '__main__':
    main()
