import argparse
import os
import pathlib
import resource
import subprocess
import sys
import time
from abc import ABC, abstractmethod

import pkg_resources

import pathway as pw  # type:ignore
from pathway.stdlib.graphs.pagerank import pagerank  # type:ignore


def get_git_commit(path):
    try:
        git = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            cwd=path,
            text=True,
            check=True,
        )
        return git.stdout.strip()
    except Exception:
        return None


def display_path_and_version(name, path):
    sys.stderr.write(f"{name} path: {path}\n")
    parent = pathlib.Path(path).parent
    commit = get_git_commit(parent)
    if commit is not None:
        sys.stderr.write(f"{name} commit: {commit}\n")


def display_paths_and_versions():
    display_path_and_version("Benchmark code", __file__)
    display_path_and_version("Pathway", pw.__file__)
    display_path_and_version("Pathway engine", pw.engine.__file__)
    sys.stderr.write(f"Pathway package version: {pw.__version__}\n")


class Benchmark(ABC):
    def __init__(self, input_filename, *args, **kwargs):
        self._input_filename = input_filename

    @abstractmethod
    def run_benchmark(self): ...


class PagerankBenchmark(Benchmark):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pagerank_steps = kwargs.get("pagerank_steps", 5)

    def get_input_table(self):
        return pw.io.jsonlines.read(
            path=self._input_filename,
            mode="static",
            schema=pw.schema_builder(
                columns={
                    "u": pw.column_definition(dtype=int),
                    "v": pw.column_definition(dtype=int),
                }
            ),
            autocommit_duration_ms=None,
        )

    def run_benchmark(self):
        input_table = self.get_input_table()
        edges = input_table.select(
            u=input_table.pointer_from(pw.this.u),
            v=input_table.pointer_from(pw.this.v),
        )
        print("Launching pagerank with {} steps...".format(self.pagerank_steps))
        result = pagerank(edges, self.pagerank_steps)
        pw.io.null.write(result)
        pw.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pathway benchmarker")
    parser.add_argument("--input-filename", type=str)
    parser.add_argument("--pagerank-steps", type=int, default=5)
    args = parser.parse_args()

    display_paths_and_versions()

    benchmark = PagerankBenchmark(
        args.input_filename,
        pagerank_steps=args.pagerank_steps,
    )

    before = time.time()
    benchmark.run_benchmark()
    result = "runtime=pathway\tdataset=livejournal\tworkers={}\tsteps={}\ttime_elapsed={}\tmemory={}\n".format(
        os.environ.get("PATHWAY_THREADS", 1),
        args.pagerank_steps,
        time.time() - before,
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )

    try:
        version = pkg_resources.get_distribution("pathway").version
    except Exception:
        version = "UNKNOWN"

    print(result, file=sys.stderr)
    for _ in range(2):
        try:
            with open(
                "results/pagerank-{}-{}-{}-{}.txt".format(
                    args.pagerank_steps,
                    os.environ.get("PATHWAY_THREADS", 1),
                    time.time(),
                    version,
                ),
                "w",
            ) as f:
                f.write(result)
            break
        except FileNotFoundError:
            os.mkdir("results")
