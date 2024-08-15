JUDGE_PROMPT = """Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Answer options:
A: If response by assistant A is better
B: If response by assistant B is better
C: If it is a tie

Use the following format to respond:
### Evaluation Evidence:
[Add your explanation here]

### Answer:
A or B or C"""

RATER_PROMPT_10 = """Please act as an impartial judge and evaluate the quality of the response provided by an AI assistants to the user question displayed below. Assign an overall score out of 10, where a higher score indicates better overall performance. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their response. Begin your evaluation by comparing the two responses and provide a short explanation. Do not allow the length of the response to influence your evaluation.

Use the following format to respond:
### Evaluation Evidence:
[Add your explanation here]

### Overall Score:
X/10"""

MULTI_RATER_PROMPT_5 = """Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Each response receives an overall score out of 5, where a higher score indicates better overall performance. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation.

Use the following format to respond:
### Evaluation Evidence:
[Add your explanation here]

### Score Assistant A:
X/5

### Score Assistant B:
Y/5"""

MULTI_RATER_PROMPT_10 = """Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Each response receives an overall score out of 10, where a higher score indicates better overall performance. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation.

Use the following format to respond:
### Evaluation Evidence:
[Add your explanation here]

### Score Assistant A:
X/10

### Score Assistant B:
Y/10"""

MULTI_RATER_PROMPT_100 = """Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Each response receives an overall score out of 100, where a higher score indicates better overall performance. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation.

Use the following format to respond:
### Evaluation Evidence:
[Add your explanation here]

### Score Assistant A:
X/100

### Score Assistant B:
Y/100"""

DEBATE_PROMPT = """We would like to request your feedback on the performance of two AI assistants in response to the user question. There are a few other referee assigned the same task, it's your responsibility to discuss with them and think critically before you make your final judgement.
Each response receives an overall score on a scale of 1 to 10, where a higher score indicates better overall performance. You should choose the assistant that follows the user's instructions and answers the user's question better. You don't necessarily have to agree with others. 
Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation."""

FEEDBACK_PROMPT = """Please give constructive feedback on how to improve the response provided by an AI assistant to the user question. 
Your evaluation should consider factors such as the instruction following (the response should align with the user instructions), helpfulness, relevance, accuracy, and creativity of the response.
Assign an overall score out of 10, up to one decimal place, where a higher score indicates better overall performance.

Use the following format to respond:
### Evaluation:
[Add your evaluation here]

### Overall Score:
X/10

### Feedback:
[Add your feedback here]"""
