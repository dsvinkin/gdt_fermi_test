"""
Script uses GBM data tools 1.1.1.

https://fermi.gsfc.nasa.gov/ssc/data/analysis/gbm/gbm_data_tools/gdt-docs/notebooks/PhaExport.html
"""

import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt 
import numpy as np


from gbm.data import TTE
from gbm.data import RSP

from gbm.binning.unbinned import bin_by_time

from gbm.plot import Lightcurve, Spectrum

# the background fitter interface
from gbm.background import BackgroundFitter

# our fitting algorithm
from gbm.background.binned import Polynomial


def plot_lc(lc_data, fig_name, str_title, y_lim=None, bg_data=None, src_lc=None, x_range=None):
    """
    https://fermi.gsfc.nasa.gov/ssc/data/analysis/gbm/gbm_data_tools/gdt-docs/api/api-plot.html?highlight=lightcurve#gbm.plot.Lightcurve
  

    Some features 
    # toggle off the errorbars
    lcplot.errorbars.toggle()
    
    # change lightcurve plot properties
    lcplot.lightcurve.color = 'purple'
    lcplot.lightcurve.linewidth = 1
    lcplot.lightcurve.linestyle = ':'

    lc_select = phaii.to_lightcurve(time_range=(362., 385.0))
    lcplot.add_selection(lc_select)
    """

    # plot a lightcurve with our background fit included
    lcplot = Lightcurve(data=lc_data, background=bg_data)

    if src_lc is not None and x_range is not None:
        lcplot.add_selection(src_lc)
        lcplot.xlim = x_range
    
    if y_lim is not None: 
        lcplot.ylim = y_lim
    
    lcplot.ax.set_title(str_title)

    print(f'Saving {fig_name}.png')
    plt.savefig(f'{fig_name}.png')
    plt.close()

def plot_spectrum(spec_data, spec_bkgd, spec_selection):
    """
    https://fermi.gsfc.nasa.gov/ssc/data/analysis/gbm/gbm_data_tools/gdt-docs/api/api-plot.html?highlight=lightcurve#spectrum
    """

    specplot = Spectrum(data=spec_data, background=spec_bkgd)
    specplot.add_selection(spec_selection)

def fit_bg(tte, time_res, bkgd_times, poly_order):

    phaii = tte.to_phaii(bin_by_time, time_res, time_ref=0.0)

    backfitter = BackgroundFitter.from_phaii(phaii, Polynomial, time_ranges=bkgd_times)
    
    # once initialized, run the fit - in this case, we use a fit the background as a 1st degree polynomial
    backfitter.fit(order=poly_order)
    
    return backfitter, phaii

def make_spectrum(phaii, bkgd, src_time, erange, spectrum_name, pha_path):

    # the observed count spectrum during the source selection
    spec_data = phaii.to_spectrum(time_range=src_time)
    
    # the background model integrated over the source selection time
    spec_bkgd = bkgd.integrate_time(*src_time)
    
    # the energy range selection that was made
    spec_selection = phaii.to_spectrum(time_range=src_time, energy_range=erange)
    
    # plot a count spectrum with the data, background fit, and energy range selection
    specplot = Spectrum(data=spec_data, background=spec_bkgd)
    specplot.add_selection(spec_selection)

    # the single-spectrum PHA object over our source time interval and energy range
    pha = phaii.to_pha(time_ranges=src_time, energy_range=erange)
    
    # the background spectrum BAK object over our source time interval
    bak = bkgd.to_bak(time_range=src_time)

    # write the BAK object as a .bak file
    bak.write(directory=f'./{pha_path}', filename=f'{spectrum_name}.bak')

    # write the PHA object as a .pha file
    pha.write(directory=f'./{pha_path}', filename=f'{spectrum_name}.pha', backfile=f'{spectrum_name}.bak')
    
    return pha, bak

def make_rsp(rsp, pha, sp_name, pha_path):

    nearest_drm = rsp.extract_drm(atime=pha.tcent)
    
    # the interpolated drm
    interp_drm = rsp.interpolate(pha.tcent)

    # write the interpolated drm from the rsp2 file to a new rsp file
    interp_drm.write(f'./{pha_path}', filename=f'{sp_name}.rsp', overwrite=True)

def make_bg(tte, time_res_bg):

    pass
    
