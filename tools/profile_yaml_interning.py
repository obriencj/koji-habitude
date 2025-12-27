#!/usr/bin/env python3

"""
koji-habitude - YAML Interning Profiler

Standalone utility to profile YAML loading performance and memory usage
with and without string interning enabled.

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

# Import the loader module to access YAML_INTERNING
from koji_habitude.loader import load_yaml_files


def format_bytes(bytes_val: int) -> str:
    """
    Format bytes as human-readable string.
    """

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def profile_load(
        paths: List[str],
        interning: bool,
        recursive: bool) -> Tuple[float, int, int]:
    """
    Load a YAML dataset and measure time and memory usage.

    :param paths: List of paths to YAML files or directories
    :param interning: Whether to enable string interning
    :param recursive: Whether to recursively load from directories
    :returns: Tuple of (load_time_seconds, memory_delta_bytes, peak_memory_bytes)
    """

    # Set YAML_INTERNING before loading
    from koji_habitude import loader
    original_value = loader.ENABLE_INTERNING
    loader.ENABLE_INTERNING = interning

    # Get current process for memory measurement
    process = psutil.Process(os.getpid())

    try:
        # Measure memory before loading
        gc.collect()  # Clean up before measurement
        start_mem = process.memory_info().rss
        start_time = time.perf_counter()

        # Load all documents into memory
        documents = list(load_yaml_files(paths, recursive=recursive))

        # Measure memory and time after loading
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss

        load_time = end_time - start_time
        memory_delta = end_mem - start_mem
        peak_memory = end_mem  # Peak is the memory after loading

        # Explicitly delete and force garbage collection
        del documents
        gc.collect()

        return (load_time, memory_delta, peak_memory)

    finally:
        # Restore original YAML_INTERNING value
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
    help="Number of times to load the dataset (default: 1)")
@click.option(
    '--recursive', '-r',
    is_flag=True,
    default=False,
    help="Recursively load YAML files from directories")
def main(paths: List[str], interning: bool, iterations: int, recursive: bool):
    """
    Profile YAML loading performance and memory usage.

    This utility loads a YAML dataset multiple times and measures the
    time and memory usage for each load. Use this to compare the memory
    benefits of string interning for large YAML datasets.

    The dataset can be a single YAML file or a directory containing
    YAML files.
    """

    results: List[Tuple[float, int, int]] = []

    click.echo(f"Profiling YAML loading with interning={'enabled' if interning else 'disabled'}")
    click.echo(f"Paths: {paths}")
    click.echo(f"Iterations: {iterations}")
    click.echo(f"Recursive: {recursive}")
    click.echo()

    # Run profiling iterations
    for i in range(iterations):
        click.echo(f"Iteration {i + 1}/{iterations}...", nl=False)
        load_time, memory_delta, peak_memory = profile_load(
            paths, interning, recursive)
        results.append((load_time, memory_delta, peak_memory))
        click.echo(f" done ({load_time:.3f}s, {format_bytes(memory_delta)})")

    click.echo()
    click.echo("Results:")
    click.echo("-" * 80)
    click.echo(f"{'Iteration':<12} {'Time (s)':<12} {'Memory Delta':<20} {'Peak Memory':<20}")
    click.echo("-" * 80)

    times = []
    memory_deltas = []
    peak_memories = []

    for i, (load_time, memory_delta, peak_memory) in enumerate(results, 1):
        times.append(load_time)
        memory_deltas.append(memory_delta)
        peak_memories.append(peak_memory)
        click.echo(
            f"{i:<12} {load_time:<12.3f} {format_bytes(memory_delta):<20} {format_bytes(peak_memory):<20}")

    click.echo("-" * 80)

    # Summary statistics
    if iterations > 1:
        click.echo()
        click.echo("Summary Statistics:")
        click.echo("-" * 80)
        click.echo(f"{'Metric':<20} {'Min':<20} {'Max':<20} {'Avg':<20} {'Total':<20}")
        click.echo("-" * 80)

        min_time = min(times)
        max_time = max(times)
        avg_time = sum(times) / len(times)
        total_time = sum(times)

        min_mem = min(memory_deltas)
        max_mem = max(memory_deltas)
        avg_mem = sum(memory_deltas) / len(memory_deltas)
        total_mem = sum(memory_deltas)

        min_peak = min(peak_memories)
        max_peak = max(peak_memories)
        avg_peak = sum(peak_memories) / len(peak_memories)

        click.echo(
            f"{'Time (s)':<20} {min_time:<20.3f} {max_time:<20.3f} {avg_time:<20.3f} {total_time:<20.3f}")
        click.echo(
            f"{'Memory Delta':<20} {format_bytes(min_mem):<20} {format_bytes(max_mem):<20} "
            f"{format_bytes(avg_mem):<20} {format_bytes(total_mem):<20}")
        click.echo(
            f"{'Peak Memory':<20} {format_bytes(min_peak):<20} {format_bytes(max_peak):<20} "
            f"{format_bytes(avg_peak):<20} {'N/A':<20}")
        click.echo("-" * 80)


if __name__ == '__main__':
    main()


# The end.
