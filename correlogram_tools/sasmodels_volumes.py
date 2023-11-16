"""
Define volume fraction of each component in multicomponent models.
"""
import numpy as np

# For a two-component model only need to know the volume fraction, which is
# equal ot the scale. (Some models define an explicit volume fraction component,
# which applies an additional scale.) For other models, need the volume of each
# separate component independently, with components named for the corresponding
# sld parameter. These models will need specialized code because the sasmodels
# api does not provide the internal component volumes.
#
# Hollow objects are special because they only have a shell component named
# sld but no core component. The volume fraction taken up by the particles
# includes the hollow core, so the volume fraction of solvent needs to be
# increased by the core fraction. Note: vesicle model is not a hollow sphere
# since the volume fraction is volume fraction of surfactant not the volume
# fraction occupied by vesicles.
# CMW 2023-11-14: The hollow_cylinder model defines the volume fraction or scale
# parameter as the volume fraction of the shell only.

# TODO: Is fuzzy_sphere homogeneous?
# TODO: Do models without slds still have volume fraction?
# TODO: no sld: be_polyelectrolyte mass/surface fractal, polygauss coil, star polymer
# TODO: missing: core_shell_*, hollow_*, lamellar_hg*, polymer_micelle, raspberry, stacked_disk, adsorbed_layer
# TODO: onion and spherical_sld have continous changes
# TODO: Doesn't support polydispersity
# TODO: Can we avoid explicitly listing the two-phase models?
# TODO: Add a check that the sum of all components including solvent is 1.
# TODO: Add an explicit list of unsupported models?

# Homogeneous shapes with a single phase in the shape
HOMOGENEOUS_SHAPES = set("""
barbell
bcc_paracrystal
capped_cylinder
cylinder
ellipsoid
elliptical_cylinder
fc_paracrystal
flexible_cylinder
flexible_cylinder_elliptical
fuzzy_sphere
lamellar
lamellar_stack_paracrystal
linear_pearls
parallelepiped
pearl_necklace
pringle
rectangular_prism
sc_paracrystal
sphere
triaxial_ellipsoid
hollow_cylinder
""".split())

# Additional two-phase systems that include an explicit volume fraction parameter
VOLFRACTIONS = set("""
fractal
fractal_core_shell
multilayer_vesicle
vesicle
""".split())

TWO_PHASE_MODELS = HOMOGENEOUS_SHAPES | VOLFRACTIONS

# TODO: return all components at once rather than a separate call for each.
# Since we need to compute the volume of all components anyway to determine the
# fraction this leads to a lot of work being thrown away.


def get_volume_fractions(sasmodel_name, prefix, sld_param, parameters: dict) -> list:
    """returns the volume fractions for the sld parameter (sld_param)"""

    # Filter parameters based on the provided prefix of the model. For example,
    # in a sphere+sphere model there will be parameters for A_sld and B_sld, but
    # we only want the parameters for A_ without the A_ prefix.
    if len(prefix) > 0:
        parameters = {
            key[len(prefix):]: value
            for (key, value) in parameters.items()
            if key.startswith(prefix)
        }

    # Convert to numpy vectors so we can do math on lists
    parameters = {k: np.array(v) for k, v in parameters.items()}

    # fractal core-shell sphere uses both volfraction and scale parameters to
    # set the proportions.
    vf = parameters["scale"]
    if sasmodel_name in VOLFRACTIONS:
        vf *= parameters["volfraction"]

    # Check if we have a specialized implementation for the particular model in
    # this module, and return its fractional part
    if sasmodel_name in globals():
        parts = globals()[sasmodel_name](parameters)
        total = sum(v for v in parts.values())
        # Extra work to accommodate hollow cores
        if sld_param == "sld_solvent":
            return list(1 - vf * total)
        if sld_param not in parts:
            raise KeyError(f"{sasmodel_name} does not use {sld_param}")
        return list(vf * parts[sld_param])

    # Single component system. Return volume fraction based on scale.
    if sasmodel_name in TWO_PHASE_MODELS:
        if sld_param == "sld_solvent":
            return list(1 - vf)
        return list(vf)  # sld

    raise NotImplementedError(f"{sasmodel_name} does not define component fractions")


def binary_hard_sphere(parameters):
    # Don't care about the radii since we already have the relative volume fraction
    vf_sm, vf_lg = parameters["volfraction_sm"], parameters["volfraction_lg"]
    return dict(sld_sm=vf_sm, sld_lg=vf_lg)


def core_multi_shell(parameters):
    radius = parameters["radius"]
    volume = 4/3*np.pi*radius**3
    result = {"sld_core": volume}
    shells = int(parameters["n"][0])
    for k in range(1, shells+1):
        rnext = radius + parameters[f"thickness{k}"]
        vnext = 4/3*np.pi*rnext**3
        result[f"sld{k}"] = vnext - volume
        radius, volume = rnext, vnext
    total = sum(result.values())
    return {k: v/total for k, v in result.items()}


def core_shell_cylinder(parameters):
    """returns relative volume fractions of the cylinder core and shell"""
    length, radius, thickness = parameters["length"], parameters["radius"], parameters["thickness"]
    inner = np.pi*radius**2*length
    outer = np.pi*(radius+thickness)**2*(length+2*thickness)
    core = inner/outer
    shell = (outer-inner)/outer
    return dict(sld_core=core, sld_shell=shell)


def core_shell_ellipsoid(parameters):
    re, core_ratio = parameters["radius_equat_core"], parameters["x_core"]
    rp = re*core_ratio
    te, shell_ratio = parameters["thick_shell"], parameters["x_polar_shell"]
    tp = te*shell_ratio
    inner = 4/3*np.pi*re**2*rp
    outer = 4/3*np.pi*(re+te)**2*(rp+tp)
    return dict(sld_core=inner/outer, sld_shell=(outer-inner)/outer)


def core_shell_sphere(parameters):
    radius, thickness = parameters["radius"], parameters["thickness"]
    inner = 4/3*np.pi*radius**3
    outer = 4/3*np.pi*(radius+thickness)**3
    core = inner/outer
    shell = (outer-inner)/outer
    return dict(sld_core=core, sld_shell=shell)


def fractal_core_shell(parameters):
    # fractal core-shell has the same radius, thickness parameters as core-shell
    return core_shell_sphere(parameters)

# CMW 2023-11-14 The holldw_cylinder model defines the scale as the volume fraction of shell only
# def hollow_cylinder(parameters):
#     length, radius, thickness = parameters["length"], parameters["radius"], parameters["thickness"]
#     inner = np.pi*radius**2*length
#     outer = np.pi*(radius+thickness)**2*length
#     # Hollow objects need an adjustment to solvent fraction
#     return dict(sld_solvent=inner, sld=outer-inner)
