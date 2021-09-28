"""Get scenes used by a notebook.

Matthew Alger
Geoscience Australia
2021
"""

from contextlib import ExitStack
import unittest.mock

import click
import datacube
from testbook import exceptions
from testbook import testbook


BAD_FNS = [
    'dea_tools.plotting.rgb',
    'datacube.utils.cog.write_cog'
]

def get_unserialisable_mock(tb, deferred):
    try:
        return deferred()
    except exceptions.TestbookSerializeError as e:
        return tb.ref(e.save_varname)
    

def get_scenes_used(nb_path, debug=False):
    dc = datacube.Datacube(app='get_scenes_used')
    with testbook(nb_path, execute=False) as tb:
        with tb.patch('datacube.Datacube') as mock_datacube, ExitStack() as stack:
            # https://stackoverflow.com/questions/45589718/combine-two-context-managers-into-one
            cms = [stack.enter_context(tb.patch(bad_fn)) for bad_fn in BAD_FNS]
            tb.inject("""
import datacube, unittest.mock
def load_store_query(*args, **kwargs):
    mock = unittest.mock.MagicMock()
    mock._query = (args, kwargs)
    mock.load = lambda: mock  # Handle dask
    mock.geobox.dimensions = [1, 1]
    return mock
datacube.Datacube().load = unittest.mock.MagicMock(name='loader', side_effect=load_store_query)
            """)
            tb.execute()
            dc_ = tb.ref('dc')
            queries = dc_.load.call_args_list
            n_calls = dc_.load.call_count.resolve()
            query_list = []
            for i in range(n_calls):
                ref = get_unserialisable_mock(tb, lambda: queries[i])
                if debug:
                    print(ref)
                try:
                    args, kwargs = ref
                except exceptions.TestbookSerializeError:
                    try:
                        res = get_unserialisable_mock(tb, lambda: ref.kwargs['like'])
                    except exceptions.TestbookRuntimeError:  # KeyError
                        args = ref.args
                        kwargs = {k: ref.kwargs[k] for k in ref.kwargs if k != 'progress_cbk'}
                    kwargs['product'] = ref.kwargs['product']
                query_list.append((args, kwargs))
            scene_uris = set()
            for args, kwargs in query_list:
                for bad_arg in ['resampling', 'dask_chunks']:
                    if bad_arg in kwargs:
                        del kwargs[bad_arg]
                if debug:
                    print(args, kwargs)
                datasets = dc.find_datasets(*args, **kwargs)
                for ds in datasets:
                    for uri in ds.uris:
                        scene_uris.add(uri)
            print('\n'.join(sorted(scene_uris)))

            
@click.command()
@click.argument('path')
@click.option('--debug/--no-debug', default=False)
def main(path, debug):
    return get_scenes_used(path, debug=debug)


if __name__ == '__main__':
    main()
