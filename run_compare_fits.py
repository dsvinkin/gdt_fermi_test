"""
# Basic header and structure comparison only
python compare_fits.py table1.fits table2.fits

# Compare table content as well
python compare_fits.py table1.fits table2.fits --compare-content

# Compare with custom tolerance for floating point values
python compare_fits.py data1.fits data2.fits --compare-content --tolerance 1e-8

# Show more difference rows
python compare_fits.py table1.fits table2.fits --compare-content --max-rows 20

# Complete comparison with statistics (slower for large tables)
python compare_fits.py large1.fits large2.fits --compare-content --compare-all

# Compare specific HDU with content
python compare_fits.py multi.hdu.fits multi.hdu2.fits --hdu 2 --compare-content
"""

import sys
import os

def main():
    """
    python compare_fits.py table1.fits table2.fits --hdu 2
    """
    lst_types = "pha  bak rsp".split()
    lst_det = "n7 b1".split()

    sp = 'sp14'
    det  = 'n7'
    
    for fits_type in lst_types:

        hdu_old = 2 
        hdu_new = 2 

        if fits_type == 'pha' or fits_type == 'bak':
            hdu_old = 2 
            hdu_new = 1 
        
        str_sys = f"python3 compare_fits_deep.py"+\
            f" pha_out_gbm111/{det}_{sp}.{fits_type} pha_out_main_core_7abfee8_fermi_7fb502d/{det}_{sp}.{fits_type} "+\
            f" --hdu1={hdu_old} --hdu2={hdu_new} --compare-content --tolerance=1e-3 --max-rows=20 > pha_hdu2_dif_{fits_type}.txt" 
        os.system(str_sys)


main()