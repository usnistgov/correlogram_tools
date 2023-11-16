import numpy as np
import scipy.special as sp

from bumps.fitproblem import FitProblem
from sasmodels.data import Data1D
from sasmodels import bumps_model


def hankel(ac_length, q, Iq):
    
    """
    Returns the Hankel transformation of the scattering cross section, I(q), as G(ac_length) - G(0).
    
    The projection function can be converted to the dark field intensity collected on the INFER instrument by:
         
         DF = exp[wavelength**2 * thickness * (G(ac_length) - G(0))]
             
    This function utilizes the Hankel transformation approach implemented in the sasmodels code at:
    https://github.com/SasView/sasmodels/blob/master/sasmodels/sesans.py
    Some changes have been made to account for the scaling/normalization with INFER terms.
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, units Angstroms
    q : array_like
        scattering vector, units 1/Angstrom
    Iq : array_like
        scattering cross section, I(q), calculated at every q-value, absolute units 1/cm
                    
    Returns
    -------
    G : array, length of ac_length
        projection function as G(ac_length) - G(0)
    
    """

    dq = np.diff(q, prepend=2*q[0]-q[1])  # prepend will ensure that q[1] - q[0] gets inserted at beginning of dq
    
    # Hankel transformation
    G0 = np.dot(q*dq, Iq)
    G = np.dot((sp.j0(np.outer(q, ac_length))*(q*dq).reshape((-1, 1))).T, Iq)
    
    return (G - G0) / (2 * np.pi)


def visibility(ac_length, q, Iq, wavelength, thickness):
    
    """
    Returns the loss in visibility using the projection function (G(ac_length)-G(0)),
    as determined by the Hankel transformation on the scattering cross section, I(q).
        
    The projection function can be converted to the dark field intensity collected on the INFER instrument by:
         
        V_s/V_o = exp[wavelength**2 * thickness * (G(ac_length) - G(0))]
             
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, Angstroms
    q : array_like
        scattering vector, units 1/Angstrom
    Iq : array_like
        scattering cross section, I(q), calculated at every q-value, absolute units 1/cm
    wavelength : real or array_like
        wavelength of the source radiation in INFER measurement, Angstroms
        the dark field intensity can be determined at a single wavelength or
        at a unique wavelength for each autocorrelation length
        if array_like, length must match length of ac_length array
    thickness : real or array_like
        thickness of the sample, centimeter
        the dark field intensity can be determined at a single thickness or
        across a range of thicknesses
                    
    Returns
    -------
    visibility : array, 2D array, len(ac_length) x len(thickness)
        loss in visibility as a function of ac_length and thickness
        first dimension corresponds to ac_length (dependent on wavelength)
        second dimension corresponds to thickness
    
    """

    if not np.isscalar(wavelength) and len(wavelength) != len(ac_length):
        raise Exception(f"Length of wavelength is not a scalar and does not match length of autocorrelation length.")

    # generating normalized projection function using Hankel transformation
    G = hankel(ac_length, q, Iq)
    
    # scale by appropriate wavelength
    G = np.array(wavelength)**2 * G
    
    # calculating dark field
    vis = np.exp(np.outer(G, np.array(thickness)))

    return vis


def dark_field(ac_length, q, Iq, wavelength, thickness):
    
    """
    Returns the dark_field based on the dark field intensity, determined by:
        
        DF = -ln(visibility)
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, Angstroms
    q : array_like
    scattering vector, units 1/Angstrom
    Iq : array_like
        scattering cross section, I(q), calculated at every q-value, absolute units 1/cm
    wavelength : real or array_like
        wavelength of the source radiation in INFER measurement, Angstroms
        the dark field intensity can be determined at a single wavelength or
        at a unique wavelength for each autocorrelatin length
        if array_like, length must match length of ac_length array
    thickness : real or array_like
        thickness of the sample, centimeter
        the dark field intensity can be determined at a single thickness or
        across a range of thicknesses
                    
    Returns
    -------
    dark_field : array, 1D or 2D array
        dark_field intensity as a function of ac_length and thickness
        first dimension corresponds to ac_length (dependent on wavelength)
        second dimension corresponds to thickness

    """
    
    # generating dark field intensity
    vis = visibility(ac_length, q, Iq, wavelength, thickness)
    
    # calculating dark_field
    DF = -np.log(vis)
    
    return DF


def normalized_amplitude(vis, As, Ao):
    
    """
    Returns the simulated normalized phase step amplitude defined as Bs/Bo, where Bs is the phase step amplitude of the
    sample and Bo is the phase step amplitude of the open beam. This is determined by using the dark field intensity:
        
        vis = (Bs/Bo)/(As/Ao)
        
    where As/Ao is the normalized transmission (phase step mean).
    
    Parameters
    ----------
    vis : real or array_like
        loss in visibility at each autocorrelation length
    As : real
        sample transmission
    Ao : real
        open beam transmission (no sample in beam path)
                    
    Returns
    -------
    norm_amp : array, length of DF
        normalized phase step amplitude at each autocorrelation length
    
    """
    
    norm_amp = vis * (As/Ao)
    
    return norm_amp


