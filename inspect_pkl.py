import pickle
import json

def get_info(name):
    with open(name, 'rb') as f:
        obj = pickle.load(f)
    info = {"file": name}
    if hasattr(obj, 'feature_names_in_'):
        info["features"] = list(obj.feature_names_in_)
    if hasattr(obj, 'classes_'):
        info["classes"] = [str(c) for c in obj.classes_]
    if hasattr(obj, 'n_features_in_'):
        info["n_features"] = obj.n_features_in_
    return info

results = []
for f in ['model.pkl', 'scaler.pkl', 'encoder.pkl']:
    try:
        results.append(get_info(f))
    except:
        pass

print(json.dumps(results, indent=2))
