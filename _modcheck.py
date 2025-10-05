import importlib, sys
sys.path.append('backend/app')
mods=['main','rl_obs','action_mapping','safety','crud','models','schemas','database']
for m in mods:
    try:
        importlib.import_module(m)
        print(m,'OK')
    except Exception as e:
        print(m,'FAIL',e)
