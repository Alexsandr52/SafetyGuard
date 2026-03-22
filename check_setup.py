#!/usr/bin/env python3
"""
SafetyGuard Setup Check Script
Проверяет установку и готовность всех компонентов
"""

import sys
import os

def check_redis():
    """Проверяет Redis"""
    print('📦 Checking Redis...')
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print('  ✓ Redis is running and accessible')
        return True
    except ImportError:
        print('  ✗ Redis Python package not installed')
        print('    Run: pip install redis')
        return False
    except Exception as e:
        print(f'  ✗ Redis is not running: {e}')
        print('    Install Redis:')
        print('    - macOS: brew install redis && brew services start redis')
        print('    - Linux: sudo apt-get install redis-server && sudo systemctl start redis')
        return False

def check_opencv():
    """Проверяет OpenCV"""
    print('🎥 Checking OpenCV...')
    try:
        import cv2
        print(f'  ✓ OpenCV version: {cv2.__version__}')
        return True
    except ImportError:
        print('  ✗ OpenCV not installed')
        print('    Run: pip install opencv-python')
        return False

def check_yolo():
    """Проверяет YOLO"""
    print('🎯 Checking YOLO/Ultralytics...')
    try:
        from ultralytics import YOLO
        print('  ✓ Ultralytics YOLO package installed')
        return True
    except ImportError:
        print('  ✗ Ultralytics not installed')
        print('    Run: pip install ultralytics')
        return False

def check_onnx():
    """Проверяет ONNX Runtime"""
    print('⚡ Checking ONNX Runtime...')
    try:
        import onnxruntime
        print('  ✓ ONNX Runtime installed')
        return True
    except ImportError:
        print('  ✗ ONNX Runtime not installed')
        print('    Run: pip install onnxruntime')
        return False

def check_fastapi():
    """Проверяет FastAPI"""
    print('🌐 Checking FastAPI...')
    try:
        from fastapi import FastAPI
        print('  ✓ FastAPI installed')
        return True
    except ImportError:
        print('  ✗ FastAPI not installed')
        print('    Run: pip install fastapi uvicorn')
        return False

def check_model():
    """Проверяет наличие модели"""
    print('🎨 Checking model files...')
    model_files = [
        'backend/best.pt',
        'backend/best.onnx',
        'backend/best_quantized.onnx'
    ]

    found = []
    for model_file in model_files:
        if os.path.exists(model_file):
            size_mb = os.path.getsize(model_file) / (1024 * 1024)
            found.append(model_file)
            print(f'  ✓ {model_file} ({size_mb:.2f} MB)')
        else:
            print(f'  ⚠ {model_file} not found (will be created)')

    if found:
        print(f'  ✓ Found {len(found)} model file(s)')
        return True
    else:
        print('  ✗ No model files found')
        print('    Place best.pt in backend/ directory')
        return False

def check_directories():
    """Проверяет директории"""
    print('📁 Checking directories...')
    dirs = ['uploads', 'results', 'frontend', 'backend']
    all_exist = True
    for d in dirs:
        if os.path.exists(d):
            print(f'  ✓ {d}/ exists')
        else:
            print(f'  ⚠ {d}/ will be created')
            all_exist = False
    return all_exist

def main():
    print('╔════════════════════════════════════════════════╗')
    print('║       SafetyGuard Setup Check v1.0.0              ║')
    print('╚════════════════════════════════════════════════╝')
    print()

    checks = [
        ('Redis', check_redis),
        ('OpenCV', check_opencv),
        ('YOLO', check_yolo),
        ('ONNX', check_onnx),
        ('FastAPI', check_fastapi),
        ('Model', check_model),
        ('Directories', check_directories)
    ]

    results = []
    for name, check_func in checks:
        print()
        result = check_func()
        results.append((name, result))

    print()
    print('╔════════════════════════════════════════════════╗')
    print('║                    Summary                            ║')
    print('╚════════════════════════════════════════════════╝')
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = '✓ PASS' if result else '✗ FAIL'
        print(f'  {status} - {name}')

    print()
    print(f'Result: {passed}/{total} checks passed')
    print()

    if passed == total:
        print('🎉 All checks passed! SafetyGuard is ready to run.')
        print()
        print('Start with:')
        print('  Terminal 1: uvicorn backend.main:app --reload')
        print('  Terminal 2: python backend/worker.py')
        print()
        print('Or use the start script:')
        print('  ./start.sh')
        return 0
    else:
        print('⚠ Some checks failed. Please fix the issues above.')
        return 1

if __name__ == '__main__':
    sys.exit(main())
