def attr_update(obj, child=None, _call=True, **kwargs):
    '''Updates attributes on nested namedtuples.
    Accepts a namedtuple object, a string denoting the nested namedtuple to update,
    and keyword parameters for the new values to assign to its attributes.

    You may set _call=False if you wish to assign a callable to a target attribute.

    Example: to replace obj.x.y.z, do attr_update(obj, "x.y", z=new_value).
    Example: attr_update(obj, "x.y.z", prop1=lambda prop1: prop1*2, prop2='new prop2')
    Example: attr_update(obj, "x.y", lambda z: z._replace(prop1=prop1*2, prop2='new prop2'))
    Example: attr_update(obj, alpha=lambda alpha: alpha*2, beta='new beta')
    '''
    def call_val(old, new):
        if _call and callable(new):
            new_value = new(old)
        else:
            new_value = new
        return new_value
        
    def replace_(to_replace, parts):
        parent = reduce(getattr, parts, obj)
        new_values = {k: call_val(getattr(parent, k), v) for k,v in to_replace.iteritems()}
        new_parent = parent._replace(**new_values)
        if len(parts) == 0:
            return new_parent
        else:
            return {parts[-1]: new_parent}

    if child in (None, ""):
        parts = tuple()
    else:
        parts = child.split(".")
    return reduce(
        replace_,
        (parts[:i] for i in xrange(len(parts), -1, -1)),
        kwargs
    )
