#!/usr/bin/env python3
"""
MVP3 Key Canonicalization Utility
Provides functions for generating stable, consistent event keys.
"""

import argparse
import json
import re
from typing import Dict, List, Any, Tuple

def normalize_param_value(value: Any) -> str:
    """Normalize parameter values for consistent key generation."""
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        else:
            # Remove trailing zeros and decimal point if not needed
            return f"{value:.6f}".rstrip('0').rstrip('.')
    elif isinstance(value, str):
        # Normalize string values
        normalized = value.lower().strip()
        # Replace spaces with underscores
        normalized = normalized.replace(' ', '_')
        # Remove special characters except common ones
        normalized = re.sub(r'[^\w\-\.\%\$]', '', normalized)
        return normalized
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, (int, type(None))):
        return str(value)
    elif isinstance(value, list):
        # Sort and normalize list values
        normalized_items = [normalize_param_value(item) for item in sorted(set(str(item) for item in value))]
        return '[' + ','.join(normalized_items) + ']'
    elif isinstance(value, dict):
        # Normalize dict as sorted key=value pairs
        normalized_pairs = []
        for k in sorted(value.keys()):
            normalized_pairs.append(f"{normalize_param_value(k)}:{normalize_param_value(value[k])}")
        return '{' + ','.join(normalized_pairs) + '}'
    else:
        return str(value).lower()

def canonicalize_symbols(symbols: List[str]) -> str:
    """Canonicalize ticker symbols for consistent ordering."""
    if not symbols:
        return ""
    
    # Convert to uppercase, remove duplicates, and sort
    canonical_symbols = sorted(list(set(s.upper().strip() for s in symbols if s.strip())))
    
    return ','.join(canonical_symbols)

def canonicalize_parameters(params: Dict[str, Any]) -> str:
    """Canonicalize parameters into a sorted, consistent string."""
    if not params:
        return ""
    
    # Normalize and sort parameters
    param_pairs = []
    for key in sorted(params.keys()):
        if params[key] is not None:  # Skip None values
            normalized_key = normalize_param_value(key)
            normalized_value = normalize_param_value(params[key])
            param_pairs.append(f"{normalized_key}={normalized_value}")
    
    return ';'.join(param_pairs)

def generate_event_key(
    event_type: str,
    category: str,
    symbols: List[str],
    params: Dict[str, Any],
    data_version: str = 'v1'
) -> str:
    """
    Generate a stable, canonical event key.
    
    Format: {event_type}|{category}|{symbols_sorted}|{canonical_params}|{data_version}
    """
    # Normalize event type and category
    event_type_norm = event_type.lower().strip()
    category_norm = category.lower().strip() if category else "general"
    
    # Canonicalize symbols
    symbols_canon = canonicalize_symbols(symbols)
    
    # Canonicalize parameters
    params_canon = canonicalize_parameters(params)
    
    # Build the key
    key_parts = [
        event_type_norm,
        category_norm,
        symbols_canon,
        params_canon,
        data_version.lower()
    ]
    
    return '|'.join(key_parts)

def parse_event_key(event_key: str) -> Dict[str, Any]:
    """Parse an event key back into its components."""
    try:
        parts = event_key.split('|')
        if len(parts) != 5:
            raise ValueError(f"Invalid event key format. Expected 5 parts, got {len(parts)}")
        
        event_type, category, symbols_str, params_str, data_version = parts
        
        # Parse symbols
        symbols = symbols_str.split(',') if symbols_str else []
        
        # Parse parameters
        params = {}
        if params_str:
            param_pairs = params_str.split(';')
            for pair in param_pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Try to convert value to appropriate type
                    if value.lower() in ('true', 'false'):
                        params[key] = value.lower() == 'true'
                    elif value.isdigit():
                        params[key] = int(value)
                    elif re.match(r'^\d+\.\d+$', value):
                        params[key] = float(value)
                    else:
                        params[key] = value
        
        return {
            'event_type': event_type,
            'category': category,
            'symbols': symbols,
            'parameters': params,
            'data_version': data_version
        }
        
    except Exception as e:
        raise ValueError(f"Failed to parse event key '{event_key}': {e}")

def validate_key_consistency(keys: List[str]) -> Dict[str, Any]:
    """Validate that multiple keys are consistent and identify potential issues."""
    if not keys:
        return {'valid': True, 'issues': [], 'unique_keys': 0}
    
    issues = []
    unique_keys = len(set(keys))
    
    # Parse all keys
    parsed_keys = []
    for i, key in enumerate(keys):
        try:
            parsed = parse_event_key(key)
            parsed_keys.append((i, parsed))
        except ValueError as e:
            issues.append(f"Key {i}: Invalid format - {e}")
    
    # Check for consistency issues
    if len(parsed_keys) > 1:
        # Group by event type and category
        type_category_groups = {}
        for i, parsed in parsed_keys:
            tc_key = f"{parsed['event_type']}/{parsed['category']}"
            if tc_key not in type_category_groups:
                type_category_groups[tc_key] = []
            type_category_groups[tc_key].append((i, parsed))
        
        # Check for parameter variations within same type/category
        for tc_key, group in type_category_groups.items():
            if len(group) > 1:
                # Check symbol consistency
                symbol_sets = [set(parsed['symbols']) for _, parsed in group]
                if len(set(tuple(sorted(s)) for s in symbol_sets)) > 1:
                    issues.append(f"Inconsistent symbols in {tc_key}: {symbol_sets}")
                
                # Check parameter key consistency
                param_key_sets = [set(parsed['parameters'].keys()) for _, parsed in group]
                if len(set(tuple(sorted(s)) for s in param_key_sets)) > 1:
                    issues.append(f"Inconsistent parameter keys in {tc_key}")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'unique_keys': unique_keys,
        'total_keys': len(keys),
        'parsed_successfully': len(parsed_keys)
    }

