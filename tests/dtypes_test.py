from common import *
from vaex.column import str_type


def test_dtype(ds_local):
  ds = ds_local
  for name in ds.column_names:
    if ds.dtype(name) == str_type:
      assert ds[name].values.dtype.kind in 'OSU'
    else:
      assert ds[name].values.dtype == ds.dtype(ds[name])


def test_dtypes(ds_local):
  ds = ds_local
  assert [ds.dtypes[name] for name in ds.column_names] == [ds[name].dtype for name in ds.column_names]

def test_dtype_str():
  df = vaex.from_arrays(x=["foo", "bars"], y=[1,2])
  assert df.dtype(df.x) == str_type
  df['s'] = df.y.apply(lambda x: str(x))
  assert df.dtype(df.x) == str_type
  assert df.dtype(df.s) == str_type