import os
import subprocess

def grp_list():

    grp_counts = 20

    lst_det = 'n7 b1'.split()
    lst_sp = 'sp14 sp10_18 sp19_23 sp35_36 sp37_38'.split()
    
    for det in lst_det:
        for sp in lst_sp[:1]:
            str_ = f"grppha {det}_{sp}.pha {det}_{sp}_gr{grp_counts}.pha comm='group min {grp_counts}& exit'" 
            subprocess.call(str_, shell=True)

grp_list()