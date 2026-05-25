#!/usr/bin/env python3
"""
Script for comparing FITS file headers and table structures.
Compares two FITS files: their headers (HDUs), binary table structures, and table data.
"""

import sys
import argparse
from astropy.io import fits
from collections import defaultdict
import numpy as np

def compare_headers(header1, header2, name1="File1", name2="File2", ignore_keys=None):
    """
    Compare two FITS headers.
    
    Parameters:
    -----------
    header1, header2 : astropy.io.fits.Header
        Headers to compare
    name1, name2 : str
        File names for output
    ignore_keys : list
        List of keys to ignore during comparison
    
    Returns:
    --------
    dict : Comparison results
    """
    if ignore_keys is None:
        ignore_keys = ['COMMENT', 'HISTORY', 'CHECKSUM', 'DATASUM', 'DATE']
    
    keys1 = set(header1.keys()) - set(ignore_keys)
    keys2 = set(header2.keys()) - set(ignore_keys)
    
    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1
    common_keys = keys1 & keys2
    
    differences = []
    
    for key in common_keys:
        val1 = header1[key]
        val2 = header2[key]
        
        # Compare with type consideration
        if isinstance(val1, (str, np.str_)) and isinstance(val2, (str, np.str_)):
            if val1.strip() != val2.strip():
                differences.append({
                    'key': key,
                    f'{name1}': val1,
                    f'{name2}': val2
                })
        elif val1 != val2:
            differences.append({
                'key': key,
                f'{name1}': val1,
                f'{name2}': val2
            })
    
    result = {
        'only_in_first': {k: header1[k] for k in only_in_1},
        'only_in_second': {k: header2[k] for k in only_in_2},
        'differences': differences,
        'common_keys': list(common_keys)
    }
    
    return result

def compare_table_structure(table1, table2, name1="File1", name2="File2"):
    """
    Compare the structure of two FITS binary tables.
    
    Parameters:
    -----------
    table1, table2 : astropy.io.fits.BinTableHDU
        Tables to compare
    name1, name2 : str
        File names for output
    
    Returns:
    --------
    dict : Comparison results
    """
    result = {
        'column_names_1': list(table1.columns.names),
        'column_names_2': list(table2.columns.names),
        'type_differences': [],
        'shape_differences': [],
        'unit_differences': [],
        'only_in_first': [],
        'only_in_second': []
    }
    
    # Compare column names
    cols1_set = set(table1.columns.names)
    cols2_set = set(table2.columns.names)
    
    result['only_in_first'] = list(cols1_set - cols2_set)
    result['only_in_second'] = list(cols2_set - cols1_set)
    
    # Compare properties of common columns
    common_cols = cols1_set & cols2_set
    
    for col_name in common_cols:
        col1 = table1.columns[col_name]
        col2 = table2.columns[col_name]
        
        # Compare data types
        if col1.format != col2.format:
            result['type_differences'].append({
                'column': col_name,
                f'{name1}_format': col1.format,
                f'{name2}_format': col2.format
            })
        
        # Compare dimensions
        if col1.dim != col2.dim:
            result['shape_differences'].append({
                'column': col_name,
                f'{name1}_dim': col1.dim,
                f'{name2}_dim': col2.dim
            })
        
        # Compare units
        if col1.unit != col2.unit:
            result['unit_differences'].append({
                'column': col_name,
                f'{name1}_unit': col1.unit,
                f'{name2}_unit': col2.unit
            })
    
    return result

