import argparse
import os
from pathlib import Path
from tqdm import tqdm
import json
from models import *
from utils import *

parser = argparse.ArgumentParser(description="Evaluating LLMs as evaluator arguments.")

parser.add_argument(
    "--model_1",
    type=str,
    help="Model you want to use",
    default="gpt-4o",
    choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
)
parser.add_argument(
    "--model_2",
    type=str,
    help="Model you want to use",
    default="none",
    choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
)
parser.add_argument(
    "--judge",
    type=str,
    help="Judge for the debate",
    default="none",
)
parser.add_argument(
    "--agent_type",
    type=str,
    help="Type of agentic workflow",
    default="judge",
    choices=["judge", "rater10", "multi-rater5", "multi-rater10", "multi-rater100", "debate",]
)
parser.add_argument(
    "--dataset",
    type=str,
    help="Dataset to evaluate the model on",
    default="ma-eval/alpaca-eval",
    choices=["ma-eval/alpaca-eval", "ma-eval/mt-bench", "ma-eval/fair-eval", "ma-eval/pandalm-eval"]
)
parser.add_argument(
    "--n",
    type=int,
    help="Dataset to evaluate the model on",
)

args = parser.parse_args()

def prepare_files(dataset):
    path = f"outputs/evaluators/{args.dataset.split('/')[-1]}/{args.agent_type}/"
    model_1 = args.model_1
    if "/" in model_1:
        model_1 = args.model_1.split("/")[-1]
    model_2 = args.model_2
    if "/" in model_2:
        model_2 = args.model_2.split("/")[-1]

    file = f"{model_1}_{model_2}_{args.n}.json"
    if not os.path.exists(path):
        outputs = []
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        for _ in range(len(dataset)):
            outputs.append([])
    elif not os.path.exists(path + file):
        outputs = []
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        for _ in range(len(dataset)):
            outputs.append([])
    else:
        with open (path + file, "r") as f:
            outputs = json.load(f)
    
    return outputs

def save_file(outputs):
    model_1 = args.model_1
    if "/" in model_1:
        model_1 = args.model_1.split("/")[-1]
    model_2 = args.model_2
    if "/" in model_2:
        model_2 = args.model_2.split("/")[-1]
    judge = args.judge
    if "/" in judge:
        judge = args.judge.split("/")[-1]

    path = f"outputs/evaluators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}_{model_2}_{args.n}.json"
    with open(path, "w") as f:
        json.dump(outputs, f)

def evaluate(agent, dataset):
    outputs = prepare_files(dataset)
    for i, data in tqdm(enumerate(dataset), total=len(dataset)):
        if outputs[i] == []:
            response = agent.forward(data)
            outputs[i] = response
            save_file(outputs)

def main():
    agent = create_agent("evaluation", args.agent_type, args.model_1, args.model_2, args.judge)
    dataset = prepare_dataset(args.dataset, args.agent_type, [args.model_1, args.model_2], args.n)
    evaluate(agent, dataset)

if __name__ == "__main__":
    main()