def get_qIq(ac_length, model, num_q=10000, q_logstep=0.000125):
    
    """
    Returns the scattering vector, q, and modeled scattering cross section, I(q), required for transformations to
    INFER-relevant terms, including the Hankel transformation and generation of dark field intensity, dark_field, etc.
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, Angstroms
    model : sasmodels.bumps_model.Model
        includes all required parameters and kernel to define the scattering cross section, I(q)
        NOTE: the 'scale' parameter for I(q) should be equal to phi*(1-phi) where phi is volume fraction, and
        this is different than the standard SANS procedure that assumes scale=volume fraction under absolute scale
                    
    Optional Parameters TODO: one of these two parameters will need to be removed once we determine proper approach to q
    -------------------
    num_q : int, default is 10000
        length of q to generate
    q_logstep : float, default is 0.000125
        This is the log spacing for q that results in 8000 points per decade.

                    
    Returns
    -------
    q : array_like
        scattering vector, units 1/Angstrom
    Iq : array_like
        scattering cross section, I(q), calculated at every q-value, absolute units 1/cm
    
    """
    # generating the q-range and preparing dq for the Hankel transform
    # this will be modified to utilize the SasView/sasmodels implementation until we can mask q_max for INFER properly
    q_min = 0.1*2*np.pi/(np.max([100, len(ac_length)])*np.max(ac_length))
    # q_max = 2*np.pi/np.min(np.diff(ac_length))
    # q_max = 2 * np.pi / (ac_length[1] - ac_length[0])
    q_max = 2 * np.pi  # changed in case autocorrelation length sampling in simulation is low

    # q = np.logspace(np.log10(q_min), np.log10(q_max), num=num_q)
    q = np.exp(np.arange(np.log(q_min), np.log(q_max), step=q_logstep))

    # setup bumps FitProblem to generate I(q)
    data = Data1D(x=q, y=np.ones_like(q, dtype=float), dy=np.ones_like(q, dtype=float)*0.001)
    experiment = bumps_model.Experiment(data=data, model=model)
    problem = FitProblem(experiment)
    Iq = problem.fitness.theory()
    
    return q, Iq


def sim_visibility(ac_length, model, wavelength, thickness, num_q=10000):

    """
    Returns the simulated dark field intensity using the projection function (G(ac_length)-G(0)),
    as determined by the Hankel transformation on the modeled scattering cross section, I(q).
        
    The projection function can be converted to the dark field intensity collected on the INFER instrument by:
         
        vis = exp[wavelength**2 * thickness * (G(ac_length) - G(0))]
             
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, Angstroms
    model : sasmodels.bumps_model.Model
        includes all required parameters and kernel to define the scattering cross section, I(q)
        NOTE: the 'scale' parameter for I(q) should be equal to phi*(1-phi) where phi is volume fraction, and
        this is different from the standard SANS procedure that assumes scale=volume fraction under absolute scale
    wavelength : real or array_like
        wavelength of the source radiation in INFER measurement, Angstroms
        the dark field intensity can be determined at a single wavelength or
        at a unique wavelength for each autocorrelation length
        if array_like, length must match length of ac_length array
    thickness : real or array_like
        thickness of the sample, centimeter
        the dark field intensity can be determined at a single thickness or
        across a range of thicknesses
                    
    Optional Parameters
    -------------------
    num_q : int, default is 10000
        number of points of q to generate when retrieving I(q) vs q from the model
                    
    Returns
    -------
    visibility : array, 1D or 2D array
        loss in visibility as a function of ac_length and thickness
        first dimension corresponds to ac_length (dependent on wavelength)
        second dimension corresponds to thickness
                    
    """
    # calculating appropriate scattering vector and modeled scattering cross section
    q, Iq = get_qIq(ac_length, model, num_q=num_q)
    
    # simulated dark field
    vis = visibility(ac_length, q, Iq, wavelength, thickness)
    
    return vis


def sim_dark_field(ac_length, model, wavelength, thickness, num_q=10000):

    """
    Returns the dark_field based on the simulated dark field intensity, determined by:
        
        DF = -ln(vis)
    
    Parameters
    ----------
    ac_length : array_like
        autocorrelation length, Angstroms
    model : sasmodels.bumps_model.Model
        includes all required parameters and kernel to define the scattering cross section, I(q)
        NOTE: the 'scale' parameter for I(q) should be equal to phi*(1-phi) where phi is volume fraction, and
        this is different from the standard SANS procedure that assumes scale=volume fraction under absolute scale
    wavelength : real or array_like
        wavelength of the source radiation in INFER measurement, Angstroms
        the dark field intensity can be determined at a single wavelength or
        at a unique wavelength for each autocorrelation length
        if array_like, length must match length of ac_length array
    thickness : real or array_like
        thickness of the sample, centimeter
        the dark field intensity can be determined at a single thickness or
        across a range of thicknesses
                    
    Optional Parameters
    -------------------
    num_q : int, default is 10000
        number of points of q to generate when retrieving I(q) vs q from the model
                    
    Returns
    -------
    dark_field : array, 1D or 2D array
        dark_field intensity as a function of ac_length and thickness
        first dimension corresponds to ac_length (dependent on wavelength)
        second dimension corresponds to thickness
    
    """
    
    # calculating appropriate scattering vector and modeled scattering cross section
    q, Iq = get_qIq(ac_length, model, num_q=num_q)
    
    # simulated dark_field
    df = dark_field(ac_length, q, Iq, wavelength, thickness)
    
    return df
