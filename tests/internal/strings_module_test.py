import vaex.strings
import numpy as np
import sys
import pytest
import pyarrow as pa

def test_regex():
    bytes_strings = np.frombuffer(("aapnootmies".encode('utf8')), dtype='S1')
    indices = np.array([0, 3, 3+4, 3+4+4], dtype=np.int32)
    sl = vaex.strings.StringList32(bytes_strings, indices, 3, 0)
    assert sl.search('aa', False).tolist() == [True, False, False]
    assert sl.search('aa', True).tolist() == [True, False, False]
    # assert False

def test_regex_array():
    ar = np.array(["aap", "noot", "mies"], dtype='object')
    sa = vaex.strings.StringArray(ar)
    assert sa.search('aa', False).tolist() == [True, False, False]
    assert sa.search('aa', True).tolist() == [True, False, False]
    # assert False

def test_string_array():
    ar = np.array(["aap", "noot", "mies"], dtype='object')

    sa = vaex.strings.StringArray(ar)
    assert sys.getrefcount(sa) == 2
    # we should keep a reference only
    assert sys.getrefcount(ar) == 2

    assert sa.get(0) == "aap"
    assert sa.get(1) == "noot"
    assert sa.get(2) == "mies"
    # getting a string creates a new object
    s = sa.get(2)
    assert sys.getrefcount(s) == 2

    string_list = sa.get(0,3)
    assert sys.getrefcount(string_list) == 2
    # internally in the list, s, and in getrefcount
    s = string_list[0]
    assert sys.getrefcount(s) == 3

    assert list(sa.get(0,3)) == ["aap", "noot", "mies"]
    assert list(sa.get(1,3)) == ["noot", "mies"]
    string_list = sa.get(0,3)

    c = sa.capitalize()
    assert list(c.get(0,3)) == ["Aap", "Noot", "Mies"]
    assert list(c.get(1,3)) == ["Noot", "Mies"]


def test_arrow_offset():
    bytes_strings = np.frombuffer(("aapnootmies".encode('utf8')), dtype='S1')


