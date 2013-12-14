

def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app

appstats_MAX_STACK = 20
appstats_CALC_RPC_COSTS = True
appstats_DATASTORE_DETAILS = True