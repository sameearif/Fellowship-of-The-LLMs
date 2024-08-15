from models import *
import re

MODES = ["persistent", "single-turn"]

class Judge:
    def __init__(self, model_name, system_prompt):
        self.model_name = model_name
        if self.model_name.startswith("gpt"):
            self.model = GPT(model_name, system_prompt)
        else:
            self.model = OpenSource(model_name, system_prompt)
        self.system_prompt = system_prompt
    
    def prepare_message(self, conversation_a, conversation_b, turn=1):
        if turn == 1:
            prompt = conversation_a[0]["content"]
            response_1 = conversation_a[1]["content"]
            response_2 = conversation_b[1]["content"]
            message = f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant A's Answer|>\n{response_1}\n<|The End of Assistant A's Answer|>\n<|The Start of Assistant B's Answer|>\n\n{response_2}<|The End of Assistant B's Answer|>\n\n"
        else:
            prompt_1 = conversation_a[0]["content"]
            prompt_2 = conversation_a[2]["content"]
            response_1_1 = conversation_a[1]["content"]
            response_1_2 = conversation_a[3]["content"]
            response_2_1 = conversation_b[1]["content"]
            response_2_2 = conversation_b[3]["content"]
            message = f"""<|Start of Assistant A's Conversation with User|>\n### User:\n{prompt_1}\n\n### Assistant A:\n{response_1_1}\n\n### User:\n{prompt_2}\n\n### Assistant A:\n{response_1_2}\n<|End of Assistant A's Conversation with User|>\n\n<|Start of Assistant B's Conversation with User|>\n### User:\n{prompt_1}\n\n### Assistant B:\n{response_2_1}\n\n### User:\n{prompt_2}\n\n### Assistant B:\n{response_2_2}\n<|End of Assistant B's Conversation with User|>\n\n"""
        return message
    
    def forward(self, data):
        turn_to_answer = 1
        message = self.prepare_message(data["conversation_a"], data["conversation_b"], data["turn"])
        response = self.model.forward(message)
        matches = re.findall(r"###\s*answer\s*:\s*\n\s*([abc])\b", response.lower())
        pick = ""
        if matches:
            pick = matches[0]
        else:
            turn_to_answer += 1
            response += "\n\n" + self.model.forward(f"What is your final answer? The only Answer options are:\nA: If response by assistant A is better\nB: If response by assistant B is better\nC: If it is a tie.\nReturn your final answer only. The answer should be in the following format:\n### answer:\nA or B or C")
            matches = re.findall(r"###\s*answer\s*:\s*\n\s*([abc])\b", response.lower())
            if matches:
                pick = matches[0]
        preference = ""
        if pick == "a":
            preference = "model_a"
        elif pick == "b":
            preference = "model_b"
        else:
            preference = "tie"
        self.model.clear()
        return {"response": response, "pick": preference, "turns_to_answer": turn_to_answer}

