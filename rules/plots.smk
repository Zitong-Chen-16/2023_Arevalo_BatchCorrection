rule tidy_scores:
    input:
        metrics_files=expand(metrics_pattern, workflow=WORKFLOWS, method=METHODS)
        + expand(metrics_baseline_pattern, workflow=WORKFLOWS),
    output:
        "outputs/{scenario}/plots/tidy_scores.parquet",
    params:
        metrics_redlist=[
            "pcr",
            # "pcr_batch",
            # "il_f1",
            # "il_asw",
            "negcon_fraction_below_p",
            "negcon_fraction_below_corrected_p",
            "nonrep_fraction_below_p",
            "nonrep_fraction_below_corrected_p",
            # "lisi_label",
        ],
        methods_redlist=[],
    run:
        plot.figures.tidy_scores(
            input.metrics_files, params.metrics_redlist, params.methods_redlist, *output
        )


rule pivot_scores:
    input:
        "outputs/{scenario}/plots/tidy_scores.parquet",
    output:
        "outputs/{scenario}/plots/pivot_scores.parquet",
    run:
        plot.figures.pivot_scores(*input, *output)


rule results_table:
    input:
        "outputs/{scenario}/plots/pivot_scores.parquet",
    output:
        "outputs/{scenario}/plots/results_table.{ext}",
    run:
        plot.figures.results_table(*input, *output)


rule cartesian_plane:
    input:
        "outputs/{scenario}/plots/tidy_scores.parquet",
    output:
        "outputs/{scenario}/plots/cartesian.{ext}",
    params:
        min_cvar=0.01,
    run:
        plot.figures.cartesian_plane(*input, *params, *output)


rule barplot_all_metrics:
    input:
        "outputs/{scenario}/plots/tidy_scores.parquet",
    output:
        "outputs/{scenario}/plots/all_metrics_barplot.{ext}",
    run:
        plot.figures.barplot_all_metrics(*input, *output)


rule barplot_map_scores:
    input:
        "outputs/{scenario}/plots/tidy_scores.parquet",
    output:
        "outputs/{scenario}/plots/map_scores_barplot.{ext}",
    run:
        plot.figures.barplot_map_scores(*input, *output)


rule hbarplot_all_metrics:
    input:
        "outputs/{scenario}/plots/pivot_scores.parquet",
    output:
        "outputs/{scenario}/plots/mean_all_metrics_hbarplot.{ext}",
    run:
        plot.figures.hbarplot_all_metrics(*input, *output)


rule prepare_embeddings:
    input:
        embd_files=expand(umap_pattern, workflow=WORKFLOWS, method=METHODS)
        + expand(umap_baseline_pattern, workflow=WORKFLOWS),
    output:
        "outputs/{scenario}/plots/embeddings.parquet",
    run:
        plot.figures.prepare_embeddings(input.embd_files, *output)


rule umap_batch:
    input:
        "outputs/{scenario}/plots/embeddings.parquet",
        "outputs/{scenario}/plots/pivot_scores.parquet",
    output:
        "outputs/{scenario}/plots/umap_batch.{ext}",
    run:
        plot.figures.umap_batch(*input, *output)


rule umap_source:
    input:
        "outputs/{scenario}/plots/embeddings.parquet",
        "outputs/{scenario}/plots/pivot_scores.parquet",
    output:
        "outputs/{scenario}/plots/umap_source.{ext}",
    run:
        plot.figures.umap_source(*input, *output)
