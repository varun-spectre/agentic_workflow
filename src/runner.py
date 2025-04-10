import re

class AgentRunner:
    def __init__(self, config, memory, llm_fn):
        self.config = config
        self.memory = memory
        self.llm_fn = llm_fn  # function that calls your LLM
        self.steps = 0
        self.retries = 0

    def extract_tag(self, text, tag):
        """Extract content from a specific tag like <plan> or <execute>"""
        pattern = f"<{tag}>(.*?)</{tag}>"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    def run(self, user_input: str):
        self.memory.add("user", user_input)

        while self.steps < self.config.max_steps:
            self.steps += 1
            print(f"\n🧠 Step {self.steps}")

            try:
                # Full prompt with memory
                context = self.memory.get_context()
                full_prompt = f"{context}\n\nUser: {user_input}"
                llm_response = self.llm_fn(full_prompt)
                self.memory.add("agent", llm_response)

                # 🔍 Extract stages
                plan = self.extract_tag(llm_response, "plan")
                execute_code = self.extract_tag(llm_response, "execute")
                solution = self.extract_tag(llm_response, "solution")

                if plan:
                    print(f"\n📝 Plan:\n{plan}")

                if execute_code:
                    print(f"\n⚙️ Executing Code:\n{execute_code}")
                    result = self.config.use_tool("code_executor", execute_code)
                    self.memory.add("tool", result)
                    print(f"\n✅ Execution Result:\n{result}")

                if solution:
                    print(f"\n💡 Final Solution:\n{solution}")
                    self.memory.add("agent", solution)
                    break  # finished successfully

            except Exception as e:
                self.retries += 1
                print(f"❌ Error: {str(e)} (Retry {self.retries}/{self.config.max_retries})")
                if self.retries >= self.config.max_retries:
                    print("🛑 Max retries reached.")
                    break
