from sim.csma_cd import simulate

def test_cd_metrics_bounded():
    x=simulate(4,.1,seed=3)
    assert 0<=x['throughput']<=1
    assert abs(x['success_fraction']+x['collision_fraction']+x['idle_fraction']-1)<1e-9
