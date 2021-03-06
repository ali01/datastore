
import unittest

import datastore
from datastore import Key
from datastore import Query


class TestDatastore(unittest.TestCase):

  def subtest_simple(self, stores, numelems=1000):

    def checkLength(len):
      try:
        for sn in stores:
          self.assertEqual(len(sn), numelems)
      except TypeError, e:
        pass

    self.assertTrue(len(stores) > 0)

    pkey = Key('/dfadasfdsafdas/')

    checkLength(0)

    # ensure removing non-existent keys is ok.
    for value in range(0, numelems):
      key = pkey.child(value)
      for sn in stores:
        self.assertFalse(sn.contains(key))
        sn.delete(key)
        self.assertFalse(sn.contains(key))

    checkLength(0)

    # insert numelems elems
    for value in range(0, numelems):
      key = pkey.child(value)
      for sn in stores:
        self.assertFalse(sn.contains(key))
        sn.put(key, value)
        self.assertTrue(sn.contains(key))
        self.assertEqual(sn.get(key), value)

    # reassure they're all there.
    checkLength(numelems)

    for value in range(0, numelems):
      key = pkey.child(value)
      for sn in stores:
        self.assertTrue(sn.contains(key))
        self.assertEqual(sn.get(key), value)

    checkLength(numelems)

    k = pkey
    n = int(numelems)
    allitems = list(range(0, n))

    def test_query(query, slice):
      for sn in stores:
        try:
          contents = list(sn.query(Query(pkey)))
          expected = contents[slice]
          result = list(sn.query(query))

          # make sure everything is there.
          self.assertTrue(len(contents) == len(allitems))
          self.assertTrue(all([val in contents for val in allitems]))

          self.assertTrue(len(result) == len(expected))
          self.assertTrue(all([val in result for val in expected]))
          #TODO: should order be preserved?
          # self.assertEqual(result, expected)

        except NotImplementedError:
          print 'WARNING: %s does not implement query.' % sn

    test_query(Query(k), slice(0, n))
    test_query(Query(k, limit=n), slice(0, n))
    test_query(Query(k, limit=n/2), slice(0, n/2))
    test_query(Query(k, offset=n/2), slice(n/2, n))
    test_query(Query(k, offset=n/3, limit=n/3), slice(n/3, 2*(n/3)))
    del k
    del n

    # change numelems elems
    for value in range(0, numelems):
      key = pkey.child(value)
      for sn in stores:
        self.assertTrue(sn.contains(key))
        sn.put(key, value + 1)
        self.assertTrue(sn.contains(key))
        self.assertNotEqual(value, sn.get(key))
        self.assertEqual(value + 1, sn.get(key))

    checkLength(numelems)

    # remove numelems elems
    for value in range(0, numelems):
      key = pkey.child(value)
      for sn in stores:
        self.assertTrue(sn.contains(key))
        sn.delete(key)
        self.assertFalse(sn.contains(key))

    checkLength(0)


class TestDictionaryDatastore(TestDatastore):

  def test_dictionary(self):

    s1 = datastore.DictDatastore()
    s2 = datastore.DictDatastore()
    s3 = datastore.DictDatastore()
    stores = [s1, s2, s3]

    self.subtest_simple(stores)


class TestKeyTransformDatastore(TestDatastore):

  def test_simple(self):

    s1 = datastore.KeyTransformDatastore(datastore.DictDatastore())
    s2 = datastore.KeyTransformDatastore(datastore.DictDatastore())
    s3 = datastore.KeyTransformDatastore(datastore.DictDatastore())
    stores = [s1, s2, s3]

    self.subtest_simple(stores)

  def test_reverse_transform(self):

    def transform(key):
      return key.reverse

    ds = datastore.DictDatastore()
    kt = datastore.KeyTransformDatastore(ds, keytransform=transform)

    k1 = Key('/a/b/c')
    k2 = Key('/c/b/a')
    self.assertFalse(ds.contains(k1))
    self.assertFalse(ds.contains(k2))
    self.assertFalse(kt.contains(k1))
    self.assertFalse(kt.contains(k2))

    ds.put(k1, 'abc')
    self.assertEqual(ds.get(k1), 'abc')
    self.assertFalse(ds.contains(k2))
    self.assertFalse(kt.contains(k1))
    self.assertEqual(kt.get(k2), 'abc')

    kt.put(k1, 'abc')
    self.assertEqual(ds.get(k1), 'abc')
    self.assertEqual(ds.get(k2), 'abc')
    self.assertEqual(kt.get(k1), 'abc')
    self.assertEqual(kt.get(k2), 'abc')

    ds.delete(k1)
    self.assertFalse(ds.contains(k1))
    self.assertEqual(ds.get(k2), 'abc')
    self.assertEqual(kt.get(k1), 'abc')
    self.assertFalse(kt.contains(k2))

    kt.delete(k1)
    self.assertFalse(ds.contains(k1))
    self.assertFalse(ds.contains(k2))
    self.assertFalse(kt.contains(k1))
    self.assertFalse(kt.contains(k2))

  def test_lowercase_transform(self):

    def transform(key):
      return Key(str(key).lower())

    ds = datastore.DictDatastore()
    lds = datastore.KeyTransformDatastore(ds, keytransform=transform)

    k1 = Key('hello')
    k2 = Key('HELLO')
    k3 = Key('HeLlo')

    ds.put(k1, 'world')
    ds.put(k2, 'WORLD')

    self.assertEqual(ds.get(k1), 'world')
    self.assertEqual(ds.get(k2), 'WORLD')
    self.assertFalse(ds.contains(k3))

    self.assertEqual(lds.get(k1), 'world')
    self.assertEqual(lds.get(k2), 'world')
    self.assertEqual(lds.get(k3), 'world')

    def test(key, val):
      lds.put(key, val)
      self.assertEqual(lds.get(k1), val)
      self.assertEqual(lds.get(k2), val)
      self.assertEqual(lds.get(k3), val)

    test(k1, 'a')
    test(k2, 'b')
    test(k3, 'c')



