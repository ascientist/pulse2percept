import numpy as np
import scipy.optimize as scpo
import numpy.testing as npt
import pytest
import logging

import pulse2percept as p2p


def test_Grid():
    # Invalid calls
    with pytest.raises(ValueError):
        grid = p2p.retina.Grid(x_range=1, n_axons=1)
    with pytest.raises(ValueError):
        grid = p2p.retina.Grid(x_range=(1.0, 0.0), n_axons=1)
    with pytest.raises(ValueError):
        grid = p2p.retina.Grid(y_range=1, n_axons=1)
    with pytest.raises(ValueError):
        grid = p2p.retina.Grid(y_range=(1.0, 0.0), n_axons=1)

    # Verify size of axon bundles
    for n_axons in [3, 5, 10]:
        grid = p2p.retina.Grid(x_range=(0, 0), y_range=(0, 0), n_axons=n_axons,
                               save_data=False)
        # Number of axon bundles given by `n_axons`
        npt.assert_equal(len(grid.axon_bundles), n_axons)
        # Number of axons given by number of pixels on grid
        npt.assert_equal(len(grid.axons), 1)


def test_BaseModel():
    # Cannot instantiate abstract class
    with pytest.raises(TypeError):
        tm = p2p.retina.BaseModel(0.01)

    # Child class must provide `model_cascade()`
    class Incomplete(p2p.retina.BaseModel):
        pass
    with pytest.raises(TypeError):
        tm = Incomplete()

    # A complete class
    class Complete(p2p.retina.BaseModel):

        def model_cascade(self, inval):
            return inval

    tm = Complete(tsample=0.1)
    npt.assert_equal(tm.tsample, 0.1)
    npt.assert_equal(tm.model_cascade(2.4), 2.4)


def test_TemporalModel():
    tsample = 0.01 / 1000

    # Assume 4 electrodes, each getting some stimulation
    pts = [p2p.stimuli.PulseTrain(tsample=tsample, dur=0.1)] * 4
    ptrain_data = [pt.data for pt in pts]

    # For each of these 4 electrodes, we have two effective current values:
    # one for the ganglion cell layer, one for the bipolar cell layer
    ecs_item = np.random.rand(2, 4)

    # What we want is the effective current per layer, for all electrodes
    # added up.
    # We do this for different layer configurations:
    for layers in [['INL'], ['GCL'], ['GCL', 'INL']]:
        ecm_by_hand = np.zeros((2, ptrain_data[0].size))
        if 'INL' in layers:
            for curr, pt in zip(ecs_item[0, :], ptrain_data):
                ecm_by_hand[0, :] += curr * pt
        if 'GCL' in layers:
            for curr, pt in zip(ecs_item[1, :], ptrain_data):
                ecm_by_hand[1, :] += curr * pt

        # And that should be the same as `calc_layer_current`:
        tm = p2p.retina.TemporalModel(tsample=tsample)
        ecm = tm.calc_layer_current(ecs_item, ptrain_data, layers)
        npt.assert_almost_equal(ecm, ecm_by_hand)
        tm.model_cascade(ecs_item, ptrain_data, layers, False)

    with pytest.raises(ValueError):
        tm.calc_layer_current(ecs_item, ptrain_data, ['unknown'])
    with pytest.raises(ValueError):
        tm.model_cascade(ecs_item, ptrain_data, ['unknown'], False)


def test_Nanduri2012():
    tsample = 0.01 / 1000
    tm = p2p.retina.Nanduri2012(tsample=tsample)

    # Assume 4 electrodes, each getting some stimulation
    pts = [p2p.stimuli.PulseTrain(tsample=tsample, dur=0.1)] * 4
    ptrain_data = [pt.data for pt in pts]

    # For each of these 4 electrodes, we have two effective current values:
    # one for the ganglion cell layer, one for the bipolar cell layer
    ecs_item = np.random.rand(2, 4)

    # Calulating layer current:
    # The Nanduri model does not support INL, so it's just one layer:
    with pytest.raises(ValueError):
        tm.calc_layer_current(ecs_item, ptrain_data, ['GCL', 'INL'])
    with pytest.raises(ValueError):
        tm.calc_layer_current(ecs_item, ptrain_data, ['unknown'])

    # ...and that should be the same as `calc_layer_current`:
    ecm_by_hand = np.sum(ecs_item[1, :, np.newaxis] * ptrain_data, axis=0)
    ecm = tm.calc_layer_current(ecs_item, ptrain_data, ['GCL'])
    npt.assert_almost_equal(ecm, ecm_by_hand)

    # Running the model cascade:
    with pytest.raises(ValueError):
        tm.model_cascade(ecs_item, ptrain_data, ['GCL', 'INL'], False)
    with pytest.raises(ValueError):
        tm.model_cascade(ecs_item, ptrain_data, ['unknown'], False)
    tm.model_cascade(ecs_item, ptrain_data, ['GCL'], False)


