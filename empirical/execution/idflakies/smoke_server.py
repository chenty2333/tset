import server_run as s, concurrent.futures as cf, time
jobs=[(v,sub,1) for v in ("gate","iid","pair") for sub in ("aismessages","http-request")]
stop=time.time()+7200
with cf.ThreadPoolExecutor(6) as ex:
    for r in ex.map(lambda j: s.job(*j,1800,stop), jobs): print(r,flush=True)
