#!/usr/bin/env python3

"""
koji-habitude - Namespace Profiling

Standalone utility to profile memory usage when streaming YAML data into a
Namespace via feedall_raw, which creates pydantic objects and adds a second
layer of memory stress.

Author: Christopher O'Brien <obriencj@gmail.com>
License: GNU General Public License v3
AI-Assistant: Claude 4.5 Sonnet via Cursor
"""


import gc
import os
import time
from typing import List, Tuple

import click
import psutil

# Import the loader and namespace modules
from koji_habitude.loader import MultiLoader, YAMLLoader
from koji_habitude.namespace import Namespace


def format_bytes(bytes_val: int) -> str:
    """
    Format bytes as human-readable string.
    """

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def profile_namespace(
        paths: List[str],
        interning: bool,
        recursive: bool,
        expand: bool,
        enable_templates: bool) -> Tuple[float, float, int, int, int]:
    """
    Stream YAML data into a Namespace and measure time and memory usage.

    :param paths: List of paths to YAML files or directories
    :param interning: Whether to enable string interning
    :param recursive: Whether to recursively load from directories
    :param expand: Whether to call namespace.expand() after feeding
    :param enable_templates: Whether to enable templates in namespace
    :returns: Tuple of (feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand)
    """

    # Set ENABLE_INTERNING before loading
    from koji_habitude import loader
    original_value = loader.ENABLE_INTERNING
    loader.ENABLE_INTERNING = interning

    # Get current process for memory measurement
    process = psutil.Process(os.getpid())

    try:
        # Stage 1: Baseline
        gc.collect()
        mem_before = process.memory_info().rss

        # Stage 2: Stream into namespace (creates pydantic objects)
        namespace = Namespace(enable_templates=enable_templates)
        ml = MultiLoader([YAMLLoader])

        start_time = time.perf_counter()
        namespace.feedall_raw(ml.load(paths, recursive=recursive))
        feed_time = time.perf_counter() - start_time
        mem_after_feed = process.memory_info().rss

        # Stage 3: Expand (if enabled)
        expand_time = 0.0
        mem_after_expand = mem_after_feed
        if expand:
            start_time = time.perf_counter()
            namespace.expand()
            expand_time = time.perf_counter() - start_time
            mem_after_expand = process.memory_info().rss

        # Explicitly delete and force garbage collection
        del namespace
        gc.collect()

        return (feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand)

    finally:
        # Restore original ENABLE_INTERNING value
        loader.ENABLE_INTERNING = original_value


@click.command()
@click.argument('paths', nargs=-1, required=True)
@click.option(
    '--interning/--no-interning',
    default=True,
    help="Enable or disable YAML string interning (default: enabled)")
@click.option(
    '--iterations', '-n',
    default=1,
    type=int,
    help="Number of times to run the full pipeline (default: 1)")
@click.option(
    '--recursive', '-r',
    is_flag=True,
    default=False,
    help="Recursively load YAML files from directories")
@click.option(
    '--expand/--no-expand',
    default=True,
    help="Whether to call namespace.expand() after feeding (default: enabled)")
@click.option(
    '--enable-templates/--no-templates',
    default=True,
    help="Whether to enable templates in namespace (default: enabled)")
