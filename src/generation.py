from datasets import load_dataset
from tqdm import tqdm
import os
import argparse
from pathlib import Path
import json

from utils import *

parser = argparse.ArgumentParser(description="Evaluating LLMs as evaluator arguments.")

parser.add_argument(
    "--generator",
    type=str,
    help="Model you want to use",
    default="gpt-4o",
    choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
)
parser.add_argument(
    "--reviewer_1",
    type=str,
    help="Model you want to use",
    default="none",
    choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
)
parser.add_argument(
    "--reviewer_2",
    type=str,
    help="Model you want to use",
    default="none",
    choices=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "google/gemma-2-9b-it", "google/gemma-2-27b-it"]
)
parser.add_argument(
    "--agent_type",
    type=str,
    help="Type of agentic workflow",
    default="none",
    choices=["none", "feedback", "multi-feedback"]
)
parser.add_argument(
    "--pick",
    type=bool,
    help="Pick between the respones of the feedback",
    default=True,
    choices=[True, False]
)
parser.add_argument(
    "--versus",
    type=bool,
    help="Versus a agent",
    default=False,
    choices=[True, False]
)
parser.add_argument(
    "--dataset",
    type=str,
    help="Dataset to evaluate the model on",
    default="ma-eval/argilla-capybara-prompts-subset",
    choices=["ma-eval/argilla-capybara-prompts-subset", "ma-eval/argilla-capybara-prompts", "ma-eval/no-robots"]
)

args = parser.parse_args()

def prepare_files(dataset):
    path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/"
    model_1 = args.generator
    if "/" in model_1:
        model_1 = model_1.split("/")[-1]
    model_2 = args.reviewer_1
    if "/" in model_2:
        model_2 = model_2.split("/")[-1]
    model_3 = args.reviewer_2
    if "/" in model_3:
        model_3 = model_3.split("/")[-1]

    if args.agent_type == "none":
        file = f"{model_1}.json"
    elif args.agent_type == "multi-feedback":
        file = f"{model_1}_{model_2}_{model_3}.json"
    else:
        file = f"{model_1}_{model_2}.json"

    if args.pick:
        file = f"{file.replace('.json', '')}_picks.json"
    
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
    model_1 = args.generator
    if "/" in model_1:
        model_1 = model_1.split("/")[-1]
    model_2 = args.reviewer_1
    if "/" in model_2:
        model_2 = model_2.split("/")[-1]
    model_3 = args.reviewer_2
    if "/" in model_3:
        model_3 = model_3.split("/")[-1]

    if args.agent_type == "none":
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}.json"
    elif args.agent_type == "multi-feedback":
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}_{model_2}_{model_3}.json"
    else:
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}_{model_2}.json"

    if args.pick:
        path = f"{path.replace('.json', '')}_picks.json"

    with open(path, "w") as f:
        json.dump(outputs, f)

def get_responses():
    model_1 = args.generator
    if "/" in model_1:
        model_1 = model_1.split("/")[-1]
    model_2 = args.reviewer_1
    if "/" in model_2:
        model_2 = model_2.split("/")[-1]
    model_3 = args.reviewer_2
    if "/" in model_3:
        model_3 = model_3.split("/")[-1]

    if args.agent_type == "none":
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}.json"
    elif args.agent_type == "multi-feedback":
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}_{model_2}_{model_3}.json"
    else:
        path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{model_1}_{model_2}.json"

    with open(path, "r") as f:
        responses = json.load(f)
    
    return responses

def get_versus_responses():
    path = f"outputs/generators/{args.dataset.split('/')[-1]}/{args.agent_type}/{args.against}.json"
    with open(path, "r") as f:
        responses = json.load(f)
    return responses

def generate(agent, dataset):
    outputs = prepare_files(dataset)
    for i, prompt in tqdm(enumerate(dataset["prompt"]), total=len(dataset)):
        if outputs[i] == []:
            try:
                output = agent.forward(prompt)
            except:
                output = "None"
                agent.clear()
            outputs[i] = (output)
            save_file(outputs)
        if args.agent_type == "none":
            agent.clear()

def versus(agent, dataset, responses, responses_against):
    outputs = prepare_files(dataset)
    for i, prompt in tqdm(enumerate(dataset["prompt"]), total=len(dataset)):
        out = agent.forward(prompt, responses[i], responses_against[i])
        outputs[i] = out
        save_file(outputs)
        save_file(outputs)

def pick(agent, dataset, responses):
    outputs = prepare_files(dataset)
    for i, prompt in tqdm(enumerate(dataset["prompt"]), total=len(dataset)):
        out = agent.forward(prompt, responses[i])
        outputs[i] = out
        save_file(outputs)

def main():
    if args.pick:
        agent = create_agent("evaluation", "feedback-agent-judge", args.model_1, args.model_2, args.judge)
    if args.versus:
        agent = create_agent("evaluation", "versus", args.model_1, args.model_2, args.judge)
    agent = create_agent("evaluation", args.agent_type, args.model_1, args.model_2, args.judge)
    dataset = prepare_dataset(args.dataset, args.agent_type, [args.model_1, args.model_2], args.n)
    if args.pick:
        responses = get_responses()
        pick(agent, dataset, responses)
    elif args.versus:
        responses = get_responses()
        versus_respones = get_versus_responses()
        versus(agent, dataset, responses, versus_respones)
    else:
        generate(agent, dataset)

if __name__ == "__main__":
    main()