def compare_table_content(table1, table2, name1="File1", name2="File2", 
                          max_rows=10, tolerance=1e-6, compare_all=False):
    """
    Compare the content of two FITS tables.
    
    Parameters:
    -----------
    table1, table2 : astropy.io.fits.BinTableHDU
        Tables to compare
    name1, name2 : str
        File names for output
    max_rows : int
        Maximum number of rows to display in differences
    tolerance : float
        Tolerance for floating point comparisons
    compare_all : bool
        If True, compare all rows; if False, stop after finding differences
    
    Returns:
    --------
    dict : Comparison results
    """
    # Get data
    data1 = table1.data
    data2 = table2.data
    
    # Check row counts
    nrows1 = len(data1)
    nrows2 = len(data2)
    
    result = {
        'nrows1': nrows1,
        'nrows2': nrows2,
        'row_count_match': (nrows1 == nrows2),
        'column_differences': [],
        'row_differences': [],
        'statistics': {}
    }
    
    # Compare row counts
    if nrows1 != nrows2:
        result['row_differences'].append({
            'type': 'row_count',
            f'{name1}_rows': nrows1,
            f'{name2}_rows': nrows2
        })
        if not compare_all:
            return result
    
    # Get common columns
    cols1 = set(table1.columns.names)
    cols2 = set(table2.columns.names)
    common_cols = list(cols1 & cols2)
    
    # Compare each common column
    for col_name in common_cols:
        col_data1 = data1[col_name]
        col_data2 = data2[col_name]
        
        # Check if columns have same shape
        if col_data1.shape != col_data2.shape:
            result['column_differences'].append({
                'column': col_name,
                'type': 'shape_mismatch',
                f'{name1}_shape': col_data1.shape,
                f'{name2}_shape': col_data2.shape
            })
            continue
        
        # Compare column data
        try:
            if np.issubdtype(col_data1.dtype, np.number):
                # Numeric comparison with tolerance
                if col_data1.dtype == np.float64 or col_data1.dtype == np.float32:
                    diff_mask = ~np.isclose(col_data1, col_data2, rtol=tolerance, atol=tolerance, equal_nan=True)
                else:
                    diff_mask = (col_data1 != col_data2)
            else:
                # String or other types comparison
                if col_data1.dtype.kind in ['S', 'U']:
                    # String comparison
                    diff_mask = np.array([str(x).strip() != str(y).strip() for x, y in zip(col_data1, col_data2)])
                else:
                    diff_mask = (col_data1 != col_data2)
            
            n_diffs = np.sum(diff_mask)
            
            if n_diffs > 0:
                # Get indices where differences occur
                if col_data1.ndim == 1:
                    diff_indices = np.where(diff_mask)[0]
                else:
                    # For multi-dimensional columns, find first dimension differences
                    diff_indices = np.where(diff_mask.any(axis=tuple(range(1, diff_mask.ndim))))[0]
                
                # Store difference information
                diff_info = {
                    'column': col_name,
                    'dtype': str(col_data1.dtype),
                    'n_differences': int(n_diffs),
                    'differences': []
                }
                
                # Show first few differences
                for idx in diff_indices[:max_rows]:
                    if col_data1.ndim == 1:
                        val1 = col_data1[idx]
                        val2 = col_data2[idx]
                    else:
                        val1 = col_data1[idx]
                        val2 = col_data2[idx]
                    
                    diff_info['differences'].append({
                        'row': int(idx),
                        f'{name1}': str(val1),
                        f'{name2}': str(val2)
                    })
                
                result['column_differences'].append(diff_info)
                
                # Stop if not comparing all and we found differences
                if not compare_all:
                    break
                    
        except Exception as e:
            result['column_differences'].append({
                'column': col_name,
                'type': 'comparison_error',
                'error': str(e)
            })
    
    # Calculate statistics
    if compare_all and nrows1 == nrows2:
        total_elements = 0
        total_differences = 0
        for col_diff in result['column_differences']:
            if 'n_differences' in col_diff:
                total_differences += col_diff['n_differences']
                # Estimate total elements
                if col_diff['column'] in common_cols:
                    col_data = data1[col_diff['column']]
                    total_elements += col_data.size
        
        if total_elements > 0:
            result['statistics'] = {
                'total_elements': total_elements,
                'total_differences': total_differences,
                'difference_percentage': (total_differences / total_elements) * 100
            }
    
    return result