class TestLowercaseKeyDatastore(TestDatastore):

  def test_simple(self):

    s1 = datastore.LowercaseKeyDatastore(datastore.DictDatastore())
    s2 = datastore.LowercaseKeyDatastore(datastore.DictDatastore())
    s3 = datastore.LowercaseKeyDatastore(datastore.DictDatastore())
    stores = [s1, s2, s3]

    self.subtest_simple(stores)


  def test_lowercase(self):

    ds = datastore.DictDatastore()
    lds = datastore.LowercaseKeyDatastore(ds)

    k1 = Key('hello')
    k2 = Key('HELLO')
    k3 = Key('HeLlo')

    ds.put(k1, 'world')
    ds.put(k2, 'WORLD')

    self.assertEqual(ds.get(k1), 'world')
    self.assertEqual(ds.get(k2), 'WORLD')
    self.assertFalse(ds.contains(k3))

    self.assertEqual(lds.get(k1), 'world')
    self.assertEqual(lds.get(k2), 'world')
    self.assertEqual(lds.get(k3), 'world')

    def test(key, val):
      lds.put(key, val)
      self.assertEqual(lds.get(k1), val)
      self.assertEqual(lds.get(k2), val)
      self.assertEqual(lds.get(k3), val)

    test(k1, 'a')
    test(k2, 'b')
    test(k3, 'c')


class TestNamespaceDatastore(TestDatastore):

  def test_simple(self):

    s1 = datastore.NamespaceDatastore(Key('a'), datastore.DictDatastore())
    s2 = datastore.NamespaceDatastore(Key('b'), datastore.DictDatastore())
    s3 = datastore.NamespaceDatastore(Key('c'), datastore.DictDatastore())
    stores = [s1, s2, s3]

    self.subtest_simple(stores)


  def test_namespace(self):

    k1 = Key('/c/d')
    k2 = Key('/a/b')
    k3 = Key('/a/b/c/d')

    ds = datastore.DictDatastore()
    nd = datastore.NamespaceDatastore(k2, ds)

    ds.put(k1, 'cd')
    ds.put(k3, 'abcd')

    self.assertEqual(ds.get(k1), 'cd')
    self.assertFalse(ds.contains(k2))
    self.assertEqual(ds.get(k3), 'abcd')

    self.assertEqual(nd.get(k1), 'abcd')
    self.assertFalse(nd.contains(k2))
    self.assertFalse(nd.contains(k3))

    def test(key, val):
      nd.put(key, val)
      self.assertEqual(nd.get(key), val)
      self.assertFalse(ds.contains(key))
      self.assertFalse(nd.contains(k2.child(key)))
      self.assertEqual(ds.get(k2.child(key)), val)

    for i in range(0, 10):
      test(Key(str(i)), 'val%d' % i)