class Rater:
    def __init__(self, model_name, system_prompt):
        self.model_name = model_name
        if self.model_name.startswith("gpt"):
            self.model = GPT(model_name, system_prompt)
        else:
            self.model = OpenSource(model_name, system_prompt)
        self.system_prompt = system_prompt
    
    def forward(self, data):
        output = {}
        prompt = data["conversation_a"][0]["content"]
        model_responses = [data["conversation_a"][1]["content"], data["conversation_b"][1]["content"]]
        for i, model_response in enumerate(model_responses):
            turn_to_answer = 1
            response = self.model.forward(f"### Prompt:\n{prompt}\n\n### Response:\n{model_response}")
            matches = re.findall(r"###\s*overall\s*score\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            score = -1
            if matches:
                score = float(matches[0])
            else:
                turn_to_answer += 1
                response += "\n\n" + self.model.forward(f"What is the overall score out of 10? Return your final answer only. The answer should be in the following format:\n### Overall Score:\nX/10")
                matches = re.findall(r"###\s*overall\s*score\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score = float(matches[0])
            
            if i == 0:
                output["response_1"] = response
                output["score_1"] = score
                output["turns_to_answer_1"] = turn_to_answer
            elif i == 1:
                output["response_2"] = response
                output["score_2"] = score
                output["turns_to_answer_2"] = turn_to_answer
            self.model.clear()

        return output

class MultiRater:
    def __init__(self, model_name, system_prompt, score_type):
        self.model_name = model_name
        if self.model_name.startswith("gpt"):
            self.model = GPT(model_name, system_prompt)
        else:
            self.model = OpenSource(model_name, system_prompt)
        self.system_prompt = system_prompt
        self.score_type = score_type
    
    def forward(self, data):
        output = {}
        prompt = data["conversation_a"][0]["content"]
        response_1 = data["conversation_a"][1]["content"]
        response_2 = data["conversation_b"][1]["content"]
        turn_to_answer = 1
        response = self.model.forward(f"### Prompt:\n{prompt}\n\n### Response A:\n{response_1}\n\n### Response B:\n{response_2}")
        ### For score out of 5
        if self.score_type == 5:
            matches_a = re.findall(r"###\s*score\s*assistant\s*a\s*:\s*\n?\s*([0-5](?:\.\d+)?)/5\b", response.lower())
            matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-5](?:\.\d+)?)/5\b", response.lower())
        ### For score out of 10
        elif self.score_type == 10:
            matches_a = re.findall(r"###\s*score\s*assistant\s*a\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        ### For score out of 100
        elif self.score_type == 100:
            matches_a = re.findall(r"###\s*score\s*assistant\s*a\s*:\s*\n?\s*([0-9]?\d(?:\.\d+)?|100(?:\.0+)?)/100\b", response.lower())
            matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-9]?\d(?:\.\d+)?|100(?:\.0+)?)/100\b", response.lower())
        score_a = -1
        score_b = -1
        if matches_a:
            score_a = float(matches_a[0])
            if matches_b:
                score_b = float(matches_b[0])
            else:
                turn_to_answer += 1
                if self.score_type == 5:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 5? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/5\n\n### Score Assistant B:\nY/5")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-5](?:\.\d+)?)/5\b", response.lower())
                elif self.score_type == 10:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                elif self.score_type == 100:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 100? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/100\n\n### Score Assistant B:\nY/100")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-9]?\d(?:\.\d+)?|100(?:\.0+)?)/100\b", response.lower())

                if matches_b:
                    score_b = float(matches_b[0])
        else:
            turn_to_answer += 1
            if self.score_type == 5:
                response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 5? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/5\n\n### Score Assistant B:\nY/5")
                matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-5](?:\.\d+)?)/5\b", response.lower())
            elif self.score_type == 10:
                response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10")
                matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            elif self.score_type == 100:
                response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 100? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/100\n\n### Score Assistant B:\nY/100")
                matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-9]?\d(?:\.\d+)?|100(?:\.0+)?)/100\b", response.lower())
            if matches_a:
                score_a = float(matches_a[0])
            if matches_b:
                score_b = float(matches_b[0])
            else:
                turn_to_answer += 1
                if self.score_type == 5:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 5? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/5\n\n### Score Assistant B:\nY/5")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-5](?:\.\d+)?)/5\b", response.lower())
                elif self.score_type == 10:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                elif self.score_type == 100:
                    response += "\n\n" + self.model.forward(f"What is the overall score for each response out of 100? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/100\n\n### Score Assistant B:\nY/100")
                    matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*([0-9]?\d(?:\.\d+)?|100(?:\.0+)?)/100\b", response.lower())
                if matches_a:
                    score_a = float(matches_a[0])
                if matches_b:
                    score_b = float(matches_b[0])

        output["response"] = response
        output["score_1"] = score_a
        output["score_2"] = score_b
        output["turns_to_answer"] = turn_to_answer
        
        self.model.clear()
        return output

