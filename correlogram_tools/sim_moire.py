import numpy as np
from numpy import pi, sqrt, sin, cos, isnan, arctan2, log
import cv2

from .sim_images import xi_encode, imsave


def sim_moire(experiment, save_raw=False, ext='tif', verbose=True):
    """
    Simulate a moiré pattern for the experiment.

    Not yet a complete simulation:
    * visibility should be a function of period and wavelength
    * visibility could vary across the beam (e.g., if the phase gratings are tilted relative to one another)
    * no moiré rotation with period (source gratings may be misaligned)
    * no salt and pepper noise, bad pixels or other detector artifacts
    * no beam profile giving per pixel intensity distribution with wavelength
    * no dark current estimate
    * no hydrogen scatter or background level
    * no "ghosting" from previous measurements
    * no detector point spread function
    * no wavelength dispersion or angular divergence
    """
    if experiment.H0 is None or experiment.H1byH0 is None:
        experiment.generate_simulation_images()

    H0, H1byH0 = experiment.H0, experiment.H1byH0
    # print("H0, H1/H0", H0.shape, H1byH0.shape)
    raw_path = experiment.export_path / "raw"
    if save_raw:
        raw_path.mkdir(parents=True, exist_ok=True)
    recon_path = experiment.export_path / "recon"
    recon_path.mkdir(parents=True, exist_ok=True)

    config = experiment.config
    n_phase = config["instrument"]["n_phase_steps"]  # number of phase steps
    n_periods = config["instrument"]["n_phase_step_periods"]  # stepping over more than one period
    delta_phi = 2*pi*n_periods/n_phase

    # collecting noise arguments required for the recongeneration package
    # step_sigma = config["sim_noise"]["phase_step_sigma"]  # phase step jitter, feature currently turned off
    moire_mean = config["sim_noise"]["moire_mean"]  # average exposure per pixel
    moire_vis = config["sim_noise"]["moire_vis"]  # visibility of moiré pattern
    moire_amp = moire_mean * moire_vis
    noise_mean = config["sim_noise"]["noise_mean"]
    noise_std = sqrt(config["sim_noise"]["noise_var"])
    peak = moire_mean + moire_amp + noise_mean + 3*noise_std

    Z = experiment.measurements_z  # sample distance [mm]
    distance = config["instrument"]["interferometer_length"]
    aperture = config["instrument"].get("aperture_type", "pinhole")
    if aperture not in ("pinhole", "slit"):
        raise ValueError(f"Expected aperture_type: pinhole|slit but got {aperture}")
    dx = config["instrument"]["slit_aperture_x"]  # aperture size in x [cm]
    dy = config["instrument"]["slit_aperture_y"]  # aperture size in y [cm]
    pixelsz = config["instrument"]["x_pixel_pitch"]  # effective pixel size [um]
    autocorrelationlength = experiment.measurements_xi  # Calculated [um]
    moireperiod = experiment.measurements_moire * 1000  # moire fringe period [um]
    wavelength = experiment.measurements_wavelength  # wavelength [nm]
    p = moireperiod/pixelsz  # number of pixels for 1 period of moiré fringe

    blur_method = geoblur_pinhole if aperture == "pinhole" else geoblur_slit
    periods = set()
    file_index = 1
    ny, nx, n_points = H0.shape
    noise = np.empty((ny, nx*n_phase), dtype='float32')
    for k in range(n_points):
        if k % 5 == 0:
            print(f"Raw reconstruction {k+1} of {n_points}")
        # Apply geometric blur. This needs to happen in the space where counts
        # are additive since it represents a mixing of paths through the sample.
        # In this case we are blurring "I = H0 + H1 (cos(w) + 1)" so blur has
        # to happen in H0 and H1, and not in H1byH0.
        # Note: not actually magnifying and shrinking so this doesn't capture
        # the messiness on the edges of the detector.
        H0_k = blur_method(H0[..., k], distance, dx, dy, pixelsz, Z[k]/1000)
        H1_k = blur_method(H1byH0[..., k]*H0[..., k], distance, dx, dy, pixelsz, Z[k]/1000)
        H1byH0_k = H1_k / H0_k
        H0_k[isnan(H0_k)] = 0
        H1byH0_k[isnan(H1byH0_k)] = 0
        H1_k = H1byH0_k * H0_k

        # Suppress noise (for code testing purposes)
        # noise_std = step_sigma = 0

        # Generate raw frames
        ny, nx = H0_k.shape
        x = 2*pi*np.arange(0, nx)
        # TODO: add phase estimate to reconstruction. For now step_sigma should always be zero.
        step_sigma = 0  # ensure zero until phase estimate is added
        jitter = step_sigma*np.random.randn(n_phase).astype(np.float32)
        wave = np.empty((1, nx, n_phase), dtype=np.float32)
        for step in range(n_phase):
            wave[..., step] = sin(x/p[k] + delta_phi*(step + jitter[step]))

        # TODO: only need one open beam per period, with unique jitter in the phase step
        sim_open = moire_mean + moire_amp*wave
        sim_samp = moire_mean*H0_k[:, :, None] + moire_amp*wave*H1_k[:, :, None]
        # TODO: use poisson noise instead of flat gaussian
        # TODO: use GPU for image calculations (randn alone is half the run time)
        # sim_open = sim_open + noise_mean + np.zeros((ny, nx, n_phase), dtype=np.float32)
        # sim_samp = sim_samp + noise_mean
        # Note: using "open = open + noise" because open is (1 X nx X n_phase)
        # but "sample += noise" because sample is (ny X nx X n_phase)
        cv2.randn(noise, noise_mean, noise_std)
        sim_open = sim_open + noise.reshape(ny, nx, n_phase)
        cv2.randn(noise, noise_mean, noise_std)
        sim_samp += noise.reshape(ny, nx, n_phase)

        period_k = int(moireperiod[k])
        if save_raw:
            if period_k not in periods:
                periods.add(period_k)
                for step in range(n_phase):
                    stem = xi_encode("open",
                                     period=period_k, wavelength=wavelength[k], phase=step, increment=file_index)
                    imsave(sim_open[:, :, step], raw_path / f"{stem}.{ext}", peak=peak)
                    file_index += 1
            for step in range(n_phase):
                stem = xi_encode("samp",
                                 period=period_k, z=Z[k], wavelength=wavelength[k], phase=step, increment=file_index)
                imsave(sim_samp[:, :, step], raw_path / f"{stem}.{ext}", peak=peak)
                file_index += 1

        H0_r, H1_r, H1byH0_r, H1dark_r, phi_r = reconstruction(sim_open, sim_samp, n_periods)

        stem = xi_encode("samp", autocorrelationlength[k], period=period_k, z=Z[k], wavelength=wavelength[k])
        imsave(H0_r, recon_path / f"{stem}_H0.{ext}", peak=1.1)
        # imsave(H1_r, recon_path / f"{stem}_H1.{ext}", peak=1.1)
        imsave(H1byH0_r, recon_path / f"{stem}_H1byH0.{ext}", peak=1.1)