def print_comparison_result(header_result, table_result, content_result, 
                           filename1, filename2, show_content=True):
    """
    Print comparison results in a human-readable format.
    """
    print("\n" + "="*80)
    print(f"FITS FILES COMPARISON")
    print(f"File 1: {filename1}")
    print(f"File 2: {filename2}")
    print("="*80)
    
    # Header comparison
    print("\n[1] HEADER COMPARISON:")
    print("-"*40)
    
    if header_result['only_in_first']:
        print(f"\n[WARNING] Keys only in {filename1}:")
        for key, value in header_result['only_in_first'].items():
            print(f"   {key}: {value}")
    
    if header_result['only_in_second']:
        print(f"\n[WARNING] Keys only in {filename2}:")
        for key, value in header_result['only_in_second'].items():
            print(f"   {key}: {value}")
    
    if header_result['differences']:
        print(f"\n[WARNING] Differences in common key values:")
        for diff in header_result['differences']:
            print(f"\n   Key: {diff['key']}")
            print(f"     {filename1}: {diff[filename1]}")
            print(f"     {filename2}: {diff[filename2]}")
    elif not header_result['only_in_first'] and not header_result['only_in_second']:
        print("[OK] Headers are identical (considering ignored keys)")
    
    # Table structure comparison
    if table_result:
        print("\n\n[2] TABLE STRUCTURE COMPARISON:")
        print("-"*40)
        
        print(f"\nColumns in {filename1}: {table_result['column_names_1']}")
        print(f"Columns in {filename2}: {table_result['column_names_2']}")
        
        if table_result['only_in_first']:
            print(f"\n[WARNING] Columns only in {filename1}: {table_result['only_in_first']}")
        
        if table_result['only_in_second']:
            print(f"\n[WARNING] Columns only in {filename2}: {table_result['only_in_second']}")
        
        if table_result['type_differences']:
            print(f"\n[WARNING] Data type differences:")
            for diff in table_result['type_differences']:
                print(f"   Column '{diff['column']}':")
                print(f"     {filename1}: {diff[f'{filename1}_format']}")
                print(f"     {filename2}: {diff[f'{filename2}_format']}")
        
        if table_result['shape_differences']:
            print(f"\n[WARNING] Dimension differences:")
            for diff in table_result['shape_differences']:
                print(f"   Column '{diff['column']}':")
                print(f"     {filename1}: {diff[f'{filename1}_dim']}")
                print(f"     {filename2}: {diff[f'{filename2}_dim']}")
        
        if table_result['unit_differences']:
            print(f"\n[WARNING] Unit differences:")
            for diff in table_result['unit_differences']:
                print(f"   Column '{diff['column']}':")
                print(f"     {filename1}: {diff[f'{filename1}_unit']}")
                print(f"     {filename2}: {diff[f'{filename2}_unit']}")
        
        if (not table_result['only_in_first'] and 
            not table_result['only_in_second'] and 
            not table_result['type_differences'] and
            not table_result['shape_differences'] and
            not table_result['unit_differences']):
            print("\n[OK] Table structures are identical")
    else:
        print("\n[2] No tables found in specified HDU")
    
    # Table content comparison
    if show_content and content_result:
        print("\n\n[3] TABLE CONTENT COMPARISON:")
        print("-"*40)
        
        # Row count comparison
        print(f"\nRow count in {filename1}: {content_result['nrows1']}")
        print(f"Row count in {filename2}: {content_result['nrows2']}")
        
        if not content_result['row_count_match']:
            print("[WARNING] Row counts do not match!")
        
        # Column differences
        if content_result['column_differences']:
            print(f"\n[WARNING] Found {len(content_result['column_differences'])} column(s) with differences:")
            for col_diff in content_result['column_differences']:
                if 'type' in col_diff and col_diff['type'] == 'shape_mismatch':
                    print(f"\n   Column '{col_diff['column']}':")
                    print(f"     Shape mismatch - {filename1}: {col_diff[f'{filename1}_shape']}, "
                          f"{filename2}: {col_diff[f'{filename2}_shape']}")
                elif 'type' in col_diff and col_diff['type'] == 'comparison_error':
                    print(f"\n   Column '{col_diff['column']}':")
                    print(f"     Comparison error: {col_diff['error']}")
                else:
                    print(f"\n   Column '{col_diff['column']}' (dtype: {col_diff['dtype']}):")
                    print(f"     Number of differences: {col_diff['n_differences']}")
                    if col_diff['differences']:
                        print(f"     First {len(col_diff['differences'])} differences:")
                        for diff in col_diff['differences']:
                            print(f"       Row {diff['row']}: {filename1}={diff[filename1]}, "
                                  f"{filename2}={diff[filename2]}")
        else:
            if content_result['row_count_match']:
                print("\n[OK] Table contents are identical")
            else:
                print("\n[WARNING] Cannot compare content due to row count mismatch")
        
        # Statistics
        if content_result['statistics']:
            print(f"\n[STATISTICS]")
            print(f"   Total elements compared: {content_result['statistics']['total_elements']}")
            print(f"   Total differences: {content_result['statistics']['total_differences']}")
            print(f"   Difference percentage: {content_result['statistics']['difference_percentage']:.4f}%")
    
    elif not show_content and table_result:
        print("\n\n[3] TABLE CONTENT COMPARISON: Skipped (use --compare-content to enable)")

