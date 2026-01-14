#!/usr/bin/env python3
"""
Failed Products Analyzer
Analyzes error logs from bulk import to identify patterns and specific failures
"""
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def analyze_import_logs(log_dir='logs'):
    """Analyze all import logs and generate failure report"""
    log_path = Path(log_dir)
    
    if not log_path.exists():
        print("❌ No logs directory found")
        return
    
    # Find latest error log
    error_logs = list(log_path.glob('bulk_errors_*.log'))
    if not error_logs:
        print("❌ No error logs found")
        return
    
    latest_error_log = max(error_logs, key=lambda x: x.stat().st_mtime)
    print(f"📄 Analyzing error log: {latest_error_log.name}")
    
    # Parse errors
    failed_skus = defaultdict(list)
    error_patterns = Counter()
    missing_categories = Counter()
    
    with open(latest_error_log, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract SKU failures
    sku_errors = re.findall(r'SKU ([A-Z0-9]+): (.+)', content)
    for sku, error in sku_errors:
        failed_skus[sku].append(error.strip())
        
        # Categorize error types
        if 'missing category' in error.lower():
            # Extract category name
            cat_match = re.search(r"missing category '([^']+)'", error)
            if cat_match:
                missing_categories[cat_match.group(1)] += 1
            error_patterns['Missing Category'] += 1
        elif 'invalid_sku' in error.lower():
            error_patterns['Invalid/Duplicate SKU'] += 1
        elif 'timeout' in error.lower():
            error_patterns['Timeout'] += 1
        elif 'http' in error.lower():
            error_patterns['HTTP Error'] += 1
        else:
            error_patterns['Other'] += 1
    
    # Generate report
    print(f"\n{'='*60}")
    print("FAILED PRODUCTS ANALYSIS REPORT")
    print(f"{'='*60}")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log file: {latest_error_log.name}")
    
    print(f"\n📊 SUMMARY")
    print(f"   Total failed SKUs: {len(failed_skus)}")
    print(f"   Total error instances: {sum(error_patterns.values())}")
    
    print(f"\n🔍 ERROR PATTERNS")
    for pattern, count in error_patterns.most_common():
        print(f"   {pattern}: {count}")
    
    if missing_categories:
        print(f"\n❌ TOP MISSING CATEGORIES")
        for category, count in missing_categories.most_common(10):
            print(f"   '{category}': {count} SKUs affected")
    
    print(f"\n📋 FAILED SKUs SAMPLE (first 20)")
    for i, (sku, errors) in enumerate(list(failed_skus.items())[:20]):
        print(f"   {sku}: {errors[0]}")
        if len(errors) > 1:
            print(f"      + {len(errors)-1} more error(s)")
    
    if len(failed_skus) > 20:
        print(f"   ... and {len(failed_skus)-20} more failed SKUs")
    
    # Generate CSV for detailed analysis
    csv_path = log_path / f'failed_skus_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("SKU,Error_Type,Error_Message\n")
        for sku, errors in failed_skus.items():
            for error in errors:
                error_type = "Missing_Category" if "missing category" in error.lower() else "Other"
                f.write(f'"{sku}","{error_type}","{error.replace('"', '""')}"\n')
    
    print(f"\n💾 Detailed CSV saved: {csv_path.name}")
    return {
        'failed_skus': dict(failed_skus),
        'error_patterns': dict(error_patterns),
        'missing_categories': dict(missing_categories)
    }

def analyze_progress_logs(log_dir='logs'):
    """Analyze progress logs to see what was successfully imported"""
    log_path = Path(log_dir)
    
    # Find latest progress log
    progress_logs = list(log_path.glob('bulk_progress_*.json'))
    if not progress_logs:
        print("❌ No progress logs found")
        return
    
    latest_progress_log = max(progress_logs, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_progress_log, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        print(f"\n📈 PROGRESS ANALYSIS")
        print(f"   Processed SKUs: {len(progress_data.get('processed_skus', []))}")
        print(f"   Products created: {progress_data.get('stats', {}).get('products_created', 0)}")
        print(f"   Products updated: {progress_data.get('stats', {}).get('products_updated', 0)}")
        print(f"   Errors: {progress_data.get('stats', {}).get('errors', 0)}")
        
        return progress_data
        
    except Exception as e:
        print(f"❌ Failed to read progress log: {e}")
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze bulk import failure logs')
    parser.add_argument('--log-dir', default='logs', help='Directory containing log files')
    args = parser.parse_args()
    
    # Analyze both error and progress logs
    error_analysis = analyze_import_logs(args.log_dir)
    progress_analysis = analyze_progress_logs(args.log_dir)
    
    if error_analysis and progress_analysis:
        success_rate = (progress_analysis.get('stats', {}).get('products_created', 0) / 
                       (len(error_analysis['failed_skus']) + progress_analysis.get('stats', {}).get('products_created', 1))) * 100
        print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")