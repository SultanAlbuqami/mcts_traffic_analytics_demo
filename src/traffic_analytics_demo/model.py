from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass(frozen=True)
class ModelReport:
    split_strategy: str
    train_rows: int
    test_rows: int
    train_positive_rate: float
    test_positive_rate: float
    decision_threshold: float
    auc: float | None
    f1: float
    precision: float
    recall: float
    group_metrics: pd.DataFrame
    top_features: pd.DataFrame
    holdout_predictions: pd.DataFrame


def get_model_feature_columns(
    model_df: pd.DataFrame, target_col: str = "has_fatality"
) -> list[str]:
    return [
        c
        for c in model_df.columns
        if c
        not in [
            "road_id",
            "date",
            target_col,
            "fatalities",
            "injuries",
            "accidents",
            "severe",
            "severe_rate",
        ]
    ]


def _safe_auc(y_true: pd.Series, proba: np.ndarray) -> float | None:
    if pd.Series(y_true).nunique() < 2:
        return None
    return float(roc_auc_score(y_true, proba))


def _select_decision_threshold(y_true: pd.Series, proba: np.ndarray) -> float:
    candidate_thresholds = np.linspace(0.15, 0.75, 25)
    best_threshold = 0.50
    best_f1 = -1.0

    for threshold in candidate_thresholds:
        pred = (proba >= threshold).astype(int)
        score = float(f1_score(y_true, pred, zero_division=0))
        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)

    return best_threshold


def _split_train_test(
    df: pd.DataFrame,
    target_col: str,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if df[target_col].nunique() < 2:
        raise ValueError("Target must contain at least two classes to train the model.")

    if "date" in df.columns:
        dated = df.copy()
        dated["date"] = pd.to_datetime(dated["date"], errors="coerce")
        unique_dates = sorted(d for d in dated["date"].dropna().unique())
        if len(unique_dates) >= 8:
            test_dates = max(1, int(len(unique_dates) * test_size))
            cutoff = unique_dates[-test_dates]
            train_df = dated[dated["date"] < cutoff].copy()
            test_df = dated[dated["date"] >= cutoff].copy()
            if (
                not train_df.empty
                and not test_df.empty
                and train_df[target_col].nunique() >= 2
                and test_df[target_col].nunique() >= 2
            ):
                return train_df, test_df, "Temporal holdout"

    target = df[target_col].astype(int)
    class_counts = target.value_counts()
    if int(class_counts.min()) >= 2:
        train_idx, test_idx = train_test_split(
            df.index,
            test_size=test_size,
            random_state=random_state,
            stratify=target,
        )
        return df.loc[train_idx].copy(), df.loc[test_idx].copy(), "Stratified random split"

    rare_classes = class_counts[class_counts < 2].index
    candidate_test_idx = target[~target.isin(rare_classes)].index
    if len(candidate_test_idx) < 2:
        raise ValueError(
            "Insufficient target variation for a safe train/test split. "
            "Increase generated sample size (days/accidents/violations)."
        )

    desired_test_rows = max(1, int(round(len(df) * test_size)))
    max_test_rows = len(candidate_test_idx) - 1
    test_rows = min(desired_test_rows, max_test_rows)
    test_idx = pd.Series(candidate_test_idx).sample(n=test_rows, random_state=random_state).tolist()
    train_idx = df.index.difference(test_idx)

    train_df = df.loc[train_idx].copy()
    test_df = df.loc[test_idx].copy()
    if train_df[target_col].nunique() < 2:
        raise ValueError(
            "Unable to keep both target classes in training data. "
            "Increase generated sample size (days/accidents/violations)."
        )
    if test_df.empty:
        raise ValueError("Unable to create a non-empty test split from the available rows.")

    return train_df, test_df, "Random split (rare target class forced into train)"


def train_and_evaluate(
    model_df: pd.DataFrame,
    target_col: str = "has_fatality",
    random_state: int = 42,
) -> tuple[Pipeline, ModelReport]:
    df = model_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    feature_cols = get_model_feature_columns(df, target_col=target_col)
    if not feature_cols:
        raise ValueError("No usable feature columns found in model_df.")

    train_df, test_df, split_strategy = _split_train_test(
        df,
        target_col=target_col,
        test_size=0.25,
        random_state=random_state,
    )

    X_train = train_df[feature_cols]
    y_train = train_df[target_col].astype(int)
    X_test = test_df[feature_cols]
    y_test = test_df[target_col].astype(int)

    cat_cols = [c for c in X_train.columns if X_train[c].dtype == "object"]
    num_cols = [c for c in X_train.columns if c not in cat_cols]

    transformers = []
    if num_cols:
        transformers.append(("num", Pipeline(steps=[("scaler", StandardScaler())]), num_cols))
    if cat_cols:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols))

    pre = ColumnTransformer(transformers=transformers, remainder="drop")
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=random_state)
    pipe = Pipeline(steps=[("pre", pre), ("clf", clf)])

    pipe.fit(X_train, y_train)

    train_proba = pipe.predict_proba(X_train)[:, 1]
    decision_threshold = _select_decision_threshold(y_train, train_proba)
    proba = pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= decision_threshold).astype(int)

    auc = _safe_auc(y_test, proba)
    f1 = float(f1_score(y_test, pred, zero_division=0))
    precision = float(precision_score(y_test, pred, zero_division=0))
    recall = float(recall_score(y_test, pred, zero_division=0))

    gcols = [c for c in ["region", "road_type"] if c in test_df.columns]
    gm_rows = []
    if gcols:
        tmp = test_df[gcols].copy()
        tmp["y_true"] = y_test.values
        tmp["y_pred"] = pred
        tmp["y_proba"] = proba
        for gcol in gcols:
            for group_name, sub in tmp.groupby(gcol):
                gm_rows.append(
                    {
                        "group_col": gcol,
                        "group": str(group_name),
                        "n": int(len(sub)),
                        "positive_rate": float(sub["y_true"].mean()),
                        "pred_positive_rate": float(sub["y_pred"].mean()),
                        "auc": _safe_auc(sub["y_true"], sub["y_proba"]),
                        "f1": float(f1_score(sub["y_true"], sub["y_pred"], zero_division=0)),
                        "recall": float(
                            recall_score(sub["y_true"], sub["y_pred"], zero_division=0)
                        ),
                    }
                )
    group_metrics = pd.DataFrame(gm_rows)

    feature_names: list[str] = []
    if num_cols:
        feature_names.extend(num_cols)
    if cat_cols:
        ohe: OneHotEncoder = pipe.named_steps["pre"].named_transformers_["cat"]
        feature_names.extend(list(ohe.get_feature_names_out(cat_cols)))

    coefs = pipe.named_steps["clf"].coef_.ravel()
    top_features = pd.DataFrame({"feature": feature_names, "coef": coefs})
    top_features["abs_coef"] = top_features["coef"].abs()
    top_features = top_features.sort_values("abs_coef", ascending=False).head(15)[
        ["feature", "coef"]
    ]

    holdout_predictions = test_df[
        ["road_id", "date", "region", "city", "road_type", target_col]
    ].copy()
    holdout_predictions["predicted_risk"] = proba
    holdout_predictions["predicted_label"] = pred
    holdout_predictions["risk_band"] = pd.cut(
        holdout_predictions["predicted_risk"],
        bins=[-0.01, 0.20, 0.50, 0.75, 1.0],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)
    holdout_predictions = holdout_predictions.sort_values("predicted_risk", ascending=False)

    report = ModelReport(
        split_strategy=split_strategy,
        train_rows=int(len(train_df)),
        test_rows=int(len(test_df)),
        train_positive_rate=float(y_train.mean()),
        test_positive_rate=float(y_test.mean()),
        decision_threshold=decision_threshold,
        auc=auc,
        f1=f1,
        precision=precision,
        recall=recall,
        group_metrics=group_metrics,
        top_features=top_features,
        holdout_predictions=holdout_predictions,
    )
    return pipe, report