def main():
    parser = argparse.ArgumentParser(
        description="Compare headers, table structures, and table data of two FITS files"
    )
    parser.add_argument("file1", help="Path to first FITS file")
    parser.add_argument("file2", help="Path to second FITS file")
    parser.add_argument("--hdu", type=int, default=1, 
                       help="HDU number to compare (default: 1)")
    parser.add_argument("--ignore-keys", nargs='+', 
                       default=['COMMENT', 'HISTORY', 'CHECKSUM', 'DATASUM', 'DATE'],
                       help="Keys to ignore during header comparison")
    parser.add_argument("--compare-content", action='store_true',
                       help="Compare table content (data values)")
    parser.add_argument("--max-rows", type=int, default=10,
                       help="Maximum number of rows to show in content differences (default: 10)")
    parser.add_argument("--tolerance", type=float, default=1e-6,
                       help="Tolerance for floating point comparisons (default: 1e-6)")
    parser.add_argument("--compare-all", action='store_true',
                       help="Compare all rows and show statistics (may be slow for large tables)")
    
    args = parser.parse_args()
    
    try:
        # Open FITS files
        with fits.open(args.file1) as hdul1, fits.open(args.file2) as hdul2:
            # Check if HDU exists
            if args.hdu >= len(hdul1):
                print(f"Error: HDU {args.hdu} does not exist in {args.file1}")
                sys.exit(1)
            if args.hdu >= len(hdul2):
                print(f"Error: HDU {args.hdu} does not exist in {args.file2}")
                sys.exit(1)
            
            # Compare headers
            header_result = compare_headers(
                hdul1[args.hdu].header, 
                hdul2[args.hdu].header,
                name1=args.file1,
                name2=args.file2,
                ignore_keys=args.ignore_keys
            )
            
            # Compare table structures if they exist
            table_result = None
            content_result = None
            
            if (isinstance(hdul1[args.hdu], (fits.BinTableHDU, fits.TableHDU)) and
                isinstance(hdul2[args.hdu], (fits.BinTableHDU, fits.TableHDU))):
                
                table_result = compare_table_structure(
                    hdul1[args.hdu],
                    hdul2[args.hdu],
                    name1=args.file1,
                    name2=args.file2
                )
                
                # Compare content if requested
                if args.compare_content:
                    print("Comparing table content...")
                    content_result = compare_table_content(
                        hdul1[args.hdu],
                        hdul2[args.hdu],
                        name1=args.file1,
                        name2=args.file2,
                        max_rows=args.max_rows,
                        tolerance=args.tolerance,
                        compare_all=args.compare_all
                    )
            
            # Print results
            print_comparison_result(
                header_result, 
                table_result, 
                content_result,
                args.file1, 
                args.file2,
                show_content=args.compare_content
            )
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing FITS files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()