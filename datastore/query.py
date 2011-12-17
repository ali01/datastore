

def _object_getattr(obj, field):
  '''Attribute getter for the objects to operate on.

  This function can be overridden in classes or instances of Query, Filter, and Order.
  Thus, a custom function to extract values to attributes can be specified, and the
  system can remain agnostic to the client's data model, without loosing query power.
  '''

  # TODO: consider changing this to raise an exception if no value is found.
  value = None

  # check whether this key is an attribute
  if hasattr(obj, field):
    value = getattr(obj, field)

  # if not, perhaps it is an item (raw dicts, etc)
  elif field in obj:
    value = obj[field]

  # return whatever we've got.
  return value




def limit_gen(limit, iterable):
  '''A generator that applies a count `limit`.'''
  limit = int(limit)
  assert limit >= 0, 'negative limit'

  for item in iterable:
    if limit <= 0:
      break
    yield item
    limit -= 1


def offset_gen(offset, iterable):
  '''A generator that applies an `offset`.'''
  offset = int(offset)
  assert offset >= 0, 'negative offset'

  for item in iterable:
    if offset > 0:
      offset -= 1
    else:
      yield item




class Filter(object):
  '''Represents a Filter for a specific field and its value.
  Filters are used on queries to narrow down the set of matching objects.
  '''

  CONDITIONAL_OPERATORS = {
    "<"  : lambda a, b: a < b,
    "<=" : lambda a, b: a <= b,
    "="  : lambda a, b: a == b,
    "!=" : lambda a, b: a != b,
    ">=" : lambda a, b: a >= b,
    ">"  : lambda a, b: a > b
  }

  '''Object attribute getter. Can be overridden to match client data model.'''
  object_getattr = staticmethod(_object_getattr)

  def __init__(self, field, op, value):
    if op not in self.CONDITIONAL_OPERATORS:
      raise ValueError('"%s" is not a valid filter Conditional Operator' % op)

    self.field = field
    self.op = op
    self.value = value

  def __call__(self, obj):
    '''Returns whether this object passes this filter.
    This method aggressively tries to find the appropriate value.
    '''
    value = self.object_getattr(obj, self.field)

    # TODO: which way should the direction go here? it may make more sense to
    #       convert the passed-in value instead. Or try both? Or not do it at all?
    if not isinstance(value, self.value.__class__):
      value = self.value.__class__(value)

    return self.valuePasses(value)

  def valuePasses(self, value):
    '''Returns whether this value passes this filter'''
    return self.CONDITIONAL_OPERATORS[self.op](value, self.value)


  def __str__(self):
    return '%s %s %s' % (self.field, self.op, self.value)

  def __repr__(self):
    return "Filter('%s', '%s', %s)" % (self.field, self.op, repr(self.value))


  def __eq__(self, o):
    return self.field == o.field and self.op == o.op and self.value == o.value

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(repr(self))

  def generator(self, iterable):
    '''Generator function that iteratively filters given `items`.'''
    for item in iterable:
      if self(item):
        yield item

  @classmethod
  def filter(cls, filters, iterable):
    '''Returns the elements in `iterable` that pass given `filters`'''
    if isinstance(filters, Filter):
      filters = [filters]

    for filter in filters:
      iterable = filter.generator(iterable)

    return iterable





class Order(object):
  '''Represents an Order upon a specific field, and a direction.
  Orders are used on queries to define how they operate on objects
  '''

  ORDER_OPERATORS = ['-', '+']

  '''Object attribute getter. Can be overridden to match client data model.'''
  object_getattr = staticmethod(_object_getattr)

  def __init__(self, order):
    self.op = '+'

    try:
      if order[0] in self.ORDER_OPERATORS:
        self.op = order[0]
        order = order[1:]
    except IndexError:
      raise ValueError('Order input be at least two characters long.')

    self.field = order

    if self.op not in self.ORDER_OPERATORS:
      raise ValueError('"%s" is not a valid Order Operator.' % op)


  def __str__(self):
    return '%s%s' % (self.op, self.field)

  def __repr__(self):
    return "Order('%s%s')" % (self.op, self.field)


  def __eq__(self, other):
    return self.field == other.field and self.op == other.op

  def __ne__(self, other):
    return not self.__eq__(other)

  def __hash__(self):
    return hash(repr(self))


  def isAscending(self):
    return self.op == '+'

  def isDescending(self):
    return not self.isAscending()


  def keyfn(self, obj):
    '''A key function to be used in pythonic sort operations.'''
    return self.object_getattr(obj, self.field)

  @classmethod
  def multipleOrderComparison(cls, orders):
    '''Returns a function that will compare two items according to `orders`'''
    comparers = [ (o.keyfn, 1 if o.isAscending() else -1) for o in orders]

    def cmpfn(a, b):
      for keyfn, ascOrDesc in comparers:
        comparison = cmp(keyfn(a), keyfn(b)) * ascOrDesc
        if comparison is not 0:
          return comparison
      return 0

    return cmpfn

  @classmethod
  def sorted(cls, items, orders):
    '''Returns the elements in `items` sorted according to `orders`'''
    return sorted(items, cmp=cls.multipleOrderComparison(orders))