class Debate:
    def __init__(self, model_1, model_2, system_prompt):
        if model_2.startswith("gpt"):
            self.model_1 = GPT(model_2, system_prompt)
        else:
            self.model_1 = OpenSource(model_2, system_prompt)
        
        if model_2.startswith("gpt"):
            self.model_2 = GPT(model_2, system_prompt)
        else:
            self.model_2 = OpenSource(model_2, system_prompt)
        
        if model_2.startswith("gpt"):
            self.model_3 = GPT(model_1, system_prompt)
        else:
            self.model_3 = OpenSource(model_1, system_prompt)

    def create_message(self, prompt, assistant_1, assistant_2, conversation_history):
        convo = self.create_convo_message(conversation_history)
        if convo == "":
            message = f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant 1's Answer|>\n{assistant_1}\n<|The End of Assistant 1's Answer|>\n<|The Start of Assistant 2's Answer|>\n\n{assistant_2}<|The End of Assistant 2's Answer|>"
            return message
        message = f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant 1's Answer|>\n{assistant_1}\n<|The End of Assistant 1's Answer|>\n<|The Start of Assistant 2's Answer|>\n{assistant_2}\n<|The End of Assistant 2's Answer|>\n\nHere is your discussion history:\n{convo}"
        return message
    
    def create_convo_message(self, conversation_history):
        message = ""
        for turn in conversation_history:
            message = f'{message}**{turn[0]}**:\n"""{turn[1]}"""\n\n'
        return message

    def forward(self, data, n=2):
        assert n > 0, "Invalid feedback cycles. Number of feedback cycles should be greater than 0."
        output = {}
        prompt = data["conversation_a"][0]["content"]
        assistant_1 = data["conversation_a"][1]["content"]
        assistant_2 = data["conversation_b"][1]["content"]
        conversation_history = []
        for i in range(n):
            topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nYou are now General Public, one of the referees in this task. You are interested in the story and looking for updates on the investigation. Please think critically by yourself and note that it's your responsibility to choose one of which is the better first.\n\nNow it's your turn to speak General Public, please make your talk short and clear.\n**General Public**:"
            response_1 = self.model_1.forward(topic)
            conversation_history.append(["General Public", response_1])

            topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nYou are now Psychologist, one of the referees in this task. You will study human behavior and mental processes in order to understand and explain human behavior. Please help other people to determine which response is the better one.\n\nNow it's your turn to speak Psychologist, please make your talk short and clear.\n**Psychologist**:"
            response_2 = self.model_2.forward(topic)
            conversation_history.append(["Psychologist", response_2])

            topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nYou are now Critic, one of the referees in this task. You will check fluent writing, clear sentences, and good wording in summary writing. Your job is to question others judgement to make sure their judgement is well-considered and offer an alternative solution if two responses are at the same level.\n\nNow it's your turn to speak Critic, please make your talk short and clear.\n**Critic**:"
            response_3 = self.model_3.forward(topic)
            conversation_history.append(["Critic", response_3])

            output[f"response_1_{i + 1}"] = response_1
            output[f"response_2_{i + 1}"] = response_2
            output[f"response_3_{i + 1}"] = response_3
        
            self.model_1.clear()
            self.model_2.clear()
            self.model_3.clear()

        score_1_1 = 0
        score_2_1 = 0
        topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nYou are now General Public, one of the referees in this task. You are interested in the story and looking for updates on the investigation. Please think critically by yourself and note that it's your responsibility to choose one of which is the better first.\n\nNow it's your turn to speak Psychologist, please make your talk short and clear.\n\nPlease first provide a comprehensive explanation of your evaluation, avoiding any potential bias and ensuring that the order in which the responses were presented does not affect your judgment. Then, output two lines indicating the scores for Assistant 1 and 2 out of 10, respectively. Remember that you are not required to output the same value as other referees! Output with the following format strictly:\n### Evaluation evidence: [your explanation here]\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**General Public**:"
        response = self.model_1.forward(topic)
        matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        if matches:
            score_1_1 = float(matches[0])
            matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_2_1 = float(matches[0])
            else:
                self.model_1.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                response += "\n\n" + self.model_1.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**General Public**:")
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_1 = float(matches[0])
                else:
                    score_1_1 = 0
        else:
            self.model_1.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
            response += "\n\n" + self.model_1.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**General Public**:")
            matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_1_1 = float(matches[0])
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_1 = float(matches[0])
                else:
                    self.model_1.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                    self.model_1.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**General Public**:")
                    matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                    if matches:
                        score_2_1 = float(matches[0])
                    else:
                        score_1_1 = 0

        output["response_1"] = response

        score_1_2 = 0
        score_2_2 = 0

        topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nnYou are now Psychologist, one of the referees in this task. You will study human behavior and mental processes in order to understand and explain human behavior. Please help other people to determine which response is the better one.\n\nNow it's your turn to speak Psychologist, please make your talk short and clear.\n\nPlease first provide a comprehensive explanation of your evaluation, avoiding any potential bias and ensuring that the order in which the responses were presented does not affect your judgment. Then, output two lines indicating the scores for Assistant 1 and 2 out of 10, respectively. Remember that you are not required to output the same value as other referees! Output with the following format strictly:\n### Evaluation evidence: [your explanation here]\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Psychologist**:"
        response = self.model_2.forward(topic)
        matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        if matches:
            score_1_2 = float(matches[0])
            matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_2_2 = float(matches[0])
            else:
                self.model_2.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                response += "\n\n" + self.model_2.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Psychologist**:")
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_2 = float(matches[0])
                else:
                    score_1_2 = 0
        else:
            self.model_2.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
            self.model_2.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Psychologist**:")
            matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_1_2 = float(matches[0])
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_2 = float(matches[0])
                else:
                    self.model_2.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                    response += "\n\n" + self.model_2.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Psychologist**:")
                    matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                    if matches:
                        score_2_2 = float(matches[0])
                    else:
                        score_1_2 = 0

        output["response_2"] = response

        score_1_3 = 0
        score_2_3 = 0

        topic = self.create_message(prompt, assistant_1, assistant_2, conversation_history) + "\n\nYou are now Critic, one of the referees in this task. You will check fluent writing, clear sentences, and good wording in summary writing. Your job is to question others judgement to make sure their judgement is well-considered and offer an alternative solution if two responses are at the same level.\n\nNow it's your turn to speak Critic, please make your talk short and clear.\n\nPlease first provide a comprehensive explanation of your evaluation, avoiding any potential bias and ensuring that the order in which the responses were presented does not affect your judgment. Then, output two lines indicating the scores for Assistant 1 and 2 out of 10, respectively. Remember that you are not required to output the same value as other referees! Output with the following format strictly:\n### Evaluation evidence: [your explanation here]\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Critic**:"
        response = self.model_3.forward(topic)
        matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        if matches:
            score_1_3 = float(matches[0])
            matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_2_3 = float(matches[0])
            else:
                self.model_3.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                response += "\n\n" + self.model_3.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Critic**:")
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_3 = float(matches[0])
                else:
                    score_1_3 = 0
        else:
            self.model_3.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
            response += "\n\n" + self.model_3.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Critic**:")
            matches = re.findall(r"###\s*score\s*assistant\s*1\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
            if matches:
                score_1_3 = float(matches[0])
                matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                if matches:
                    score_2_3 = float(matches[0])
                else:
                    self.model_3.clear([{"role": "user", "content": topic}, {"role": "assistant", "content": response}])
                    self.model_3.forward("What are your final scores?  Return your final answers only. Output with the following format strictly:\n### Score Assistant 1: X/10\n### Score Assistant 2: Y/10\n**Critic**:")
                    matches = re.findall(r"###\s*score\s*assistant\s*2\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
                    if matches:
                        score_2_3 = float(matches[0])
                    else:
                        score_1_3 = 0

        output["response_3"] = response
        output["score_1"] = (score_1_1 + score_1_2 + score_1_3)/3
        output["score_2"] = (score_2_1 + score_2_2 + score_2_3)/3
        
        self.model_1.clear()
        self.model_2.clear()
        self.model_3.clear()
        return output

class Feedback:
    def __init__(self, generator, reviewer, reviewer_sys):
        self.client = Together()
        self.generator = generator
        self.reviewer = reviewer
        self.generator_messages = []
        self.reviewer_sys = reviewer_sys
        self.reviewer_messages = [{"role": "system", "content": self.reviewer_sys}]
    def get_response(self, model, messages):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            stream=False
        )
        return response.choices[0].message.content
    def clear(self):
        self.generator_messages = []
        self.reviewer_messages = [{"role": "system", "content": self.reviewer_sys}]
    def forward(self, prompt, n=3):
        output = {}
        for i in range(n):
            if i == 0:
                self.generator_messages.append({"role": "user", "content": prompt})
                x = self.get_response(self.generator, self.generator_messages)
                self.generator_messages.append({"role": "assistant", "content": x})

                self.reviewer_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]"})
                try:
                    f = self.get_response(self.reviewer, self.reviewer_messages)
                except:
                    f = ""
                self.reviewer_messages.append({"role": "assistant", "content": f})
                output[f"response_{i + 1}"] = x
                output[f"feedback_{i + 1}"] = f
            else:
                if f != "":
                    self.generator_messages.append({"role": "user", "content": f"Update your response based on the following feedback:\n[Start of Feedback]\n{f}\n[End of Feedback]\n\nDo not engage in formalities such as 'Thank you for your feedback' or 'Here is an updated version...' etc, just update the response."})
                    x = self.get_response(self.generator, self.generator_messages)
                    self.generator_messages.append({"role": "assistant", "content": x})
                    
                    if i != 2:
                        self.reviewer_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]\n\nGive feedback on the updated response."})
                        try:
                            f = self.get_response(self.reviewer, self.reviewer_messages)
                        except:
                            f = ""
                        self.reviewer_messages.append({"role": "assistant", "content": f})

                    output[f"response_{i + 1}"] = x
                    if i != 2:
                        output[f"feedback_{i + 1}"] = f
        self.clear()
        return output
    