def main(
        paths: List[str],
        interning: bool,
        iterations: int,
        recursive: bool,
        expand: bool,
        enable_templates: bool):
    """
    Profile Namespace memory usage when streaming YAML data.

    This utility streams YAML data directly into a Namespace via feedall_raw,
    which creates pydantic objects from the streamed dictionaries. This adds
    a second layer of memory stress compared to just loading YAML files.

    The dataset can be a single YAML file or a directory containing
    YAML files.
    """

    results: List[Tuple[float, float, int, int, int]] = []

    click.echo(f"Profiling Namespace with interning={'enabled' if interning else 'disabled'}")
    click.echo(f"Paths: {paths}")
    click.echo(f"Iterations: {iterations}")
    click.echo(f"Recursive: {recursive}")
    click.echo(f"Expand: {expand}")
    click.echo(f"Enable templates: {enable_templates}")
    click.echo()

    # Run profiling iterations
    for i in range(iterations):
        click.echo(f"Iteration {i + 1}/{iterations}...", nl=False)
        feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand = profile_namespace(
            paths, interning, recursive, expand, enable_templates)
        results.append((feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand))
        feed_delta = mem_after_feed - mem_before
        click.echo(f" done (feed: {feed_time:.3f}s, {format_bytes(feed_delta)})")

    click.echo()
    click.echo("Results:")
    click.echo("-" * 100)
    if expand:
        click.echo(f"{'Iteration':<12} {'Feed Time':<12} {'Expand Time':<12} {'Mem Before':<20} {'Mem After Feed':<20} {'Mem After Expand':<20}")
    else:
        click.echo(f"{'Iteration':<12} {'Feed Time':<12} {'Expand Time':<12} {'Mem Before':<20} {'Mem After Feed':<20}")
    click.echo("-" * 100)

    feed_times = []
    expand_times = []
    mem_befores = []
    mem_after_feeds = []
    mem_after_expands = []

    for i, (feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand) in enumerate(results, 1):
        feed_times.append(feed_time)
        expand_times.append(expand_time)
        mem_befores.append(mem_before)
        mem_after_feeds.append(mem_after_feed)
        mem_after_expands.append(mem_after_expand)

        feed_delta = mem_after_feed - mem_before
        expand_delta = mem_after_expand - mem_after_feed if expand else 0
        total_delta = mem_after_expand - mem_before

        if expand:
            click.echo(
                f"{i:<12} {feed_time:<12.3f} {expand_time:<12.3f} "
                f"{format_bytes(mem_before):<20} {format_bytes(mem_after_feed):<20} "
                f"{format_bytes(mem_after_expand):<20}")
        else:
            click.echo(
                f"{i:<12} {feed_time:<12.3f} {'N/A':<12} "
                f"{format_bytes(mem_before):<20} {format_bytes(mem_after_feed):<20}")

    click.echo("-" * 100)

    # Memory deltas
    click.echo()
    click.echo("Memory Deltas:")
    click.echo("-" * 100)
    click.echo(f"{'Iteration':<12} {'Feed Delta':<20} {'Expand Delta':<20} {'Total Delta':<20}")
    click.echo("-" * 100)

    for i, (feed_time, expand_time, mem_before, mem_after_feed, mem_after_expand) in enumerate(results, 1):
        feed_delta = mem_after_feed - mem_before
        expand_delta = mem_after_expand - mem_after_feed if expand else 0
        total_delta = mem_after_expand - mem_before

        if expand:
            click.echo(
                f"{i:<12} {format_bytes(feed_delta):<20} {format_bytes(expand_delta):<20} "
                f"{format_bytes(total_delta):<20}")
        else:
            click.echo(
                f"{i:<12} {format_bytes(feed_delta):<20} {'N/A':<20} "
                f"{format_bytes(total_delta):<20}")

    click.echo("-" * 100)

    # Summary statistics
    if iterations > 1:
        click.echo()
        click.echo("Summary Statistics:")
        click.echo("-" * 100)
        click.echo(f"{'Metric':<20} {'Min':<20} {'Max':<20} {'Avg':<20} {'Total':<20}")
        click.echo("-" * 100)

        # Feed time statistics
        min_feed = min(feed_times)
        max_feed = max(feed_times)
        avg_feed = sum(feed_times) / len(feed_times)
        total_feed = sum(feed_times)
        click.echo(
            f"{'Feed Time (s)':<20} {min_feed:<20.3f} {max_feed:<20.3f} {avg_feed:<20.3f} {total_feed:<20.3f}")

        # Expand time statistics (if enabled)
        if expand:
            min_expand = min(expand_times)
            max_expand = max(expand_times)
            avg_expand = sum(expand_times) / len(expand_times)
            total_expand = sum(expand_times)
            click.echo(
                f"{'Expand Time (s)':<20} {min_expand:<20.3f} {max_expand:<20.3f} {avg_expand:<20.3f} {total_expand:<20.3f}")

        # Feed delta statistics
        feed_deltas = [mem_after_feed - mem_before for mem_before, mem_after_feed in zip(mem_befores, mem_after_feeds)]
        min_feed_delta = min(feed_deltas)
        max_feed_delta = max(feed_deltas)
        avg_feed_delta = sum(feed_deltas) / len(feed_deltas)
        total_feed_delta = sum(feed_deltas)
        click.echo(
            f"{'Feed Delta':<20} {format_bytes(min_feed_delta):<20} {format_bytes(max_feed_delta):<20} "
            f"{format_bytes(avg_feed_delta):<20} {format_bytes(total_feed_delta):<20}")

        # Expand delta statistics (if enabled)
        if expand:
            expand_deltas = [mem_after_expand - mem_after_feed for mem_after_feed, mem_after_expand in zip(mem_after_feeds, mem_after_expands)]
            min_expand_delta = min(expand_deltas)
            max_expand_delta = max(expand_deltas)
            avg_expand_delta = sum(expand_deltas) / len(expand_deltas)
            total_expand_delta = sum(expand_deltas)
            click.echo(
                f"{'Expand Delta':<20} {format_bytes(min_expand_delta):<20} {format_bytes(max_expand_delta):<20} "
                f"{format_bytes(avg_expand_delta):<20} {format_bytes(total_expand_delta):<20}")

        # Total delta statistics
        total_deltas = [mem_after_expand - mem_before for mem_before, mem_after_expand in zip(mem_befores, mem_after_expands)]
        min_total_delta = min(total_deltas)
        max_total_delta = max(total_deltas)
        avg_total_delta = sum(total_deltas) / len(total_deltas)
        total_total_delta = sum(total_deltas)
        click.echo(
            f"{'Total Delta':<20} {format_bytes(min_total_delta):<20} {format_bytes(max_total_delta):<20} "
            f"{format_bytes(avg_total_delta):<20} {format_bytes(total_total_delta):<20}")

        click.echo("-" * 100)


if __name__ == '__main__':
    main()


# The end.
