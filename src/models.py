from openai import OpenAI
from together import Together

class GPT:
    def __init__(self, model, system_prompt):
        self.client = OpenAI()
        self.model = model
        self.system_prompt = system_prompt
        if self.system_prompt == "":
            self.messages = []
        else:
            self.messages = [{"role": "system", "content": self.system_prompt}]
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
    def clear(self, messages=None):
        self.messages = [{"role": "system", "content": self.system_prompt}]
        if messages:
            for message in messages:
                self.messages.append(message)

class OpenSource:
    def __init__(self, model, system_prompt):
        self.client = Together()
        self.model = model
        self.system_prompt = system_prompt
        self.messages = [{"role": "system", "content": system_prompt}]
    def forward(self, x):
        self.messages.append({"role": "user", "content": x})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.0,
        )
        response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response
    def clear(self, messages=None):
        self.messages = [{"role": "system", "content": self.system_prompt}]
        if messages:
            for message in messages:
                self.messages.append(message)

