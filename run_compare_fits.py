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
    fits_type = 'rsp'
   
    str_sys = f"python3 compare_fits_deep.py pha_out_gbm111/{det}_{sp}.{fits_type} pha_out/{det}_{sp}.{fits_type} "+\
        " --hdu 2 --compare-content --tolerance=1e-3 --max-rows=20" 
    os.system(str_sys)


main()