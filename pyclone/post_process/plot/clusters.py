'''
Created on Nov 30, 2015

@author: Andrew Roth
'''
import matplotlib.gridspec as gs
import matplotlib.pyplot as pp
import numpy as np
import pandas as pd
import seaborn as sb

import pyclone.post_process

from pyclone.post_process.plot import defaults
from pyclone.post_process.plot import utils
from pyclone.post_process.plot import scatter


def density_plot(
        config, trace, out_file, burnin=0, grid_size=101, max_clusters=None, min_cluster_size=0, samples=[], thin=1):

    df = pyclone.post_process.clusters.load_table(
        config,
        trace,
        burnin=burnin,
        grid_size=grid_size,
        max_clusters=max_clusters,
        min_size=min_cluster_size,
        thin=thin
    )

    sizes = df[['cluster', 'size']].drop_duplicates().set_index('cluster').to_dict()['size']

    if len(samples) == 0:
        samples = sorted(df['sample'].unique())

    else:
        df = df[df['sample'].isin(samples)]

    num_samples = len(samples)

    clusters = df['cluster'].unique()

    postions = list(range(1, len(clusters) + 1))

    utils.setup_plot()

    width = 8

    height = 2 * num_samples + 1

    fig = pp.figure(figsize=(width, height))

    grid = gs.GridSpec(nrows=num_samples, ncols=1)

    colors = utils.get_clusters_color_map(pd.Series(clusters))

    for ax_index, sample in enumerate(samples):
        plot_df = df[df['sample'] == sample]

        plot_df = plot_df.drop(['sample', 'size'], axis=1).set_index('cluster')

        ax = fig.add_subplot(grid[ax_index])

        utils.setup_axes(ax)

        ax.annotate(
            sample,
            xy=(1.01, 0.5),
            xycoords='axes fraction',
            fontsize=defaults.axis_label_font_size
        )

        for i, (cluster, log_pdf) in enumerate(plot_df.iterrows()):
            pos = postions[i]

            y = log_pdf.index.astype(float)

            x = np.exp(log_pdf)

            x = (x / x.max()) * 0.3

            ax.fill_betweenx(y, pos - x, pos + x, color=colors[cluster], where=(x > 1e-6))

        ax.set_xticks(postions)

        if ax_index == (num_samples - 1):
            x_tick_labels = ['{0} (n={1})'.format(x, sizes[x]) for x in clusters]

            ax.set_xticklabels(
                x_tick_labels,
                rotation=90
            )

            ax.set_xlabel(
                defaults.cluster_label,
                fontsize=defaults.axis_label_font_size
            )

        else:
            ax.set_xticklabels([])

        utils.set_tick_label_font_sizes(
            ax, defaults.tick_label_font_size
        )

        ax.set_ylim(
            defaults.cellular_prevalence_limits
        )

    if num_samples == 1:
        ax.set_ylabel(
            defaults.cellular_prevalence_label,
            fontsize=defaults.axis_label_font_size
        )

    else:
        fig.text(
            -0.01,
            0.5,
            defaults.cellular_prevalence_label,
            fontsize=defaults.axis_label_font_size,
            ha='center',
            rotation=90,
            va='center'
        )

    grid.tight_layout(fig)

    utils.save_figure(fig, out_file)


def parallel_coordinates_plot(
        config,
        trace,
        out_file,
        burnin=0,
        grid_size=101,
        max_clusters=100,
        min_cluster_size=0,
        samples=[],
        thin=1):

    utils.setup_plot()

    plot_df = pyclone.post_process.clusters.load_summary_table(
        config,
        trace,
        burnin=burnin,
        grid_size=grid_size,
        max_clusters=max_clusters,
        min_size=min_cluster_size,
        thin=thin
    )

    if len(samples) == 0:
        samples = sorted(plot_df['sample'].unique())

    else:
        plot_df = plot_df[plot_df['sample'].isin(samples)]

    clusters = sorted(plot_df['cluster'].unique())

    plot_df['sample_index'] = plot_df['sample'].apply(lambda x: samples.index(x))

    plot_df = plot_df.sort_values(by='sample_index')

    grid = sb.FacetGrid(
        plot_df,
        hue='cluster',
        hue_order=clusters,
        palette='husl'
    )

    grid.map(
        pp.errorbar,
        'sample_index',
        'mean',
        'std',
        marker=defaults.line_plot_marker,
        markersize=defaults.line_plot_marker_size
    )

    ax = grid.ax

    utils.setup_axes(ax)

    fig = grid.fig

    # Legend
    box = ax.get_position()

    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])

    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Cluster')

    # Axis formatting
    ax.set_xticks(sorted(plot_df['sample_index'].unique()))

    ax.set_xticklabels(samples)

    ax.set_xlabel(defaults.sample_label, fontsize=defaults.axis_label_font_size)

    ax.set_ylabel(defaults.cellular_prevalence_label, fontsize=defaults.axis_label_font_size)

    utils.set_tick_label_font_sizes(ax, defaults.tick_label_font_size)

    # Plot limits
    ax.set_xlim(
        plot_df['sample_index'].min() - 0.1,
        plot_df['sample_index'].max() + 0.1
    )

    ax.set_ylim(*defaults.cellular_prevalence_limits)

    # Resize and save figure
    fig.set_size_inches(*utils.get_parallel_coordinates_figure_size(samples))

    utils.save_figure(fig, out_file)


def scatter_plot(
        config,
        trace,
        plot_file,
        burnin=0,
        grid_size=101,
        max_clusters=None,
        min_cluster_size=0,
        samples=None,
        thin=1):

    utils.setup_plot()

    df = pyclone.post_process.clusters.load_summary_table(
        config,
        trace,
        burnin=burnin,
        grid_size=grid_size,
        max_clusters=max_clusters,
        min_size=min_cluster_size,
        thin=thin
    )

    mean_df = df.pivot(index='cluster', columns='sample', values='mean')

    error_df = df.pivot(index='cluster', columns='sample', values='std')

    if len(samples) == 0:
        samples = sorted(df['sample'].unique())

    color_map = utils.get_clusters_color_map(pd.Series(df['cluster']))

    scatter.plot_all_pairs(
        color_map,
        mean_df,
        plot_file,
        samples,
        error_df=error_df
    )