def test_Horsager2009_model_cascade():
    tsample = 0.01 / 1000
    tm = p2p.retina.Horsager2009(tsample=tsample)

    # Assume 4 electrodes, each getting some stimulation
    pts = [p2p.stimuli.PulseTrain(tsample=tsample, dur=0.1)] * 4
    ptrain_data = [pt.data for pt in pts]

    # For each of these 4 electrodes, we have two effective current values:
    # one for the ganglion cell layer, one for the bipolar cell layer
    ecs_item = np.random.rand(2, 4)

    # Run the model cascade:
    with pytest.raises(ValueError):
        tm.model_cascade(ecs_item, ptrain_data, ['GCL', 'INL'], False)
    with pytest.raises(ValueError):
        tm.model_cascade(ecs_item, ptrain_data, ['unknown'], False)
    tm.model_cascade(ecs_item, ptrain_data, ['GCL'], False)


def test_Horsager2009_calc_layer_current():
    tsample = 0.01 / 1000
    tm = p2p.retina.Horsager2009(tsample=tsample)

    # Assume 4 electrodes, each getting some stimulation
    pts = [p2p.stimuli.PulseTrain(tsample=tsample, dur=0.1)] * 4
    ptrain_data = [pt.data for pt in pts]

    # For each of these 4 electrodes, we have two effective current values:
    # one for the ganglion cell layer, one for the bipolar cell layer
    ecs_item = np.random.rand(2, 4)

    # Calulating layer current:
    # The Horsager model does not support INL, so it's just one layer:
    with pytest.raises(ValueError):
        tm.calc_layer_current(ecs_item, ptrain_data, ['GCL', 'INL'])
    with pytest.raises(ValueError):
        tm.calc_layer_current(ecs_item, ptrain_data, ['unknown'])

    # ...and that should be the same as `calc_layer_current`:
    ecm_by_hand = np.sum(ecs_item[1, :, np.newaxis] * ptrain_data, axis=0)
    ecm = tm.calc_layer_current(ecs_item, ptrain_data, ['GCL'])
    npt.assert_almost_equal(ecm, ecm_by_hand)


def test_Horsager2009():
    """Make sure the model can reproduce data from Horsager et al. (2009)

    Single-pulse data is taken from Fig.3, where the threshold current is
    reported for a given pulse duration and amplitude of a single pulse.
    We don't fit every data point to save some computation time, but make sure
    the model produces roughly the same values as reported in the paper for
    some data points.
    """

    def forward_pass(model, pdurs, amps):
        """Calculate model output based on a list of pulse durs and amps"""
        pdurs = np.array([pdurs]).ravel()
        amps = np.array([amps]).ravel()
        for pdur, amp in zip(pdurs, amps):
            in_arr = np.ones((2, 1))
            pt = p2p.stimuli.PulseTrain(model.tsample, amp=amp, freq=0.1,
                                        pulsetype='cathodicfirst',
                                        pulse_dur=pdur / 1000.0,
                                        interphase_dur=pdur / 1000.0)
            percept = model.model_cascade(in_arr, [pt.data], 'GCL', False)
            yield percept.data.max()

    def calc_error_amp(amp_pred, pdur, model):
        """Calculates the error in threshold current

        For a given data `pdur`, what is the `amp` needed for output `theta`?
        We're trying to find the current that produces output `theta`. Thus
        we calculate the error between output produced with `amp_pred` and
        `theta`.
        """
        theta_pred = list(forward_pass(model, pdur, amp_pred))[0]
        return np.log(np.maximum(1e-10, (theta_pred - model.theta) ** 2))

    def yield_fits(model, pdurs, amps):
        """Yields a threshold current by fitting the model to the data"""
        for pdur, amp in zip(pdurs, amps):
            yield scpo.fmin(calc_error_amp, amp, disp=0, args=(pdur, model))[0]

    # Data from Fig.3 in Horsager et al. (2009)
    pdurs = [0.07335, 0.21985, 0.52707, 3.96939]  # pulse duration in ms
    amps_true = [181.6, 64.7, 33.1, 14.7]  # threshold current in uA
    amps_expected = [201.9, 61.0, 29.2, 10.4]

    # Make sure our implementation comes close to ground-truth `amps`:
    # - Do the forward pass
    model = p2p.retina.Horsager2009(tsample=0.01 / 1000, tau1=0.42 / 1000,
                                    tau2=45.25 / 1000, tau3=26.25 / 1000,
                                    beta=3.43, epsilon=2.25, theta=110.3)
    amps_predicted = np.array(list(yield_fits(model, pdurs, amps_true)))

    # - Make sure predicted values still the same
    npt.assert_almost_equal(amps_expected, amps_predicted, decimal=0)


