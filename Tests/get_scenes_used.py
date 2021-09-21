"""Get scenes used by a notebook.

Matthew Alger
Geoscience Australia
2021
"""

import unittest.mock

import click
import datacube
from testbook import exceptions
from testbook import testbook


def get_unserialisable_mock(tb, deferred):
    try:
        return deferred()
    except exceptions.TestbookSerializeError as e:
        return tb.ref(e.save_varname)
    

def get_scenes_used(nb_path, debug=False):
    dc = datacube.Datacube(app='get_scenes_used')
    with testbook(nb_path, execute=False) as tb:
        with tb.patch('datacube.Datacube') as mock_datacube:
            tb.inject("""
import datacube, unittest.mock
def load_store_query(*args, **kwargs):
    mock = unittest.mock.MagicMock()
    mock._query = (args, kwargs)
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
            for args, kwargs in query_list:
                if 'resampling' in kwargs:
                    del kwargs['resampling']
                if debug:
                    print(args, kwargs)
                datasets = dc.find_datasets(*args, **kwargs)
                for ds in datasets:
                    for uri in ds.uris:
                        print(uri)

            
@click.command()
@click.argument('path')
@click.option('--debug/--no-debug', default=False)
def main(path, debug):
    return get_scenes_used(path, debug=debug)


if __name__ == '__main__':
    main()
