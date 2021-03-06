"""
TODO : Fix float-rendering and rounding
TODO : Better error handling of wonky builds
TODO : Render git commit SHA as the short-hand version
"""
from wily import logger, format_date
import tabulate
import pathlib
from wily.config import DEFAULT_CACHE_PATH, DEFAULT_GRID_STYLE
import wily.cache as cache
from wily.operators import resolve_metric, MetricType

""" Max number of characters of the Git commit to print """
MAX_MESSAGE_WIDTH = 50


def report(config, path, metric, n, include_message=False):
    """
    Show information about the cache and runtime
    :param config: The configuration
    :type  config: :class:`wily.config.WilyConfig`

    :param path: The path to the file
    :type  path: ``str``

    :param metric: Name of the metric to report on
    :type  metric: ``str``

    :param n: Number of items to list
    :type  n: ``int``
    """
    logger.debug("Running report command")

    logger.info(f"-----------History for {metric}------------")

    data = []
    last = None
    operator, key = metric.split('.')
    metric = resolve_metric(metric)
    archivers = cache.list_archivers()

    # Set the delta colors depending on the metric type
    if metric.measure == MetricType.AimHigh:
        good_color = 32
        bad_color = 31
    elif metric.measure == MetricType.AimLow:
        good_color = 31
        bad_color = 32
    elif metric.measure == MetricType.Informational:
        good_color = 33
        bad_color = 33 

    for archiver in archivers:
        history = cache.get_index(archiver)[:n]
        # We have to do it backwards to get the deltas between releases
        history = history[::-1]
        for rev in history:
            revision_entry = cache.get(archiver, rev['revision'])
            try:
                val = revision_entry["operator_data"][operator][path][key]

                # Measure the difference between this value and the last
                if metric.type in (int, float):
                    if last:
                        delta=val-last
                    else:
                        delta=0
                    last=val
                else:
                    # TODO : Measure ranking increases/decreases for str types?
                    delta = 0

                # TODO : Format floating values nicely
                if delta == 0:
                    delta_col = delta
                elif delta < 0 :
                    delta_col = f"\u001b[{good_color}m{delta}\u001b[0m"
                else:
                    delta_col = f"\u001b[{bad_color}m+{delta}\u001b[0m"

                k = f"{val} ({delta_col})"
            except KeyError:
                k = "Not found"
            finally:
                if include_message:
                    data.append(
                        (
                            rev["revision"],
                            rev['message'][:MAX_MESSAGE_WIDTH],
                            rev["author_name"],
                            format_date(rev["date"]),
                            k
                        )
                    )
                else:
                    data.append(
                        (
                            rev["revision"],
                            rev["author_name"],
                            format_date(rev["date"]),
                            k
                        )
                    )
    if include_message:
        headers=("Revision", "Message", "Author", "Date", metric.description)
    else:
        headers=("Revision", "Author", "Date", metric.description)
    print(
        # But it still makes more sense to show the newest at the top, so reverse again
        tabulate.tabulate(
            headers=headers, tabular_data=data[::-1],
            tablefmt=DEFAULT_GRID_STYLE
        )
    )
