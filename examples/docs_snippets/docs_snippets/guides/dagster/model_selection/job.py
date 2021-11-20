# isort:skip_file
# load_iris_data_start

import pandas as pd
import sklearn.datasets
from sklearn.model_selection import train_test_split
from dagster import Out, job, op


@op(out={"training_set": Out(pd.DataFrame), "test_set": Out(pd.DataFrame)})
def load_iris_data():
    df = sklearn.datasets.load_iris(as_frame=True)["frame"]
    # set random_state here to get reproducible results
    training_set, test_set = train_test_split(df, test_size=0.33, random_state=5)
    return training_set, test_set


# load_iris_data_end

# serialize_hparams_start


def serialize_hparams(hparams):
    parts = []
    for k in sorted(hparams.keys()):
        val = str(hparams[k]).replace(r"^-", "neg").replace(".", "_")
        parts.append(f"{k}_eq_{val}")
    return "__".join(parts)


# serialize_hparams_end
# split_dataset_start


def split_dataset(df):
    features = df[
        ["sepal length (cm)", "sepal width (cm)", "petal length (cm)", "petal width (cm)"]
    ]
    target = df["target"]
    return features, target


# split_dataset_end
# generate_candidate_model_architectures_start

from dagster import DynamicOut, DynamicOutput
from sklearn.model_selection import ParameterGrid


@op(
    # "lr": logistic regression, "rf": random forest, "hparam": hyperparameter
    out={
        "lr_hparam_sets": DynamicOut(dict),
        "rf_hparam_sets": DynamicOut(dict),
    }
)
def generate_candidate_model_architectures():

    # logistic regression
    lr_grid = ParameterGrid({"C": np.logspace(0, 4, 5)})
    for hparams in lr_grid:
        yield DynamicOutput(
            output_name="lr_hparam_sets",
            mapping_key=serialize_hparams(hparams),
            value=hparams,
        )

    rf_grid = ParameterGrid(
        {
            "n_estimators": [10, 1000],
            "max_depth": [5, 30, None],
            "min_samples_leaf": [1, 10, 100],
        }
    )
    for hparams in rf_grid:
        yield DynamicOutput(
            output_name="rf_hparam_sets",
            mapping_key=serialize_hparams(hparams),
            value=hparams,
        )


# generate_candidate_model_architectures_end
# analysis_ops_start


@op
def score_lr_architecture(training_set, hparams):
    feats, target = split_dataset(training_set)
    arch = LogisticRegression(**hparams)
    score = cross_val_score(arch, feats, target, cv=5).mean()
    return dict(arch=arch, hparams=hparams, score=score)


@op
def score_rf_architecture(training_set, hparams):
    feats, target = split_dataset(training_set)
    arch = RandomForestClassifier(**hparams)
    score = cross_val_score(arch, feats, target, cv=5).mean()
    return dict(arch=arch, hparams=hparams, score=score)


# analysis_ops_end
# summary_ops_start


@op
def select_best_architecture(context, lr_results, rf_results):
    all_results = lr_results + rf_results
    best_arch = max(all_results, key=lambda m: m["score"])
    return best_arch


@op
def compute_final_score(context, training_set, test_set, best_arch):
    train_feats, train_target = split_dataset(training_set)
    test_feats, test_target = split_dataset(test_set)
    final_score = best_arch["arch"].fit(train_feats, train_target).score(test_feats, test_target)
    return dict(**best_arch, score=final_score)


@op
def report_result(context, result):
    lines = [
        "Best model architecture",
        "-----------------------",
        f'Score: {result["score"]}',
        f'Algorithm: {type(result["arch"])}',
        "Hyperparameters:",
    ] + [f"  {k}: {v}" for k, v in result["hparams"].items()]
    context.log.info("\n".join(lines))


# summary_ops_end
# job_start


@job
def model_selection():
    training_set, test_set = load_iris_data()
    lr_hparam_sets, rf_hparam_sets = generate_candidate_model_architectures()
    lr_results = lr_hparam_sets.map(
        lambda hparams: score_lr_architecture(training_set, hparams)
    ).collect()
    rf_results = rf_hparam_sets.map(
        lambda hparams: score_rf_architecture(training_set, hparams)
    ).collect()
    best_arch = select_best_architecture(lr_results, rf_results)
    best_arch_with_final_score = compute_final_score(training_set, test_set, best_arch)
    report_result(best_arch_with_final_score)


# job_end