def test_Retina_Electrodes():
    logging.getLogger(__name__).info("test_Retina_Electrodes()")
    sampling = 1
    xlo = -2
    xhi = 2
    ylo = -3
    yhi = 3
    retina = p2p.retina.Grid(x_range=(xlo, xhi), y_range=(ylo, yhi),
                             sampling=sampling,
                             save_data=False)
    npt.assert_equal(retina.gridx.shape, ((yhi - ylo) / sampling + 1,
                                          (xhi - xlo) / sampling + 1))
    npt.assert_equal(retina.range_x, retina.gridx.max() - retina.gridx.min())
    npt.assert_equal(retina.range_y, retina.gridy.max() - retina.gridy.min())

    electrode1 = p2p.implants.Electrode('epiretinal', 1, 0, 0, 0)

    # Calculate current spread for all retinal layers
    retinal_layers = ['INL', 'OFL']
    cs = dict()
    ecs = dict()
    for layer in retinal_layers:
        cs[layer] = electrode1.current_spread(retina.gridx, retina.gridy,
                                              layer=layer)
        ecs[layer] = retina.current2effectivecurrent(cs[layer])

    electrode_array = p2p.implants.ElectrodeArray('epiretinal', [1, 1], [0, 1],
                                                  [0, 1], [0, 1])
    npt.assert_equal(electrode1.x_center,
                     electrode_array.electrodes[0].x_center)
    npt.assert_equal(electrode1.y_center,
                     electrode_array.electrodes[0].y_center)
    npt.assert_equal(electrode1.radius, electrode_array.electrodes[0].radius)
    ecs_list, cs_list = retina.electrode_ecs(electrode_array)

    # Make sure cs_list has an entry for every layer
    npt.assert_equal(cs_list.shape[-2], len(retinal_layers))
    npt.assert_equal(ecs_list.shape[-2], len(retinal_layers))

    # Make sure manually generated current spreads match object
    for i, e in enumerate(retinal_layers):
        # last index: electrode, second-to-last: layer
        npt.assert_equal(cs[e], cs_list[..., i, 0])


def test_brightness_movie():
    logging.getLogger(__name__).info("test_brightness_movie()")

    tsample = 0.075 / 1000
    tsample_out = 1.0 / 30.0
    s1 = p2p.stimuli.PulseTrain(freq=20, dur=0.5,
                                pulse_dur=.075 / 1000.,
                                interphase_dur=.075 / 1000., delay=0.,
                                tsample=tsample, amp=20,
                                pulsetype='cathodicfirst')

    implant = p2p.implants.ElectrodeArray('epiretinal', [1, 1], [0, 1], [0, 1],
                                          [0, 1])

    # Smoke testing, feed the same stimulus through both electrodes:
    sim = p2p.Simulation(implant, engine='serial')

    sim.set_optic_fiber_layer(x_range=[-2, 2], y_range=[-3, 3], sampling=1,
                              save_data=False)

    sim.set_ganglion_cell_layer('latest', tsample=tsample)

    logging.getLogger(__name__).info(" - PulseTrain")
    sim.pulse2percept([s1, s1], t_percept=tsample_out)


def test_ret2dva():
    # Below 15mm eccentricity, relationship is linear with slope 3.731
    npt.assert_equal(p2p.retina.ret2dva(0.0), 0.0)
    for sign in [-1, 1]:
        for exp in [2, 3, 4]:
            ret = sign * 10 ** exp  # mm
            dva = 3.731 * sign * 10 ** (exp - 3)  # dva
            npt.assert_almost_equal(p2p.retina.ret2dva(ret), dva,
                                    decimal=3 - exp)  # adjust precision


# This function is deprecated
def test_micron2deg():
    npt.assert_almost_equal(p2p.retina.micron2deg(0.0), 0.0)
    npt.assert_almost_equal(p2p.retina.micron2deg(280.0), 1.0)


def test_dva2ret():
    # Below 50deg eccentricity, relationship is linear with slope 0.268
    npt.assert_equal(p2p.retina.dva2ret(0.0), 0.0)
    for sign in [-1, 1]:
        for exp in [-2, -1, 0]:
            dva = sign * 10 ** exp  # deg
            ret = 0.268 * sign * 10 ** (exp + 3)  # mm
            npt.assert_almost_equal(p2p.retina.dva2ret(dva), ret,
                                    decimal=-exp)  # adjust precision


