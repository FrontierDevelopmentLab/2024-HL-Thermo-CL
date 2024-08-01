import torch

def exponential_atmosphere(altitudes):    
    """
    Compute the density of the atmosphere using the piecewise exponential model. 
    Reference: Vallado, D. A. (2013). Fundamentals of astrodynamics and applications (4th Edition). Microcosm Press.

    Parameters:
        - altitudes (`torch.Tensor`): the altitudes at which to compute the density, [km].

    Returns:
        - rhos (`torch.Tensor`): the density of the atmosphere at the given altitudes
    """
    # Base altitude for the exponential atmospheric model, [km]
    zb = torch.tensor([0., 25, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120,
      130, 140, 150, 180, 200, 250, 300, 350, 400, 450,
      500, 600, 700, 800, 900, 1000])

    zb_expand = zb.clone().detach()
    # Set the two endpoints of base altitude to a small enough and a large enough value respectively for extrapolation calculations.
    zb_expand[0],zb_expand[-1] = -torch.inf,torch.inf

    # Nominal density for the exponential atmospheric model, [kg/m³]
    rhob = torch.tensor([1.225, 3.899e-2, 1.774e-2, 3.972e-3, 1.057e-3,
        3.206e-4, 8.770e-5, 1.905e-5, 3.396e-6, 5.297e-7,
        9.661e-8, 2.438e-8, 8.484e-9, 3.845e-9, 2.070e-9,
        5.464e-10, 2.789e-10, 7.248e-11, 2.418e-11,
        9.518e-12, 3.725e-12, 1.585e-12, 6.967e-13,
        1.454e-13, 3.614e-14, 1.170e-14, 5.245e-15,3.019e-15])

    # Scale height for the exponential atmospheric model, [km]
    ZS = torch.tensor([7.249, 6.349, 6.682, 7.554, 8.382, 7.714, 6.549,
      5.799, 5.382, 5.877, 7.263, 9.473, 12.636, 16.149,
      22.523, 29.740, 37.105, 45.546, 53.628, 53.298,
      58.515, 60.828, 63.822, 71.835, 88.667, 124.64,181.05, 268.00])

    bin_indices = torch.searchsorted(zb, altitudes, right=True) - 1

    rhos = rhob[bin_indices]*torch.exp(-(altitudes-zb_expand[bin_indices])/ZS[bin_indices])      
    return rhos