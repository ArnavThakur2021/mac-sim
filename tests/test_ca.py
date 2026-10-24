from sim.csma_ca import simulate
from sim.common import jains_index
from sim.bianchi import solve

def test_single_station_no_collisions():
    x=simulate(1,.5,seed=4)
    assert x['collisions']==0 and .80 < x['throughput'] <= 1
    assert abs(x['success_fraction']+x['collision_fraction']+x['idle_fraction']-1)<1e-9

def test_fairness():
    assert jains_index([2,2])==1
    assert jains_index([1,0,0])==1/3

def test_reproducible():
    assert simulate(5,.1,seed=9)==simulate(5,.1,seed=9)

def test_long_run_tracks_bianchi():
    for n in (5,10,20):
        observed=simulate(n,5.0,seed=11)['throughput']
        expected=solve(n)['throughput']
        assert abs(observed-expected)/expected < .05
