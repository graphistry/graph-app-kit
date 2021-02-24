def vertex_to_dict(vertex):
    d = {}
    for k in vertex.keys():
        if isinstance(vertex[k], list):
            d[str(k)] = vertex[k][0]
        else:
            d[str(k)] = vertex[k]
    d['id'] = d.pop('T.id')
    d['label'] = d.pop('T.label')
    return d


def edge_to_dict(edge, start_id, end_id):
    d = {}
    for k in edge.keys():
        if isinstance(edge[k], list):
            d[str(k)] = edge[k][0]
        else:
            d[str(k)] = edge[k]
    d['id'] = d.pop('T.id')
    d['label'] = d.pop('T.label')
    d['source'] = start_id
    d['target'] = end_id
    return d


def flatten_df(df):

    def obj_as_primitive(v):
        if (v is None) or type(v) == str:
            return v
        if type(v) == list:
            return ','.join([str(x) for x in v])
        return str(v)

    df2 = df.copy(deep=False)
    for c in df.columns:
        if df2[c].dtype.name == 'object':
            df2[c] = df2[c].apply(obj_as_primitive)

    return df2
