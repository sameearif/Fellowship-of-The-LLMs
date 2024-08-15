import argparse
import statistics
import json
from sklearn.metrics import cohen_kappa_score
from glob import glob
from itertools import combinations
from utils import prepare_dataset
import random

parser = argparse.ArgumentParser(description="Evaluating GPT as evaluator arguments.")

parser.add_argument(
    "--dataset",
    type=str,
    help="Dataset to evaluate the model on",
    default="ma-eval/alpaca_eval",
    choices=["ma-eval/alpaca-eval", "ma-eval/mt-bench", "ma-eval/fair-eval", "ma-eval/pandalm-eval"]
)
parser.add_argument(
    "--agent_type",
    type=str,
    help="Type of agentic workflow",
    default="judge",
    choices=["judge", "rater5", "rater10", "rater100", "multi-rater5", "multi-rater10", "multi-rater100", "debate"]
)

args = parser.parse_args()

def get_y(dataset):
    y = []
    for data in dataset:
        y.append(data["winner"])
    return y

def create_permutations(files):
    subsets = []
    for r in range(1, len(files) + 1):
        subsets.extend(combinations(files, r))
    return subsets

def get_y_pred_pick(subset):
    if args.agent_type == "debate":
        y_pred = []
        predictions = []
        for file in subset:
            with open(file, "r") as f:
                predictions.append(json.load(f))

        for i in range(len(predictions[0])):
            temp = []
            for j in range(len(predictions)):
                pick = statistics.multimode([predictions[j][i]["pick_1"], predictions[j][i]["pick_2"], predictions[j][i]["pick_3"]])
                if pick[0] == "a":
                    pick = "model_a"
                elif pick[0] == "b":
                    pick = "model_b"
                else:
                    pick = "tie"
                temp.append(pick)
            mode = statistics.multimode(temp)
            if len(mode) > 1:
                y_pred.append("tie")
            else:
                y_pred.append(mode[0])
    else:
        y_pred = []
        predictions = []
        for file in subset:
            with open(file, "r") as f:
                predictions.append(json.load(f))

        for i in range(len(predictions[0])):
            temp = []
            for j in range(len(predictions)):
                temp.append(predictions[j][i]["pick"])
            mode = statistics.multimode(temp)
            if len(mode) > 1:
                y_pred.append("tie")
            else:
                y_pred.append(mode[0])

    return y_pred

def get_y_pred_scores(subset):
    y_pred = []
    predictions = []
    for file in subset:
        with open(file, "r") as f:
            predictions.append(json.load(f))
    
    for i in range(len(predictions[0])):
        temp = []
        for j in range(len(predictions)):
            if predictions[j][i]["score_1"] > predictions[j][i]["score_2"]:
                temp.append("model_a")
            elif predictions[j][i]["score_1"] < predictions[j][i]["score_2"]:
                temp.append("model_b")
            else:
                temp.append("tie")
        mode = statistics.multimode(temp)
        if len(mode) == 1:
            y_pred.append(mode[0])
        else:
            if len(mode) == 2 and "tie" in mode and "modle_a" in mode:
                y_pred.append("model_a")
            elif len(mode) == 2 and "tie" in mode and "modle_b" in mode:
                y_pred.append("model_b")
            elif len(mode) == 2 and "model_a" in mode and "modle_b" in mode:
                y_pred.append("tie")
            else:
                y_pred.append("tie")

    return y_pred

def compute_kappa(y, y_pred):
    y_filtered = []
    y_pred_filtered = []
    for i in range(len(y_pred)):
        y_filtered.append(y[i])
        y_pred_filtered.append(y_pred[i])
    return cohen_kappa_score(y_filtered, y_pred_filtered)


def calculate_cohens_kappa(dataset):
    print("Using Cohen's Kappa:")
    alphas = {}
    y = get_y(dataset)
    files = glob(f"outputs/evaluators/{args.dataset.split('/')[-1]}/{args.agent_type}/*.json")
    subsets = create_permutations(files)
    for subset in subsets:
        if args.agent_type.startswith("rater") or args.agent_type.startswith("multi-rater") or args.agent_type == "debate":
            y_pred = get_y_pred_scores(subset)
        elif args.agent_type == "judge":
            y_pred = get_y_pred_pick(subset)
        alpha = compute_kappa(y, y_pred)
        key = []
        for file in subset:
            key.append(file.split("/")[-1].replace(".json", "").replace(f"{args.agent_type}_", "").replace("_none", ""))
        alphas[tuple(key)] = alpha
    
    sorted_accuracies = sorted(alphas.items(), key=lambda item: item[1], reverse=True)
    with open(f"kappa.json", "w") as f:
        json.dump(sorted_accuracies, f)

def main():
    dataset = prepare_dataset(args.dataset)
    calculate_cohens_kappa(dataset)

if __name__ == "__main__":
    main()