class Query(object):
  '''A Query describes a set of objects.

  Queries are used to retrieve objects and instances matching a set of criteria
  from Datastores. Query objects themselves are simply descriptions,
  the actual Query implementations are left up to the Datastores.
  '''

  '''Object attribute getter. Can be overridden to match client data model.'''
  object_getattr = staticmethod(_object_getattr)

  def __init__(self, limit=None, offset=0, object_getattr=None):
    self.limit = int(limit) if limit is not None else None
    self.offset = int(offset)

    self.filters = []
    self.orders = []

    if object_getattr:
      self.object_getattr = object_getattr

  def __str__(self):
    '''Returns a string describing this query.'''
    return repr(self)

  def __repr__(self):
    '''Returns the representation of this query. Enables eval(repr(.)).'''
    return 'Query.from_dict(%s)' % self.dict()

  def __call__(self, iterable):
    '''Naively apply this query on an iterable of objects.
    Applying a query applies filters, sorts by appropriate orders, and returns
    a limited set.

    WARNING: When orders are applied, this function operates on the entire set
             of entities directly, not just iterators/generators. That means
             the entire result set will be in memory. Datastores with large
             objects and large query results should translate the Query and
             perform their own optimizations.
    '''

    if len(self.filters) > 0:
      iterable = Filter.filter(self.filters, iterable)

    if len(self.orders) > 0:
      iterable = Order.sorted(iterable, self.orders) # not a generator :(

    if self.offset != 0:
      iterable = offset_gen(self.offset, iterable)

    if self.limit is not None:
      iterable = limit_gen(self.offset, iterable)

    return iterable


  def order(self, order):
    '''Adds an Order to this query.

    Returns self for JS-like method chaining:
    query.order('+age').order('-home')
    '''
    order = order if isinstance(order, Order) else Order(order)

    # ensure order gets attribute values the same way the rest of the query does.
    order.object_getattr = self.object_getattr
    self.orders.append(order)
    return self # for chaining


  def filter(self, *args):
    '''Adds a Filter to this query.

    Returns self for JS-like method chaining:
    query.filter('age', '>', 18).filter('sex', '=', 'Female')
    '''
    if len(args) == 1 and isinstance(args[0], Filter):
      filter = args[0]
    else:
      filter = Filter(*args)

    # ensure filter gets attribute values the same way the rest of the query does.
    filter.object_getattr = self.object_getattr
    self.filters.append(filter)
    return self # for chaining


  def __cmp__(self, other):
    return cmp(self.dict(), other.dict())

  def __hash__(self):
    return hash(repr(self))


  def dict(self):
    '''Returns a dictionary representing this query.'''
    d = dict()

    if self.limit is not None:
      d['limit'] = self.limit
    if self.offset > 0:
      d['offset'] = self.offset
    if len(self.filters) > 0:
      d['filter'] = [[f.field, f.op, f.value] for f in self.filters]
    if len(self.orders) > 0:
      d['order'] = [str(o) for o in self.orders]

    return d

  @classmethod
  def from_dict(cls, dictionary):
    '''Constructs a query from a dictionary.'''
    query = cls()
    for key, value in dictionary.items():

      if key == 'order':
        for order in value:
          query.order(order)

      elif key == 'filter':
        for filter in value:
          if not isinstance(filter, Filter):
            filter = Filter(*filter)
          query.filter(filter)

      elif key in ['limit', 'offset']:
        setattr(query, key, value)
    return query