import importlib, sys
sys.path.append('backend/app')
for m in ['schemas','crud','main']:
  try:
    importlib.import_module(m)
    print(m,'OK')
  except Exception as e:
    print(m,'FAIL',e)
