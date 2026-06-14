import pickle
with open('encoder.pkl', 'rb') as f:
    enc = pickle.load(f)
print(f"Encoder Classes: {list(enc.classes_)}")