# This function is deprecated
def test_deg2micron():
    npt.assert_almost_equal(p2p.retina.deg2micron(0.0), 0.0)
    npt.assert_almost_equal(p2p.retina.deg2micron(1.0), 280.0)


def test_jansonius2009():
    # With `rho` starting at 0, all axons should originate in the optic disc
    # center
    for phi0 in [-135.0, 66.0, 128.0]:
        for loc_od in [(15.0, 2.0), (-15.0, 2.0), (-4.2, -6.66)]:
            ax_pos = p2p.retina.jansonius2009(phi0, n_rho=100,
                                              rho_range=(0.0, 45.0),
                                              loc_od=loc_od)
            npt.assert_almost_equal(ax_pos[0, 0], loc_od[0])
            npt.assert_almost_equal(ax_pos[0, 1], loc_od[1])

    # These axons should all end at the meridian
    for sign in [-1.0, 1.0]:
        for phi0 in [110.0, 135.0, 160.0]:
            ax_pos = p2p.retina.jansonius2009(sign * phi0, n_rho=501,
                                              rho_range=(0.0, 45.0))
            print(ax_pos[-1, :])
            npt.assert_almost_equal(ax_pos[-1, 1], 0.0, decimal=1)

    # `phi0` must be within [-180, 180]
    for phi0 in [-200.0, 181.0]:
        with pytest.raises(ValueError):
            p2p.retina.jansonius2009(phi0)

    # `n_rho` must be >= 1
    for n_rho in [-1, 0]:
        with pytest.raises(ValueError):
            p2p.retina.jansonius2009(0.0, n_rho=n_rho)

    # `rho_range` must have min <= max
    for lorho in [-200.0, 90.0]:
        with pytest.raises(ValueError):
            p2p.retina.jansonius2009(0.0, rho_range=(lorho, 45.0))
    for hirho in [-200.0, 40.0]:
        with pytest.raises(ValueError):
            p2p.retina.jansonius2009(0.0, rho_range=(45.0, hirho))


def test_grow_axon_bundles():
    for n_axons in [-1, 0]:
        with pytest.raises(ValueError):
            p2p.retina.grow_axon_bundles(n_axons)
    for n_rho in [-1, 0]:
        with pytest.raises(ValueError):
            p2p.retina.grow_axon_bundles(1, n_rho=n_rho)
    for lophi in [-200.0, 90.0, 200.0]:
        with pytest.raises(ValueError):
            p2p.retina.grow_axon_bundles(1, phi_range=(lophi, 85.0))
    for hiphi in [-200.0, 90.0, 200.0]:
        with pytest.raises(ValueError):
            p2p.retina.grow_axon_bundles(1, phi_range=(95.0, hiphi))

    n_rho = 100
    phi_range = (-180.0, 180.0)
    for n_axons in [1, 5, 11]:
        phi = np.linspace(phi_range[0], phi_range[1], n_axons)
        axons = p2p.retina.grow_axon_bundles(n_axons, phi_range=phi_range,
                                             n_rho=n_rho)
        npt.assert_equal(len(axons), n_axons)
        for ax, phi0 in zip(axons, phi):
            # Every axon is at most a `n_rho` x 2 matrix, where every row has
            # (x, y). Number of rows might be < `n_rho` if axon crossed
            # meridian.
            npt.assert_equal(ax.shape[1], 2)
            npt.assert_equal(ax.shape[0] <= n_rho, True)
            ax_pos = p2p.retina.jansonius2009(phi0, n_rho=n_rho)
            npt.assert_almost_equal(ax_pos[:, 0], ax[:, 0])
            npt.assert_almost_equal(ax_pos[:, 1], ax[:, 1])


def test_find_closest_axon():
    axon_bundles = p2p.retina.grow_axon_bundles(10)
    for idx, ax in enumerate(axon_bundles):
        # Each axon bundle should be closest to itself
        closest = p2p.retina.find_closest_axon(ax[-1, :], axon_bundles)
        npt.assert_almost_equal(closest, ax[-1:0:-1, :])


def test_assign_axons():
    axon_bundles = p2p.retina.grow_axon_bundles(10)
    xg, yg = np.meshgrid([-1, 0, 1], [-1, 0, 1], indexing='xy')
    assigned = p2p.retina.assign_axons(xg, yg, axon_bundles)
    for x, y, ax in zip(xg.ravel(), yg.ravel(), assigned):
        closest = p2p.retina.find_closest_axon((x, y), axon_bundles)
        npt.assert_almost_equal(ax, closest)