class MultiFeedback:
    def __init__(self, generator, reviewer1, reviewer2, reviewer_sys):
        self.client = Together()
        self.generator = generator
        self.reviewer1 = reviewer1
        self.reviewer2 = reviewer2
        self.generator_messages = []
        self.reviewer_sys = reviewer_sys
        self.reviewer1_messages = [{"role": "system", "content": self.reviewer_sys}]
        self.reviewer2_messages = [{"role": "system", "content": self.reviewer_sys}]
    def get_response(self, model, messages):
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0,
            stream=False
        )
        return response.choices[0].message.content
    def clear(self):
        self.generator_messages = []
        self.reviewer1_messages = [{"role": "system", "content": self.reviewer_sys}]
        self.reviewer2_messages = [{"role": "system", "content": self.reviewer_sys}]
    def forward(self, prompt, n=3):
        output = {}
        for i in range(n):
            if i == 0:
                self.generator_messages.append({"role": "user", "content": prompt})
                x = self.get_response(self.generator, self.generator_messages)
                self.generator_messages.append({"role": "assistant", "content": x})

                self.reviewer1_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]"})
                f1 = self.get_response(self.reviewer1, self.reviewer1_messages)
                self.reviewer1_messages.append({"role": "assistant", "content": f1})

                self.reviewer2_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]"})
                try:
                    f2 = self.get_response(self.reviewer2, self.reviewer2_messages)
                except:
                    f2 = ""
                self.reviewer2_messages.append({"role": "assistant", "content": f2})
            else:
                if f2 != "":
                    self.generator_messages.append({"role": "user", "content": f"Update your response based on the feedback of the two agents:\n[Start of Agent 1's Feedback]\n{f1}\n[End of Agent 1's Feedback]\n\n[Start of Agent 2's Feedback]\n{f2}\n[End of Agent 2's Feedback]\n\nDo not engage in formalities such as 'Thank you for your feedback' or 'Here is an updated version...' etc, just update the response."})
                else:
                    self.generator_messages.append({"role": "user", "content": f"Update your response based on the feedback:\n[Start of Feedback]\n{f1}\n[End of Feedback]\n\nDo not engage in formalities such as 'Thank you for your feedback' or 'Here is an updated version...' etc, just update the response."})
                x = self.get_response(self.generator, self.generator_messages)
                self.generator_messages.append({"role": "assistant", "content": x})

                self.reviewer1_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]\n\nGive feedback on the updated response."})
                f1 = self.get_response(self.reviewer1, self.reviewer1_messages)
                self.reviewer1_messages.append({"role": "assistant", "content": f1})

                if f2 != "":
                    if i != 2:
                        self.reviewer2_messages.append({"role": "user", "content": f"[Start of User Question]\n{prompt}\n[End of User Question]\n\n[Start of Agent's Response]\n{x}\n[End of Agent's Response]\n\nGive feedback on the updated response."})
                        try:
                            f2 = self.get_response(self.reviewer2, self.reviewer2_messages)
                        except:
                            f2 = ""
                        self.reviewer2_messages.append({"role": "assistant", "content": f2})

            output[f"response_{i + 1}"] = x
            output[f"feedback_{i + 1}_1"] = f1
            output[f"feedback_{i + 1}_2"] = f2
        self.clear()
        return output
    
