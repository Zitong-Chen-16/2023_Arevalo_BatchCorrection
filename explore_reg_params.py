'''
Explore lambda and epsilon for config.json setup
'''
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from run_correction import workflow as correction_workflow
from run_evaluation import METRICS_SET, workflow as evaluation_workflow
from utils import PathLocator


def explore_params(config_path: str, model: str, n_opts: int,
                   min_replicates_to_eval: int, output_path: str):
    '''Expore multiple params combinations for a given configuration'''
    template_file = Path(config_path)
    with template_file.open('r', encoding='utf8') as fin:
        config = json.load(fin)

    rng = np.random.default_rng([6, 12, 2022])
    for i in range(n_opts):
        # lambda_ = 10.**rng.uniform(-6, 1.)
        # epsilon_mad = 10.**rng.uniform(-4, 1.)
        epsilon_mad = 0.00029032327858896217
        lambda_ = 5.566152843198177e-06

        config['sphering_lambda'] = lambda_
        config['epsilon_mad'] = epsilon_mad
        with TemporaryDirectory() as tmpdir:
            filename = f'{tmpdir}/{template_file.stem}_{i:02d}.json'
            with open(filename, 'w', encoding='utf8') as fout:
                json.dump(config, fout)

            locator = PathLocator(filename, model, min_replicates_to_eval,
                                  output_path)
            correction_workflow(locator, vis='mde')
            evaluation_workflow(locator, METRICS_SET['FAST'])

def main():
    # explore_params('/dgx1nas1/storage/data/sam/codes/2023_Arevalo_BatchCorrection/inputs/conf/crispr.json', 'sphering', 15, 5, '/dgx1nas1/storage/data/sam/codes/2023_Arevalo_BatchCorrection/output/crispr_run4')
    explore_params('/dgx1nas1/storage/data/sam/codes/2023_Arevalo_BatchCorrection/inputs/conf/crispr_debug.json', 'sphering', 1, 5, '/dgx1nas1/storage/data/sam/codes/2023_Arevalo_BatchCorrection/output/no_sphering')

main()