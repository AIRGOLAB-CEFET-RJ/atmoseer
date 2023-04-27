from sklearn.ensemble import GradientBoostingClassifier
import numpy as np 

NAIVE_SUBSAMPLING_KEEP_RATIO = 0.05

# With negative subsampling (train/val/test): 13934/3142/10219.

def apply_subsampling(X, y, subsampling_strategy):
    assert subsampling_strategy in  ("NAIVE", "NEGATIVE")
    if subsampling_strategy == "NAIVE":
        return apply_naive_subsampling(X, y)
    else:
        return apply_negative_subsampling(X, y)

def apply_naive_subsampling(X, y):
    """
    Naive subsampling: keep all the positive instances and subsample the negative instances completely at random.
    """
    y_eq_zero_idxs = np.where(y == 0)[0]
    y_gt_zero_idxs = np.where(y > 0)[0]
    print(f' - Original sizes (target=0)/(target>0): ({y_eq_zero_idxs.shape[0]})/({y_gt_zero_idxs.shape[0]})')

    print(f" - Using keep ratio = {NAIVE_SUBSAMPLING_KEEP_RATIO}.")

    # Setting numpy seed value
    np.random.seed(0)

    mask = np.random.choice([True, False], size=y.shape[0], p=[
                            NAIVE_SUBSAMPLING_KEEP_RATIO, 1.0-NAIVE_SUBSAMPLING_KEEP_RATIO])
    y_train_subsample_idxs = np.where(mask == True)[0]

    print(f" - Subsample (total) size: {y_train_subsample_idxs.shape[0]}")
    idxs = np.intersect1d(y_eq_zero_idxs, y_train_subsample_idxs)
    print(f" - Subsample (target=0) size: {idxs.shape[0]}")

    idxs = np.union1d(idxs, y_gt_zero_idxs)
    X, y = X[idxs], y[idxs]
    y_eq_zero_idxs = np.where(y == 0)[0]
    y_gt_zero_idxs = np.where(y > 0)[0]
    print(f' - Resulting sizes (target=0)/(target>0): ({y_eq_zero_idxs.shape[0]})/({y_gt_zero_idxs.shape[0]})')

    return X, y

def apply_negative_subsampling(X_train, y_train):
    original_shape_X_train = X_train.shape
    
    X_train = X_train.reshape(len(X_train), -1)
    y_train[y_train>0] = 1    
    
    ###
    # Apply the steps of the negative sampling procedure
    ###

    # Step 1: Train "pilot" model
    clf, X_balanced, y_balanced = train_pilot_model(X_train, y_train)

    # Step 2: Score the negative examples with the pilot model
    y_proba_normalized = score_negative_examples(clf, X_balanced, y_balanced)

    # Step 3: Sample the negative examples proportionally to the scores
    X_sampled_negative = sample_from_negative_examples(X_balanced, y_balanced, y_proba_normalized)
    
    positive_examples = X_balanced[y_balanced==1]
    desired_num_examples = len(positive_examples)
    X_train_sampled = np.concatenate((positive_examples, X_sampled_negative))
    y_train_sampled = np.concatenate((np.ones(desired_num_examples), np.zeros(desired_num_examples)))
    X_train_sampled.shape, y_train_sampled.shape
    
    X_train_sampled = X_train_sampled.reshape((len(X_train_sampled), original_shape_X_train[1], original_shape_X_train[2]))
    y_train_sampled = y_train_sampled.reshape(-1, 1)

    return X_train_sampled, y_train_sampled

def train_pilot_model(X_train, y_train):
    y_eq_zero_idxs = np.where(y_train == 0)[0]
    y_gt_zero_idxs = np.where(y_train > 0)[0]
    print(f"Amounts of neg/pos examples: {len(y_eq_zero_idxs)}/{len(y_gt_zero_idxs)}")

    positive_examples = X_train[y_gt_zero_idxs]
    negative_examples = X_train[y_eq_zero_idxs]

    num_positive_examples = len(positive_examples)
    num_negative_examples = len(negative_examples)
    desired_num_examples = min(num_positive_examples, num_negative_examples)
    print(desired_num_examples)

    positive_indices = np.random.choice(num_positive_examples, size=desired_num_examples, replace=False)
    negative_indices = np.random.choice(num_negative_examples, size=desired_num_examples, replace=False)

    X_train_equalized = np.concatenate((positive_examples[positive_indices], negative_examples[negative_indices]))
    y_train_equalized = np.concatenate((np.ones(desired_num_examples), np.zeros(desired_num_examples)))

    assert len(y_train_equalized) == 2*desired_num_examples

    # Create a GradientBoostingClassifier object with default hyperparameters
    clf = GradientBoostingClassifier()

    # Train the classifier on the equalized training dataset
    clf.fit(X_train_equalized, y_train_equalized)
    
    return clf, X_train_equalized, y_train_equalized

def score_negative_examples(clf, X_balanced, y_balanced):
    X_balanced_negative = X_balanced[y_balanced==0]
    y_balanced_negative = y_balanced[y_balanced==0]

    # Get predicted probabilities on the negative samples
    y_proba = clf.predict_proba(X_balanced_negative)

    # The predicted probabilities for the negative class (class 0) are in the first column
    y_proba_negative = y_proba[:, 0]

    # Normalize the probabilities to sum to 1
    y_proba_normalized = y_proba_negative / np.sum(y_proba_negative)

    print(f"Normalized scores for the first 5 negative examples: {y_proba_normalized[:5]}")
    print(f"Correct labels for the first 5 negative examples: {y_balanced_negative[:5]}")
    
    return y_proba_normalized

def sample_from_negative_examples(X_balanced, y_balanced, y_proba_normalized):
    # Create an array of indices corresponding to X_balanced_negative
    X_balanced_negative = X_balanced[y_balanced==0]
    indices = np.arange(len(X_balanced_negative))

    positive_examples = X_balanced[y_balanced==1]
    num_positive_examples = len(positive_examples)

    # Sample the indices using the normalized probabilities
    sampled_indices = np.random.choice(indices, size=num_positive_examples, replace=False, p=y_proba_normalized)

    # Use the sampled indices to get a subset "hard" negative examples
    X_sampled_negative = X_balanced_negative[sampled_indices]

    return X_sampled_negative