def suggest_key_improvements(event_key: str) -> List[str]:
    """Suggest improvements for better key consistency."""
    suggestions = []
    
    try:
        parsed = parse_event_key(event_key)
        
        # Check for common issues
        params = parsed['parameters']
        
        # Suggest parameter normalization
        for key, value in params.items():
            if isinstance(value, str):
                if ' ' in value:
                    suggestions.append(f"Consider normalizing parameter '{key}': '{value}' -> '{value.replace(' ', '_')}'")
                if value != value.lower():
                    suggestions.append(f"Consider lowercase for parameter '{key}': '{value}' -> '{value.lower()}'")
        
        # Check symbol formatting
        symbols = parsed['symbols']
        for symbol in symbols:
            if symbol != symbol.upper():
                suggestions.append(f"Symbol should be uppercase: '{symbol}' -> '{symbol.upper()}'")
        
        # Check category naming
        category = parsed['category']
        if ' ' in category:
            suggestions.append(f"Category should use underscores: '{category}' -> '{category.replace(' ', '_')}'")
        
    except ValueError as e:
        suggestions.append(f"Key format error: {e}")
    
    return suggestions

def main():
    """Main CLI interface for key canonicalization utilities."""
    parser = argparse.ArgumentParser(description='MVP3 Event Key Canonicalization Utility')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate key command
    gen_parser = subparsers.add_parser('generate', help='Generate a canonical event key')
    gen_parser.add_argument('--event-type', required=True, help='Event type (analysis/proposal/insight/observation)')
    gen_parser.add_argument('--category', required=True, help='Event category')
    gen_parser.add_argument('--symbols', nargs='+', help='Ticker symbols')
    gen_parser.add_argument('--params', help='Parameters as JSON string')
    gen_parser.add_argument('--data-version', default='v1', help='Data version (default: v1)')
    
    # Parse key command
    parse_parser = subparsers.add_parser('parse', help='Parse an event key into components')
    parse_parser.add_argument('key', help='Event key to parse')
    
    # Validate keys command
    validate_parser = subparsers.add_parser('validate', help='Validate key consistency')
    validate_parser.add_argument('keys', nargs='+', help='Event keys to validate')
    
    # Suggest improvements command
    suggest_parser = subparsers.add_parser('suggest', help='Suggest key improvements')
    suggest_parser.add_argument('key', help='Event key to analyze')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run consistency tests')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        # Parse parameters from JSON if provided
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError as e:
                print(f"Error parsing parameters JSON: {e}")
                return
        
        # Generate key
        key = generate_event_key(
            event_type=args.event_type,
            category=args.category,
            symbols=args.symbols or [],
            params=params,
            data_version=args.data_version
        )
        
        print(key)
        
    elif args.command == 'parse':
        try:
            parsed = parse_event_key(args.key)
            print(json.dumps(parsed, indent=2))
        except ValueError as e:
            print(f"Error: {e}")
            
    elif args.command == 'validate':
        result = validate_key_consistency(args.keys)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'suggest':
        suggestions = suggest_key_improvements(args.key)
        if suggestions:
            print("Suggestions for improvement:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        else:
            print("Key looks good - no improvements suggested")
            
    elif args.command == 'test':
        # Run consistency tests
        print("Running canonicalization consistency tests...")
        
        # Test 1: Same inputs should produce same key
        params1 = {'rsi': 70, 'timeframe': '1d', 'volume_ratio': 2.0}
        params2 = {'volume_ratio': 2.0, 'timeframe': '1d', 'rsi': 70}  # Different order
        
        key1 = generate_event_key('analysis', 'swing_setup', ['NVDA'], params1)
        key2 = generate_event_key('analysis', 'swing_setup', ['NVDA'], params2)
        
        test1_pass = key1 == key2
        print(f"[OK] Parameter order independence: {'PASS' if test1_pass else 'FAIL'}")
        if not test1_pass:
            print(f"   Key1: {key1}")
            print(f"   Key2: {key2}")
        
        # Test 2: Symbol normalization
        key3 = generate_event_key('analysis', 'swing_setup', ['nvda', 'AAPL'], {})
        key4 = generate_event_key('analysis', 'swing_setup', ['AAPL', 'NVDA'], {})
        
        test2_pass = key3 == key4
        print(f"[OK] Symbol normalization: {'PASS' if test2_pass else 'FAIL'}")
        if not test2_pass:
            print(f"   Key3: {key3}")
            print(f"   Key4: {key4}")
        
        # Test 3: Parse round-trip
        original_key = generate_event_key('proposal', 'trade_rec', ['AAPL'], {'target': 195, 'stop': 185})
        try:
            parsed = parse_event_key(original_key)
            reconstructed_key = generate_event_key(
                parsed['event_type'],
                parsed['category'],
                parsed['symbols'],
                parsed['parameters']
            )
            test3_pass = original_key == reconstructed_key
            print(f"[OK] Parse round-trip: {'PASS' if test3_pass else 'FAIL'}")
            if not test3_pass:
                print(f"   Original: {original_key}")
                print(f"   Reconstructed: {reconstructed_key}")
        except Exception as e:
            print(f"[ERR] Parse round-trip: FAIL - {e}")
        
        print("\nTest completed.")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()