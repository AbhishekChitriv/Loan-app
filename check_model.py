import pickle
with open('model.pkl', 'rb') as f:
    model = pickle.load(f)
print(f"Model Classes: {getattr(model, 'classes_', 'No classes_ found')}")
