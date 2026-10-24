from sim.csma_ca import backoff_window

def test_backoff_doubles_and_caps():
    assert [backoff_window(32,k,5) for k in range(7)] == [32,64,128,256,512,1024,1024]
