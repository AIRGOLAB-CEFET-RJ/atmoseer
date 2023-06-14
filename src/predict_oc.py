import torch
import torch.nn as nn
from train.ordinal_classification_net import OrdinalClassificationNet
import globals as globals
import pickle

pipeline_id = "A652_N"

#
# Load numpy arrays (stored in a pickle file) from disk
filename = globals.DATASETS_DIR + pipeline_id + ".pickle"
file = open(filename, 'rb')
(_, _, _, _, X_test, _) = pickle.load(file)
print(f"Shape of test data matrix: {X_test.shape}")

x = X_test[0:1, :, :]
print(f"Shape of one test example: {x.shape}")
print("Model input:")
print(x)

NUM_FEATURES = X_test.shape[2]
NUM_CLASSES = 5

#Create an instance of the model
model = OrdinalClassificationNet(in_channels=NUM_FEATURES, num_classes=NUM_CLASSES)

# Load the pretrained model weights from the file
model_path = globals.MODELS_DIR + "best_" + pipeline_id + "_OC.pt"  # Path to the pretrained model file
model.load_state_dict(torch.load(model_path))


# Set the model in evaluation (inference) mode.
model.eval()

# Make prediction using the loaded model
with torch.no_grad():
    output = model.predict(x)
    print(output)