def initialize(thread_info):
    """Initialize the system.
    thread_info: tuple of booleans setting threaded_server and threaded_clients
    """
    import sys
    print "LIGHTHEAD Animation System, python version:", sys.version_info

    # check configuration
    try:
        import conf; missing = conf.load()
        if missing:
            fatal('missing configuration entries: %s' % missing)
        if hasattr(conf, 'DEBUG_MODE') and conf.DEBUG_MODE:
            # set system-wide logging level
            import comm; comm.set_default_logging(debug=True)
    except conf.LoadException, e:
        fatal('in file {0[0]}: {0[1]}'.format(e)) 

    # Initializes the system
    import comm
    from lightHead_server import lightHeadServer, lightHeadHandler
    server = comm.create_server(lightHeadServer, lightHeadHandler,
                                conf.lightHead_server, thread_info)
    # Because what we have here is a *meta server*, we need to initialize it
    #  properly; face and all other subservers are initialized in that call
    server.create_protocol_handlers()
    return server
