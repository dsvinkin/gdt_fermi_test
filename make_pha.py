import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt 
import numpy as np

import gdt.missions.fermi 
import gdt.core

from gdt.missions.fermi.gbm.tte import GbmTte
from gdt.missions.fermi.gbm.response import GbmRsp2

from gdt.core.binning.unbinned import bin_by_time

from gdt.core.plot.lightcurve import Lightcurve
from gdt.core.plot.spectrum import Spectrum

# the background fitter interface
from gdt.core.background.fitter import BackgroundFitter

# our fitting algorithm
from gdt.core.background.binned import Polynomial


def plot_lc(lc_data, fig_name, str_title, y_lim=None, bg_data=None, src_lc=None, x_range=None):
    """
    https://astro-gdt.readthedocs.io/en/latest/core/plot/lightcurve.html
    https://astro-gdt.readthedocs.io/en/latest/api/gdt.core.plot.lightcurve.Lightcurve.html

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

    plt.savefig(f'{fig_name}.png')

def fit_bg(tte, time_res, bkgd_times, poly_order):

    phaii = tte.to_phaii(bin_by_time, time_res, time_ref=0.0)

    backfitter = BackgroundFitter.from_phaii(phaii, Polynomial, time_ranges=bkgd_times)
    
    # once initialized, run the fit - in this case, we use a fit the background as a 1st degree polynomial
    backfitter.fit(order=poly_order)
    
    return backfitter, phaii

def make_spectrum(phaii, bkgd, src_time, erange, spectrum_name):

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
    print(type(pha), type(bak))

    # write the PHA object as a .pha file
    pha.write(directory='./', filename=f'{spectrum_name}.pha', overwrite=True)
    
    # write the BAK object as a .bak file
    bak.write(directory='./', filename=f'{spectrum_name}.bak', overwrite=True)

    return pha, bak

def make_rsp(rsp, pha, sp_name):

    nearest_drm = rsp.extract_drm(atime=pha.tcent)
    
    # the interpolated drm
    interp_drm = rsp.interpolate(pha.tcent)

    # write the interpolated drm from the rsp2 file to a new rsp file
    interp_drm.write('./', filename=f'{sp_name}.rsp', overwrite=True)
    
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

    name = '250919020'
    lst_det = 'n7 b1'.split()

    lst_intervals = 'sp14 sp10_18'.split()
    dic_sp_intervals = {
        'sp14': (30.436, 30.692),
        'sp10_18': (28.388, 33.252),
    }

    time_res_src = 0.016

    dic_time_res_bg = {'n7': 1.024*4, 'b1': 1.024*10}
    dic_sp_erange = {'n7': (8.0, 1000.0), 'b1': (250.0, 4.0e4)}

    bkgd_times = [(-60.0, -10.0), (250.0, 400.0)]

    sp_name = lst_intervals[0]
    sp_src_int = dic_sp_intervals[sp_name]

    burst_interval = (30, 40)

    for det in lst_det:

        tte = GbmTte.open(f'data/glg_tte_{det}_bn{name}_v00.fit')

        poly_order = get_bg_poly_order(det)
        backfitter, phaii_bg = fit_bg(tte, dic_time_res_bg[det], bkgd_times, poly_order)

        lst_ranges, lst_range_y = get_ranges_bg(det)
        for rng, y_lim in zip(lst_ranges, lst_range_y):

            bkgd = backfitter.interpolate_bins(phaii_bg.data.tstart, phaii_bg.data.tstop)
            lc_bkgd = bkgd.integrate_energy(*rng[1])
            lc_data = phaii_bg.to_lightcurve(energy_range=rng[1])
            fig_name = f'figures/bg_{det}_{rng[0]}'
            str_title = f'{det} {rng[0]} bg fit {poly_order=}'
            plot_lc(lc_data, fig_name, str_title, y_lim, bg_data=lc_bkgd)
      
        
        erange = lst_ranges[0][1]
        phaii_src = tte.to_phaii(bin_by_time, time_res_src, time_ref=0.0, time_range=burst_interval)
        lc_data = phaii_src.to_lightcurve(energy_range=erange)

        bkgd = backfitter.interpolate_bins(phaii_src.data.tstart, phaii_src.data.tstop)
        lc_bkgd = bkgd.integrate_energy(*erange)

        src_lc = phaii_src.to_lightcurve(time_range=sp_src_int, energy_range=erange)

        fig_name = f'figures/src_{det}_{lst_ranges[0][0]}'
        str_title = f'{det}\nenergy range: {lst_ranges[0][1]} keV\ntime range: {sp_src_int} s\nbg fit {poly_order=}'
        x_rng = (30,32)
        plot_lc(lc_data, fig_name, str_title, y_lim=None, bg_data=lc_bkgd, src_lc=src_lc, x_range=x_rng)

        spectrum_name = f'pha_out/{det}_{sp_name}'
        pha, bak = make_spectrum(phaii_src, bkgd, sp_src_int, dic_sp_erange[det], spectrum_name)

        rsp = GbmRsp2.open(f'data/glg_cspec_{det}_bn{name}_v02.rsp2')
        make_rsp(rsp, pha, spectrum_name)

main()