class FeedbackAgentJudge:
    def __init__(self, system_prompt):
        self.client = OpenAI()
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": self.system_prompt}]
    def get_response(self):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            temperature=0.0,
            stream=False
        )
        return response.choices[0].message.content
    def clear(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]
    def extract_answer(self, response):
        matches_a = re.findall(r"###\s*score\s*assistant\s*a\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        if matches_a:
            score_1 = float(matches_a[0])
        else:
            score_1 = -1
        if matches_b:
            score_2 = float(matches_b[0])
        else:
            score_2 = -1
        return (score_1, score_2)
    def forward(self, prompt, data):
        output = {}
        if "response_2" not in data:
            return {"pick_1": "response_1"}
        self.messages.append({"role": "user", "content": f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant A's Answer|>\n{data['response_1']}\n<|The End of Assistant A's Answer|>\n\n<|The Start of Assistant B's Answer|>\n{data['response_2']}\n<|The End of Assistant B's Answer|>"})
        response = self.get_response()
        self.messages.append({"role": "assistant", "content": response})
        scores = self.extract_answer(response)
        if scores[0] == -1:
            self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
            response += "\n\n" + self.get_response()
            scores = self.extract_answer(response)
        else:
            if scores[1] == -1:
                self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
                response += "\n\n" + self.get_response()
                scores = self.extract_answer(response)
        temp = ""
        if scores[0] > scores[1]:
            pick = "response_1"
        elif scores[0] < scores[1]:
            pick = "response_2"
        else:
            pick = "response_2"
            temp = "tie"
            
        self.clear()
        output["response_1"] = response
        output["score_1_1"] = scores[0]
        output["score_1_2"] = scores[1]
        output["pick_1"] = pick
        if temp == "tie":
            output["pick_1"] = temp

        if "response_3" not in data:
            return output
        
        self.messages.append({"role": "user", "content": f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant A's Answer|>\n{data['response_3']}\n<|The End of Assistant A's Answer|>\n\n<|The Start of Assistant B's Answer|>\n{data[pick]}\n<|The End of Assistant B's Answer|>"})
        response = self.get_response()
        self.messages.append({"role": "assistant", "content": response})
        scores = self.extract_answer(response)
        if scores[0] == -1:
            self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
            response += "\n\n" + self.get_response()
            scores = self.extract_answer(response)
        else:
            if scores[1] == -1:
                self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
                response += "\n\n" + self.get_response()
                scores = self.extract_answer(response)
        if scores[0] > scores[1]:
            pick = output["pick_1"]
        elif scores[0] < scores[1]:
            pick = "response_3"
        else:
            pick = "tie"
        self.clear()
        output["response_2"] = response
        output["score_2_1"] = scores[0]
        output["score_2_2"] = scores[1]
        output["pick_2"] = pick
        return output

class GPT:
    def __init__(self, model):
        self.client = OpenAI()
        self.model = model
        self.messages = []
    def forward(self, x):
        self.messages.append({"role": "user", "content": x})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.0,
            stream=False
        )
        response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response
    def clear(self):
        self.messages = []

class OpenSource:
    def __init__(self, model):
        self.client = Together()
        self.model = model
        self.messages = []
    def forward(self, x):
        self.messages.append({"role": "user", "content": x})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.0,
            stream=False
        )
        response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response
    def clear(self):
        self.messages = []

class Versus:
    def __init__(self, system_prompt):
        self.client = OpenAI()
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": self.system_prompt}]
    def get_response(self):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            temperature=0.0,
            stream=False
        )
        return response.choices[0].message.content
    def clear(self):
        self.messages = [{"role": "system", "content": self.system_prompt}]
    def extract_answer(self, response):
        matches_a = re.findall(r"###\s*score\s*assistant\s*a\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        matches_b = re.findall(r"###\s*score\s*assistant\s*b\s*:\s*\n?\s*(10|[0-9](?:\.\d+)?)/10\b", response.lower())
        if matches_a:
            score_1 = float(matches_a[0])
        else:
            score_1 = -1
        if matches_b:
            score_2 = float(matches_b[0])
        else:
            score_2 = -1
        return (score_1, score_2)
    def forward(self, prompt, response1, response2):
        output = {}
        self.messages.append({"role": "user", "content": f"<|Start of User Question|>\n{prompt}\n<|End of User Question|>\n\n<|The Start of Assistant A's Answer|>\n{response1}\n<|The End of Assistant A's Answer|>\n\n<|The Start of Assistant B's Answer|>\n{response2}\n<|The End of Assistant B's Answer|>"})
        response = self.get_response()
        self.messages.append({"role": "assistant", "content": response})
        scores = self.extract_answer(response)
        if scores[0] == -1:
            self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
            response += "\n\n" + self.get_response()
            scores = self.extract_answer(response)
        else:
            if scores[1] == -1:
                self.messages.append({"role": "user", "content": "What is the overall score for each response out of 10? Return your final answers only. The answer should be in the following format:\n### Score Assistant A:\nX/10\n\n### Score Assistant B:\nY/10"})
                response += "\n\n" + self.get_response()
                scores = self.extract_answer(response)
        temp = ""
        if scores[0] > scores[1]:
            pick = "agent"
        elif scores[0] < scores[1]:
            pick = "gpt"
        else:
            pick = "tie"
            
        self.clear()
        output["response"] = response
        output["winner"] = pick
        
        return output
