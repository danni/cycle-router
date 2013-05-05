

def test_index(app):
    rv = app.get('/')

    print rv.data

    assert '<title>Cycle Router</title>' in rv.data
    assert '0 contributors.' in rv.data
    assert '0.0 kilometers.' in rv.data