def geoblur_pinhole(
    image: np.ndarray,
    aperture_distance: float,  # m
    aperture_x: float,  # cm
    aperture_y: float,  # cm (ignored)
    pixel_size: float,  # μm/px
    sample_distance: float,  # m (positive or negative)
):
    L, D, pitch, Z = aperture_distance, aperture_x, pixel_size, abs(sample_distance)

    # magnification factor M = L m / (L-Z) m
    # lambda_g px = D/2 cm • Z m / ((L-Z) m • pitch μm/px • 10⁻⁴ cm/μm)
    # = [ D/2 • Z/(L-Z) • 10⁴/pitch ] px
    # Implicit rescale by 1/M after blur is equivalent to blur/M
    # lambda_g/M = [ D/2 • Z/L • 10⁴/pitch ] px
    lambda_g = D/2*Z/L*1e4/pitch  # px
    r = int(np.floor(lambda_g))
    radius = int(np.round(lambda_g))
    width = 2*r + 1
    kernel = np.zeros((width, width), dtype='float32')
    # circle(img, center=(x,y), radius, color, linewidth=-1 for filled)
    cv2.circle(kernel, (r, r), radius, 255, -1)
    kernel /= np.sum(kernel)

    blurred = np.empty_like(image)
    # filter2d(src, dest, depth, kernel)
    cv2.filter2D(image, -1, kernel, dst=blurred, borderType=cv2.BORDER_CONSTANT)

    return blurred