def test_arrow_split():

    ar = pa.array(['a,p', 'no,t', None, 'mi,,'])
    bitmap_buffer, offsets, string_bytes = ar.buffers()

    offset = 5
    indices = np.frombuffer(offsets, np.int32, len(offsets)//4) + offset
    null_bitmap = np.frombuffer(bitmap_buffer, np.uint8, len(bitmap_buffer))
    bytes_strings = np.frombuffer(string_bytes, 'S1', len(string_bytes))

    # bytes_strings = np.frombuffer(("a,pno,tmi,,".encode('utf8')), dtype='S1')
    # offset = 5
    # indices = np.array([+0, 3, 3+4, 3+4+4], dtype=np.int32) + offset
    sl = vaex.strings.StringList32(bytes_strings, indices, len(ar), offset, null_bitmap)

    sll = sl.split(',')
    assert len(sll) == 4
    assert sll.get(0) == ['a', 'p']
    assert sll.get(0, 0) == 'a'
    assert sll.get(0, 1) == 'p'

    assert sll.get(1, 0) == 'no'
    assert sll.get(1, 1) == 't'

    assert sll.get(2) == None
    
    assert sll.get(3, 0) == 'mi'
    assert sll.get(3, 1) == ''
    assert sll.get(3, 2) == ''


def test_views():
    offset = 5
    ar = pa.array(['aap', 'noot', None, 'mies'])
    bitmap_buffer, offsets, string_bytes = ar.buffers()
    indices = np.frombuffer(offsets, np.int32, len(offsets)//4) + offset
    null_bitmap = np.frombuffer(bitmap_buffer, np.uint8, len(bitmap_buffer))

    bytes_strings = np.frombuffer(string_bytes, 'S1', len(string_bytes))
    sl = vaex.strings.StringList32(bytes_strings, indices, len(ar), offset, null_bitmap)
    
    view_indices = np.array([3, 2, 0])
    assert sys.getrefcount(view_indices) == 2
    assert sys.getrefcount(sl) == 2
    # it is a lazy view, so it should increase reference count
    slv = sl.lazy_index(view_indices)
    assert sys.getrefcount(view_indices) == 3
    assert sys.getrefcount(sl) == 3
    assert slv.tolist() == ['mies', None, 'aap']
    del slv  # and also drop the ref count
    assert sys.getrefcount(view_indices) == 2
    assert sys.getrefcount(sl) == 2

    slv = sl.index(view_indices)
    # an index (copy) should not do that
    assert sys.getrefcount(view_indices) == 2
    assert sys.getrefcount(sl) == 2
    assert slv.tolist() == ['mies', None, 'aap']

    mask = np.array([False, True, True, False])
    slv = slv.index(mask)
    # an index (copy) should not do that
    assert sys.getrefcount(view_indices) == 2
    assert sys.getrefcount(sl) == 2
    assert slv.tolist() == [None, 'aap']

def test_concat():
    offset = 5
    ar = pa.array(['aap', 'noot', None, 'mies'])
    bitmap_buffer, offsets, string_bytes = ar.buffers()
    indices = np.frombuffer(offsets, np.int32, len(offsets)//4) + offset
    null_bitmap = np.frombuffer(bitmap_buffer, np.uint8, len(bitmap_buffer))

    bytes_strings = np.frombuffer(string_bytes, 'S1', len(string_bytes))
    sl = vaex.strings.StringList32(bytes_strings, indices, len(ar), offset, null_bitmap)
    view_indices = np.array([3, 2, 0, 1])
    slv = sl.lazy_index(view_indices)
    slc = sl.concat(slv)
    assert slc.tolist() == ['aapmies', None, None, 'miesnoot']

def test_arrow_basics():
    offset = 5
    ar = pa.array(['aap', 'noot', None, 'mies'])
    bitmap_buffer, offsets, string_bytes = ar.buffers()
    indices = np.frombuffer(offsets, np.int32, len(offsets)//4) + offset
    null_bitmap = np.frombuffer(bitmap_buffer, np.uint8, len(bitmap_buffer))

    bytes_strings = np.frombuffer(string_bytes, 'S1', len(string_bytes))
    # indices = np.frombuffer(offsets, np.int32, len(offsets)//4)

    # ref counts start at 2
    assert sys.getrefcount(bytes_strings) == 2
    assert sys.getrefcount(indices) == 2

    sl = vaex.strings.StringList32(bytes_strings, indices, len(ar), offset, null_bitmap)
    assert sys.getrefcount(sl) == 2
    # we should keep a reference only
    assert sys.getrefcount(bytes_strings) == 3
    assert sys.getrefcount(indices) == 3

    assert sl.get(0) == "aap"
    assert sl.get(1) == "noot"
    assert sl.get(2) == None
    assert sl.get(3) == "mies"
    # getting a string creates a new object
    s = sl.get(3)
    assert sys.getrefcount(s) == 2

    string_list = sl.get(0,3)
    assert sys.getrefcount(string_list) == 2
    # internally in the list, s, and in getrefcount
    s = string_list[0]
    assert sys.getrefcount(s) == 3

    assert list(sl.get(0,4)) == ["aap", "noot", None, "mies"]
    assert list(sl.get(1,3)) == ["noot", None]
    string_list = sl.get(0,3)

    c = sl.capitalize()
    assert list(c.get(0,4)) == ["Aap", "Noot", None, "Mies"]
    assert list(c.get(1,3)) == ["Noot",  None]

    c = sl.lower()
    assert list(c.get(0,4)) == ["aap", "noot",  None, "mies"]

    c = sl.upper()
    assert list(c.get(0,4)) == ["AAP", "NOOT",  None, "MIES"]

    c = sl.count("a", False)
    assert c.tolist() == [2, 0, 0, 0]

    sl2 = vaex.strings.StringList32(sl.bytes, sl.indices, sl.length, sl.offset, null_bitmap)
    assert list(sl2.get(0,4)) == ["aap", "noot",  None, "mies"]
    assert list(sl2.get(1,4)) == ["noot",  None, "mies"]

    # ds2.columns['name_arrow'][:].string_sequence.slice(0,5).indices
    assert sys.getrefcount(sl) == 2
    sl_slice = sl.slice(1, 4)
    assert list(sl_slice.get(0,3)) == ["noot",  None, "mies"]
    assert sys.getrefcount(sl) == 3
    del sl_slice
    assert sys.getrefcount(sl) == 2

    sl_slice = sl.slice(0, 3)
    assert list(sl_slice.get(0,3)) == ["aap", "noot",  None]


    offset2 = 11
    indices2 = indices.copy()
    indices2[:] = 1
    null_bitmap2 = null_bitmap.copy()
    null_bitmap2[:] = 0xff
    bytes_strings2 = bytes_strings.copy()
    bytes_strings2[:] = b'?'

    assert sys.getrefcount(indices) == 3
    assert sys.getrefcount(bytes_strings) == 3

    sl_copy = vaex.strings.StringList32(bytes_strings2, indices2, len(ar), offset2, null_bitmap2)
    sl_copy.fill_from(sl)
    assert list(sl_copy.get(0,4)) == ["aap", "noot",  None, "mies"]

    # test fill_from with unequal offset

    offset = 110
    ar3 = pa.array([None, 'NOOT', 'MIES'])
    bitmap_buffer3, offsets3, string_bytes3 = ar3.buffers()
    indices3 = np.frombuffer(offsets3, np.int32, len(offsets3)//4) + offset
    null_bitmap3 = np.frombuffer(bitmap_buffer3, np.uint8, len(bitmap_buffer3))
    bytes_strings3 = np.frombuffer(string_bytes3, 'S1', len(string_bytes3))
    sl_upper = vaex.strings.StringList32(bytes_strings3, indices3, len(ar3), offset, null_bitmap3)

    sl14 = sl.slice(1, 4)
    assert sl14.offset != sl_upper.offset
    assert sl14.fill_from(sl_upper) == 4+4
    assert list(sl14.get(0,3)) == [None, "NOOT", "MIES"]


    sl14 = sl.slice(1, 4, 3)
    assert sl14.offset != sl_upper.offset
    assert sl14.fill_from(sl_upper) == 4+4
    assert list(sl14.get(0,3)) == [None, "NOOT", "MIES"]


    # sl14 and sl_slice keep a reference to sl
    del sl
    assert sys.getrefcount(indices) == 3
    assert sys.getrefcount(bytes_strings) == 3
    del sl14
    del sl_slice
    assert sys.getrefcount(indices) == 2
    assert sys.getrefcount(bytes_strings) == 2

N = 1**32+2
def test_string_array_big():
    offset = 0
    bytes_strings = np.zeros(N, dtype='S1')
    bytes_strings[:] = 'x'
    bytes_strings[-1] = 'y'

    indices = np.arange(0, N+1, dtype='i8')

    sl = vaex.strings.StringList64(bytes_strings, indices, N, offset)
    assert type(sl) == vaex.strings.StringList64

    assert sl.get(N-1) == 'y'
    assert sl.get(N-2) == 'x'

def test_string_format():
    ar = np.arange(1, 4, dtype='f4')
    vaex.strings.to_string(ar).tolist() == ["1.0", "2.0", "3.0"]
    vaex.strings.format(ar, '%g').tolist() == ["%g" % k for k in ar]
