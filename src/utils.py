from models import *
from agents import *
from prompts import *
import json
from datasets import load_dataset

SYSTEM_PROMPT_MAPPING = {
    "judge": JUDGE_PROMPT,
    "rater10": RATER_PROMPT_10,
    "multi-rater5": MULTI_RATER_PROMPT_5,
    "multi-rater10": MULTI_RATER_PROMPT_10,
    "multi-rater100": MULTI_RATER_PROMPT_100,
    "debate": DEBATE_PROMPT,
    "feedback": FEEDBACK_PROMPT,
    "multi-feedback": FEEDBACK_PROMPT,
    "feedback-agent-judge": MULTI_RATER_PROMPT_10,
    "versus": MULTI_RATER_PROMPT_10
}

def prepare_dataset(dataset_name):
    dataset = load_dataset(dataset_name)
    dataset = dataset["validation"]
    return dataset

def create_agent(task, agent_type, model_1, model_2="none", model_3="none"):
    system_prompt = SYSTEM_PROMPT_MAPPING[agent_type]
    if task == "evaluation":
        if agent_type == "judge":
            agent = Judge(model_1, system_prompt)
        elif agent_type.startswith("rater"):
            agent = Rater(model_1, system_prompt)
        elif agent_type.startswith("multi-rater"):
            agent = MultiRater(model_1, system_prompt, int(agent_type.replace("multi-rater", "")))
        elif agent_type == "debate":
            agent = Debate(model_1, model_2, system_prompt)
    elif task == "generation":
        if agent_type == "feedback":
            agent = Feedback(model_1, model_2, system_prompt)
        elif agent_type == "multi-feedback":
            agent = MultiFeedback(model_1, model_2, model_3, system_prompt)
        elif agent_type == "none":
            if model_1.startswith("gpt"):
                agent = GPT(model_1)
            else:
                agent = OpenSource(model_2)
        elif agent_type == "feedback-agent-judge":
            agent = FeedbackAgentJudge(system_prompt)
        elif agent_type == "versus":
            agent = Versus(system_prompt)
    
    return agent