def geoblur_slit(
    image: np.ndarray,
    aperture_distance: float,  # m
    aperture_x: float,  # cm
    aperture_y: float,  # cm (ignored)
    pixel_size: float,  # μm/px
    sample_distance: float,  # m (positive or negative)
):
    L, Dx, Dy, pitch, Z = aperture_distance, aperture_x, aperture_y, pixel_size, abs(sample_distance)

    # See comment in geoblur_pinhole for equation and units
    w = int(np.round(Dx/2*Z/L*1e4/pitch))  # px
    h = int(np.round(Dy/2*Z/L*1e4/pitch))  # px
    # print(f"blur {w=} {h=}")

    return cv2.blur(image, (w, h))


def reconstruction(openbeam, sample, n_periods):
    # TODO: Use full reconstruction from our NIF reduction code
    # Note: not fitting the phase steps for each frame.
    m, n, steps = openbeam.shape
    # print("open, samp", openbeam.shape, sample.shape, n_periods)
    # PAK: Unlike YK code, the pps parameter is inside sin/cos expression
    phi = 2*pi*n_periods*np.arange(steps)/steps
    B = np.ones((steps, 3), np.float32)
    B[:, 1] = sin(phi)
    B[:, 2] = cos(phi)
    # G = (B'*B)\B'
    # TODO: check dims; they are probably wrong
    # CMW: 2023-11-15 Dimensions appear to track correctly through this section.
    G = np.linalg.pinv(B)  # pseudoinverse of B[..., M, N]
    imgopen = np.zeros((m, n, 3), np.float32)
    for i in range(steps):
        imgopentemp = medfilt2(openbeam[:, :, i])
        imgopen += G[:, i][None, None, :] * imgopentemp[:, :, None]
    ampopen = sqrt(imgopen[:, :, 1]**2 + imgopen[:, :, 2]**2)
    phiopen = arctan2(imgopen[:, :, 2], imgopen[:, :, 1])

    imgsamp = np.zeros((m, n, 3), np.float32)
    for i in range(steps):
        imgsamptemp = medfilt2(sample[:, :, i])
        imgsamp += G[:, i][None, None, :] * imgsamptemp[:, :, None]
    ampsamp = sqrt(imgsamp[:, :, 1]**2 + imgsamp[:, :, 2]**2)
    phisamp = arctan2(imgsamp[:, :, 2], imgsamp[:, :, 1])

    h0 = imgsamp[:, :, 0] / imgopen[:, :, 0]
    h1 = ampsamp / ampopen
    h1byh0 = h1/h0
    h1dark = -log(h1byh0)  # TODO: confirm nomenclature with full reconstruction from NIF reduction code
    phi01 = phisamp - phiopen
    return h0, h1, h1byh0, h1dark, phi01


def medfilt2(buf, size=(3, 3), padopt='symmetric'):
    if padopt != 'symmetric':
        raise ValueError("padopt only implements 'symmetric' for now")
    if size[0] != size[1]:
        raise ValueError("only square filters for now")
    if size[0] % 2 == 0:
        raise ValueError("only odd size filters for now")
    if buf.dtype == np.float64:
        raise ValueError("only [u]int[8|16] and float32 supported")

    return cv2.medianBlur(buf, size[0])
