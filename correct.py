'''Correction methods'''
import shutil
from functools import partial
import logging

import pandas as pd
import anndata as ad
from harmonypy import run_harmony
import numpy as np
import scanpy as sc
from scvi.model import SCVI

from quality_control.io import merge_parquet, split_parquet
import scib
from zca import ZCA, ZCA_corr

logger = logging.getLogger(__name__)


def log_uniform_sampling(min_=-6, max_=-1, size=25, seed=[6, 12, 2022]):
    rng = np.random.default_rng(seed)
    return 10.**rng.uniform(min_, max_, size=size)


def sphering(dframe_path, mode, lambda_, column_norm, values_norm,
             sphered_path, spherer_path):
    if mode == 'corr':
        spherer = ZCA_corr(regularization=lambda_)
    elif mode == 'cov':
        spherer = ZCA(regularization=lambda_)
    else:
        raise ValueError(f'mode should be "corr" or "cov"')

    meta, vals, features = split_parquet(dframe_path)
    train_ix = meta[column_norm].isin(values_norm).values
    spherer.fit(vals[train_ix])
    vals = spherer.transform(vals).astype(np.float32)
    merge_parquet(meta, vals, features, sphered_path)
    np.savez_compressed(spherer_path, spherer=spherer)


def select_best(map_files, parquet_files, best_path):
    scores = pd.Series()
    for map_file, parquet_file in zip(map_files, parquet_files):
        mean_map = pd.read_parquet(map_file)['mean_average_precision'].mean()
        scores[parquet_file] = mean_map

    best_parquet = scores.sort_values().index[-1]
    shutil.copy(str(best_parquet), best_path)


def harmony(adata: ad.AnnData, batch_key: str | list[str],
            corrected_embed: str):
    '''Harmony correction'''
    n_latent = min(adata.shape) - 1  # required for arpack
    logger.info('Computing PCA...')
    sc.tl.pca(adata, n_comps=n_latent)  # Generates X_pca
    logger.info('Computing PCA Done.')
    harmony_out = run_harmony(adata.obsm['X_pca'],
                              adata.obs,
                              batch_key,
                              max_iter_harmony=20,
                              nclust=300)  # Number of compounds

    adata.obsm[corrected_embed] = harmony_out.Z_corr.T


def mnn(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    '''Mutual nearest neighbor correction'''
    adatas = []
    for _, group in adata.obs.groupby(batch_key):
        adatas.append(adata[group.index].copy())
    corrected = sc.external.pp.mnn_correct(*adatas,
                                           batch_key=batch_key,
                                           do_concatenate=True)[0]
    adata.obsm[corrected_embed] = corrected.X


def scanorama(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    '''Scanorama correction'''
    n_latent = min(adata.shape) - 1  # required for arpack
    sc.tl.pca(adata, n_comps=n_latent)  # required for arpack
    sc.external.pp.scanorama_integrate(adata,
                                       batch_key,
                                       adjusted_basis=corrected_embed)


def combat(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    '''Combat correction'''
    adata.obsm[corrected_embed] = sc.pp.combat(adata,
                                               key=batch_key,
                                               inplace=False)


def desc(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    '''DESC correction'''
    adata_corrected = scib.integration.desc(adata, batch_key)
    adata.obsm[corrected_embed] = adata_corrected.obsm['X_emb']


def scvi(adata: ad.AnnData, batch_key: str, corrected_embed: str,
         label_key: str):
    '''scVI correction'''
    n_latent = 30
    train_adata = adata.copy()
    min_value = train_adata.X.min()
    train_adata.X -= min_value

    SCVI.setup_anndata(train_adata, batch_key=batch_key, labels_key=label_key)
    vae = SCVI(train_adata, n_layers=2, n_latent=n_latent)
    vae.view_anndata_setup(adata=train_adata)
    vae.train()

    adata.obsm[corrected_embed] = vae.get_latent_representation()


def identity(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    adata.obsm[corrected_embed] = adata.X


def trvaep(adata: ad.AnnData, batch_key: str, corrected_embed: str):
    adata_int = adata.copy()
    adata_int.X = adata_int.X.astype('float32')
    adata_int = scib.integration.trvaep(adata_int, batch_key)
    adata.obsm[corrected_embed] = adata_int.X  # obsm['X_emb']


def get_method_map(batch_key: str, label_key: str) -> dict[str, partial]:
    '''Create a map of callable objects identified by method name'''
    correction_map = {
        'harmony': partial(harmony, batch_key=batch_key),
        'mnn': partial(mnn, batch_key=batch_key),
        'scanorama': partial(scanorama, batch_key=batch_key),
        'combat': partial(combat, batch_key=batch_key),
        'desc': partial(desc, batch_key=batch_key),
        'sphering': partial(identity, batch_key=batch_key),
        'scvi': partial(scvi, batch_key=batch_key, label_key=label_key),
    }
    return correction_map
