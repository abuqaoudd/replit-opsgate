# Engine package metadata stored as Python.

PACKAGE = {'name': 'opsgate-engine-foundation',
 'version': '7.1.0',
 'private': True,
 'type': 'module',
 'scripts': {'validate': 'python3 tools/opsgate.py validate-engine',
             'compile:frontend': 'python3 tools/opsgate.py compile-prompt routing:frontend-task',
             'state:migration': 'python3 tools/opsgate.py init-state routing:migration-task-missing-auth',
             'parse:report': 'python3 tools/opsgate.py parse-report fixtures/reports/sample-replit-final-report.md',
             'preflight': 'python3 tools/opsgate.py preflight routing:frontend-task',
             'check:paths': 'python3 tools/opsgate.py check-paths routing:frontend-task',
             'check:capabilities': 'python3 tools/opsgate.py check-capabilities '
                                   'routing:migration-task-missing-auth',
             'lint:prompt': 'python3 tools/opsgate.py lint-prompt fixtures/prompts/frontend-compiled-with-gate.md',
             'lint:report': 'python3 tools/opsgate.py lint-report fixtures/reports/sample-replit-final-report.md',
             'init:run': 'python3 tools/opsgate.py init-run routing:frontend-task',
             'intake': 'python3 tools/opsgate.py intake-request',
             'next-phase': 'python3 tools/opsgate.py next-phase-prompt state:ready-phased-state reports:parsed-sample-report',
             'route:frontend': 'python3 tools/opsgate.py route-request routing:frontend-task',
             'route:migration': 'python3 tools/opsgate.py route-request routing:migration-task-missing-auth'}}