class TestDatastoreCollection(TestDatastore):

  def test_tiered(self):

    s1 = datastore.DictDatastore()
    s2 = datastore.DictDatastore()
    s3 = datastore.DictDatastore()
    ts = datastore.TieredDatastore([s1, s2, s3])

    k1 = Key('1')
    k2 = Key('2')
    k3 = Key('3')

    s1.put(k1, '1')
    s2.put(k2, '2')
    s3.put(k3, '3')

    self.assertTrue(s1.contains(k1))
    self.assertFalse(s2.contains(k1))
    self.assertFalse(s3.contains(k1))
    self.assertTrue(ts.contains(k1))

    self.assertEqual(ts.get(k1), '1')
    self.assertEqual(s1.get(k1), '1')
    self.assertFalse(s2.contains(k1))
    self.assertFalse(s3.contains(k1))

    self.assertFalse(s1.contains(k2))
    self.assertTrue(s2.contains(k2))
    self.assertFalse(s3.contains(k2))
    self.assertTrue(ts.contains(k2))

    self.assertEqual(s2.get(k2), '2')
    self.assertFalse(s1.contains(k2))
    self.assertFalse(s3.contains(k2))

    self.assertEqual(ts.get(k2), '2')
    self.assertEqual(s1.get(k2), '2')
    self.assertEqual(s2.get(k2), '2')
    self.assertFalse(s3.contains(k2))

    self.assertFalse(s1.contains(k3))
    self.assertFalse(s2.contains(k3))
    self.assertTrue(s3.contains(k3))
    self.assertTrue(ts.contains(k3))

    self.assertEqual(s3.get(k3), '3')
    self.assertFalse(s1.contains(k3))
    self.assertFalse(s2.contains(k3))

    self.assertEqual(ts.get(k3), '3')
    self.assertEqual(s1.get(k3), '3')
    self.assertEqual(s2.get(k3), '3')
    self.assertEqual(s3.get(k3), '3')

    ts.delete(k1)
    ts.delete(k2)
    ts.delete(k3)

    self.assertFalse(ts.contains(k1))
    self.assertFalse(ts.contains(k2))
    self.assertFalse(ts.contains(k3))

    self.subtest_simple([ts])

  def test_sharded(self, numelems=1000):

    s1 = datastore.DictDatastore()
    s2 = datastore.DictDatastore()
    s3 = datastore.DictDatastore()
    s4 = datastore.DictDatastore()
    s5 = datastore.DictDatastore()
    stores = [s1, s2, s3, s4, s5]
    hash = lambda key: int(key.name) * len(stores) / numelems
    sharded = datastore.ShardedDatastore(stores, shardingfn=hash)
    sumlens = lambda stores: sum(map(lambda s: len(s), stores))

    def checkFor(key, value, sharded, shard=None):
      correct_shard = sharded._stores[hash(key) % len(sharded._stores)]

      for s in sharded._stores:
        if shard and s == shard:
          self.assertTrue(s.contains(key))
          self.assertEqual(s.get(key), value)
        else:
          self.assertFalse(s.contains(key))

      if correct_shard == shard:
        self.assertTrue(sharded.contains(key))
        self.assertEqual(sharded.get(key), value)
      else:
        self.assertFalse(sharded.contains(key))

    self.assertEqual(sumlens(stores), 0)
    # test all correct.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      shard = stores[hash(key) % len(stores)]
      checkFor(key, value, sharded)
      shard.put(key, value)
      checkFor(key, value, sharded, shard)
    self.assertEqual(sumlens(stores), numelems)

    # ensure its in the same spots.
    for i in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      shard = stores[hash(key) % len(stores)]
      checkFor(key, value, sharded, shard)
      shard.put(key, value)
      checkFor(key, value, sharded, shard)
    self.assertEqual(sumlens(stores), numelems)

    # ensure its in the same spots.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      shard = stores[hash(key) % len(stores)]
      checkFor(key, value, sharded, shard)
      sharded.put(key, value)
      checkFor(key, value, sharded, shard)
    self.assertEqual(sumlens(stores), numelems)

    # ensure its in the same spots.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      shard = stores[hash(key) % len(stores)]
      checkFor(key, value, sharded, shard)
      if value % 2 == 0:
        shard.delete(key)
      else:
        sharded.delete(key)
      checkFor(key, value, sharded)
    self.assertEqual(sumlens(stores), 0)

    # try out adding it to the wrong shards.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      incorrect_shard = stores[(hash(key) + 1) % len(stores)]
      checkFor(key, value, sharded)
      incorrect_shard.put(key, value)
      checkFor(key, value, sharded, incorrect_shard)
    self.assertEqual(sumlens(stores), numelems)

    # ensure its in the same spots.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      incorrect_shard = stores[(hash(key) + 1) % len(stores)]
      checkFor(key, value, sharded, incorrect_shard)
      incorrect_shard.put(key, value)
      checkFor(key, value, sharded, incorrect_shard)
    self.assertEqual(sumlens(stores), numelems)

    # this wont do anything
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      incorrect_shard = stores[(hash(key) + 1) % len(stores)]
      checkFor(key, value, sharded, incorrect_shard)
      sharded.delete(key)
      checkFor(key, value, sharded, incorrect_shard)
    self.assertEqual(sumlens(stores), numelems)

    # this will place it correctly.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      incorrect_shard = stores[(hash(key) + 1) % len(stores)]
      correct_shard = stores[(hash(key)) % len(stores)]
      checkFor(key, value, sharded, incorrect_shard)
      sharded.put(key, value)
      incorrect_shard.delete(key)
      checkFor(key, value, sharded, correct_shard)
    self.assertEqual(sumlens(stores), numelems)

    # this will place it correctly.
    for value in range(0, numelems):
      key = Key('/fdasfdfdsafdsafdsa/%d' % value)
      correct_shard = stores[(hash(key)) % len(stores)]
      checkFor(key, value, sharded, correct_shard)
      sharded.delete(key)
      checkFor(key, value, sharded)
    self.assertEqual(sumlens(stores), 0)

    self.subtest_simple([sharded])


if __name__ == '__main__':
  unittest.main()
