#!/usr/bin/env python3
"""
Create a simple diagnostic script to check the Python environment
"""

import sys
import os
import json

def diagnose_python_env():
    """Diagnose Python environment and available packages"""
    
    try:
        diagnosis = {
            'python_executable': sys.executable,
            'python_version': sys.version,
            'current_working_directory': os.getcwd(),
            'python_path': sys.path[:5],  # First 5 entries
            'environment_variables': {
                'PYTHONPATH': os.environ.get('PYTHONPATH', 'Not set'),
                'VIRTUAL_ENV': os.environ.get('VIRTUAL_ENV', 'Not set')
            },
            'package_availability': {}
        }
        
        # Test package imports
        packages_to_test = ['ib_insync', 'sqlalchemy', 'psycopg2', 'pandas']
        
        for package in packages_to_test:
            try:
                __import__(package)
                if package == 'ib_insync':
                    import ib_insync
                    diagnosis['package_availability'][package] = {
                        'available': True,
                        'version': getattr(ib_insync, '__version__', 'unknown')
                    }
                else:
                    diagnosis['package_availability'][package] = {'available': True}
            except ImportError as e:
                diagnosis['package_availability'][package] = {
                    'available': False,
                    'error': str(e)
                }
        
        # Test if we can import our modules
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            mcp_server_path = os.path.join(project_root, 'mcp-server', 'src')
            sys.path.insert(0, project_root)
            sys.path.insert(0, mcp_server_path)
            
            from src.database.connection import db_manager
            from src.brokers.ibkr import IBKRBroker
            
            diagnosis['custom_modules'] = {
                'database_connection': 'available',
                'ibkr_broker': 'available'
            }
            
        except Exception as e:
            diagnosis['custom_modules'] = {
                'error': str(e)
            }
        
        diagnosis['status'] = 'success'
        
    except Exception as e:
        diagnosis = {
            'status': 'error',
            'error': str(e)
        }
    
    print(json.dumps(diagnosis, indent=2))
    return diagnosis

if __name__ == "__main__":
    result = diagnose_python_env()
    sys.exit(0 if result.get('status') == 'success' else 1)