def report_to_markdown(rep: ModelReport) -> str:
    lines = []
    lines.append("# Model Report (Predictive)")
    lines.append("")
    lines.append("**Target:** has_fatality (road-day)")
    lines.append("")
    lines.append("## Validation Setup")
    lines.append(f"- Split strategy: {rep.split_strategy}")
    lines.append(f"- Train rows: {rep.train_rows:,}")
    lines.append(f"- Test rows: {rep.test_rows:,}")
    lines.append(f"- Train positive rate: {rep.train_positive_rate:.3f}")
    lines.append(f"- Test positive rate: {rep.test_positive_rate:.3f}")
    lines.append(f"- Decision threshold: {rep.decision_threshold:.2f}")
    lines.append("")
    lines.append("## Core Metrics")
    lines.append(
        f"- AUC: {rep.auc:.3f}" if rep.auc is not None else "- AUC: n/a (single-class holdout)"
    )
    lines.append(f"- F1: {rep.f1:.3f}")
    lines.append(f"- Precision: {rep.precision:.3f}")
    lines.append(f"- Recall: {rep.recall:.3f}")
    lines.append("")
    lines.append("## Top Signals (approx. from logistic coefficients)")
    lines.append("")
    lines.append("| Feature | Coef |")
    lines.append("|---|---:|")
    for _, row in rep.top_features.iterrows():
        lines.append(f"| {row['feature']} | {row['coef']:.4f} |")
    lines.append("")
    lines.append("## Highest-Risk Holdout Road-Days")
    lines.append("")
    lines.append(
        "| Road | Date | Region | City | Type | Actual Fatality | Predicted Risk | Risk Band |"
    )
    lines.append("|---|---|---|---|---|---:|---:|---|")
    for _, row in rep.holdout_predictions.head(10).iterrows():
        day = pd.to_datetime(row["date"]).date().isoformat() if pd.notna(row["date"]) else ""
        lines.append(
            f"| {row['road_id']} | {day} | {row['region']} | {row['city']} | {row['road_type']} | "
            f"{int(row['has_fatality'])} | {row['predicted_risk']:.3f} | {row['risk_band']} |"
        )
    lines.append("")
    lines.append("## Bias / Group Checks (sanity)")
    lines.append("")
    if rep.group_metrics.empty:
        lines.append("No group columns found to compute group metrics.")
    else:
        lines.append(
            "| Group Column | Group | n | Positive Rate | Pred + Rate | AUC | F1 | Recall |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for _, row in rep.group_metrics.iterrows():
            auc = "" if pd.isna(row["auc"]) else f"{row['auc']:.3f}"
            lines.append(
                f"| {row['group_col']} | {row['group']} | {int(row['n'])} | {row['positive_rate']:.3f} | "
                f"{row['pred_positive_rate']:.3f} | {auc} | {row['f1']:.3f} | {row['recall']:.3f} |"
            )
    lines.append("")
    lines.append("## Limitations")
    lines.append(
        "- Synthetic data: the goal is to demonstrate methodology, not claim production-level accuracy."
    )
    lines.append(
        "- This model supports prioritization and investigation, not automated enforcement decisions."
    )
    lines.append(
        "- Production maturity would add calibration, drift monitoring, challenger models, and human review."
    )
    return "\n".join(lines)
