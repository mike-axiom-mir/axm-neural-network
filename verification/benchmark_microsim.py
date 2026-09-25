"""Measure complete numeric transitions including their evidence packets."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import time
import tracemalloc

from axm_neural_network.microsim import DynamicsRules, MicroDynamics


def run(sim, batch_size, total):
    count = 0
    for offset in range(0,total//sim.rules.horizon,batch_size):
        size = min(batch_size,total//sim.rules.horizon-offset)
        states = [sim.reset(10000+offset+j) for j in range(size)]
        for step in range(sim.rules.horizon):
            actions = [((step*7+j*3)%19-9)/10 for j in range(size)]
            results = sim.step_many(states,actions)
            states = [item['state'] for item in results]
            count += size
    if count != total: raise AssertionError('transition count mismatch')


def measure():
    import numpy
    rows = []
    for backend in ('python','numpy'):
        for batch_size in (1,32,128):
            sim = MicroDynamics(DynamicsRules(horizon=16),backend=backend)
            elapsed, cpus = [],[]
            for _ in range(3):
                wall,cpu = time.perf_counter(),time.process_time()
                run(sim,batch_size,2048)
                elapsed.append(time.perf_counter()-wall)
                cpus.append(time.process_time()-cpu)
            # Separate allocation sample, excluded from the timing comparison.
            tracemalloc.start()
            run(sim,batch_size,2048)
            _,peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            rows.append({'backend':backend,'batch_size':batch_size,'transitions_per_trial':2048,
                         'episodes_per_trial':128,'steps_per_episode':16,
                         'wall_seconds_trials':elapsed,'cpu_seconds_trials':cpus,
                         'median_transitions_per_second':2048/statistics.median(elapsed),
                         'peak_traced_python_bytes_separate_trial':peak,
                         'bytes_written_by_simulator':0})
    return {'schema':'axm.micro-throughput/v1','python':platform.python_version(),
            'numpy':numpy.__version__,'platform':platform.platform(),'rows':rows,
            'unit':'One two-value tanh state transition, including reset amortization, validation and hashed experience packet.',
            'limits':['No rendering, learner update, external I/O, GPU or physical-world simulation.',
                      'Allocation sample measures Python allocations, not total process RAM or VRAM.',
                      'Local timings vary with host load; batching is measured, not assumed faster.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=measure()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps([{'backend':r['backend'],'batch':r['batch_size'],'transitions_per_second':r['median_transitions_per_second']} for r in data['rows']],indent=2))
