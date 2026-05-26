# Test of GDT-core (commit 7abfee8) and GDT-Fermi (commit 7fb502d)

This repo contains test of XSPEC compatibility test of GBM spectral FITS files generated with 
GDT-core (commit 7abfee8) and GDT-Fermi (commit 7fb502d).

GBM spectral FITS files were generated according to the 
[Reduction and Export Tutorial](https://astro-gdt.readthedocs.io/projects/astro-gdt-fermi/en/latest/notebooks.html).

The resulting files can be loaded to XSPEC version: 12.15.0 with minor warnings
```
***Warning: spectrum TELESCOPE keyword (GLAST) is not consistent with that from background/correction file ().
***Warning: spectrum INSTRUMENT keyword (GBM) is not consistent with that from background/correction file ().
***Warning: spectrum FILTER keyword (none) is not consistent with that from background/correction file ().
***Warning: Background file POISSERR keyword is missing or of wrong format, assuming FALSE.
```

The count spectrum and response-convolved model looks reasonable.
However, after grouping spectrum (e.g. by >20 counts per channel, using grppha) PHA counts seem to be incorrect. 
This is most likely due to TZERO2=32768 key in the ungrouped PHA header. It seems that TZERO2=32768 may be an artifact.  

A detailed comparison between FITS files produced by GDT v2.2.2 and GBM tools v1.1.1 is in [v222_v111_comparison](v222_v111_comparison) 
A detailed comparison between FITS files produced by GDT-core (commit 7abfee8)+GDT-Fermi (commit 7fb502d) and GBM tools v1.1.1 can be found here: 

- [PHA](pha_hdu2_dif_pha.txt)
- [BAK](pha_hdu2_dif_pha.txt)
- [RSP](pha_hdu2_dif_rsp.txt) 

The FITS files produced by GDT-core (commit 7abfee8)+GDT-Fermi (commit 7fb502d) can be found in [pha_out_main_core_7abfee8_fermi_7fb502d](pha_out_main_core_7abfee8_fermi_7fb502d).