def get_ranges_bg(det):

    if det[0] == 'n':
        lst_erange_en = ((8.0, 900.0), (8.0, 50.0), (50.0, 100.0), (100.0, 500.0), (500.0, 900.0))
        lst_erange_y =  ((600, 1400),  (500, 1000),  (100, 300), (100, 300), (0, 50))
        lst_ = [[f'e{int(e1)}_{int(e2)}', (e1, e2)] for e1, e2 in lst_erange_en]
        lst_[0][0] = 'tot'
        return lst_, lst_erange_y
    else:
        lst_erange_en = ((250, 4e4), (250, 500.0), (500, 1000.0), (1e3, 5e3), (5e3, 1e4), (1e4, 4e4))
        lst_erange_y =  ((1000, 1400), (200, 500),  (100, 400.0),  (300, 800), (0, 100), (0, 100))
        lst_ = [[f'e{int(e1)}_{int(e2)}', (e1, e2)] for e1, e2 in lst_erange_en]
        lst_[0][0] = 'tot'
        return lst_, lst_erange_y

def get_bg_poly_order(det):

    if det[0] == 'n':
        return 2
    else:
        return 1

def main():

    fig_path = 'figures_gbm111'
    pha_path = 'pha_out_gbm111'
    data_path = 'data'

    name = '250919020'
    #lst_det = 'n7 b1'.split()
    lst_det = 'n7'.split()

    lst_intervals = 'sp14 sp10_18 sp19_23 sp35_36 sp37_38'.split()
    dic_sp_intervals = {
        'sp14': (30.436, 30.692),
        'sp10_18': (28.388, 33.252),
        'sp19_23': (33.252, 36.580),
        'sp35_36': (126.692, 143.076),
        'sp37_38': (143.076, 159.460)
    }

    time_res_src = 0.016

    dic_time_res_bg = {
        'n7': 1.024*4, 
        'b0': 1.024*10, 
        'b1': 1.024*10
    }
    dic_sp_erange = {
        'n7': (8.0, 1000.0), 
        'b0': (250.0, 4.0e4), 
        'b1': (250.0, 4.0e4)
    }

    bkgd_times = [(-60.0, -10.0), (250.0, 400.0)]


    for det in lst_det:

        tte = TTE.open(f'data/glg_tte_{det}_bn{name}_v00.fit')

        poly_order = get_bg_poly_order(det)
        backfitter, phaii_bg = fit_bg(tte, dic_time_res_bg[det], bkgd_times, poly_order)

        lst_ranges, lst_range_y = get_ranges_bg(det)

        for rng, y_lim in zip(lst_ranges, lst_range_y):

            bkgd = backfitter.interpolate_bins(phaii_bg.data.tstart, phaii_bg.data.tstop)
            lc_bkgd = bkgd.integrate_energy(*rng[1])
            lc_data = phaii_bg.to_lightcurve(energy_range=rng[1])
            fig_name = f'{fig_path}/bg_{det}_{rng[0]}'
            str_title = f'{det} {rng[0]} bg fit {poly_order=}'
            plot_lc(lc_data, fig_name, str_title, y_lim, bg_data=lc_bkgd)
      
        erange = lst_ranges[0][1] # tot interval for each detector

        # producing time resolved spectra lst_intervals[:2]
        for sp_name in lst_intervals[:1]:

            sp_src_int = dic_sp_intervals[sp_name]
            burst_interval = (sp_src_int[0]-5, sp_src_int[1]+5)

            phaii_src = tte.to_phaii(bin_by_time, time_res_src, time_ref=0.0, time_range=burst_interval)
            lc_data = phaii_src.to_lightcurve(energy_range=erange)
    
            bkgd = backfitter.interpolate_bins(phaii_src.data.tstart, phaii_src.data.tstop)
            lc_bkgd = bkgd.integrate_energy(*erange)
    
            src_lc = phaii_src.to_lightcurve(time_range=sp_src_int, energy_range=erange)
    
            fig_name = f'{fig_path}/src_{sp_name}_{det}_{lst_ranges[0][0]}'
            str_title = f'{det} energy range: {lst_ranges[0][1]} keV\ntime range: {sp_src_int} s\nbg fit {poly_order=}'
     
            plot_lc(lc_data, fig_name, str_title, y_lim=None, bg_data=lc_bkgd, src_lc=src_lc, x_range=burst_interval)
    
            spectrum_name = f'{det}_{sp_name}'
            pha, bak = make_spectrum(phaii_src, bkgd, sp_src_int, dic_sp_erange[det], spectrum_name, pha_path)
    
            rsp = RSP.open(f'{data_path}/glg_cspec_{det}_bn{name}_v02.rsp2')
            make_rsp(rsp, pha, spectrum_name, pha_path)

main()
