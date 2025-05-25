import os
from dotenv import load_dotenv
from crewai import LLM, Agent, Task, Crew
from crewai_tools import CodeInterpreterTool, MCPServerAdapter
from mcp import StdioServerParameters

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = LLM(
    model=os.getenv("OPENROUTER_MODEL_NAME"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")  # Ensure downstream compatibility

# MCP Server Parameters
dojo_env = os.environ.copy()
dojo_env["UV_PYTHON"] = "3.12"

dojo_serverparams = StdioServerParameters(
    command="uvx",
    args=["../defectdojo-mcp"],
    env=dojo_env
)

git_serverparams = StdioServerParameters(
    command="uvx",
    args=["../mcp-servers/src/git"]
)

# MCP Adapters
dojo_server_adapter = MCPServerAdapter(dojo_serverparams)
git_server_adapter = MCPServerAdapter(git_serverparams)

# Tools
code_interpreter = CodeInterpreterTool()
dojo_tools = dojo_server_adapter.tools
git_tools = git_server_adapter.tools

# Agents
hacker_agent = Agent(
    role="Ethical Hacker",
    goal="Identify and exploit security vulnerabilities in the {url} web application using Python-based techniques.",
    backstory="An expert Python programmer skilled in web exploitation, including authentication bypass, injection attacks, and misconfigurations.",
    tools=[code_interpreter],
    llm=llm,
    verbose=True
)

analyst_agent = Agent(
    role="Vulnerability Analyst",
    goal="Retrieve findings from {platform} via {protocol}, assess risks, and generate structured vulnerability reports.",
    backstory="Helps ensure vulnerabilities are detected and triaged before exploitation. Collaborates with technical teams to assess and prioritize findings.",
    tools=dojo_tools,
    llm=llm,
    allow_delegation=False,
    verbose=True
)

fix_agent = Agent(
    role="Remediation Manager",
    goal="Apply and validate remediations for identified vulnerabilities, ensuring secure and stable system updates.",
    backstory="An engineer focused on patch management and secure CI/CD practices, ensuring remediation efforts are fast, reliable, and documented.",
    tools=git_tools,
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Tasks
audit_task = Task(
    description="Perform an automated web security scan on {url}. Focus on authentication flaws, injection vectors, and misconfigurations.",
    expected_output="List of identified vulnerabilities with technical descriptions and potential exploitation paths.",
    agent=hacker_agent,
)

analysis_task = Task(
    description="""
        Analyze vulnerability data from DefectDojo via MCP.
        - Prioritize based on CVSS/EPSS scores and criticality.
        - Remove false positives and duplicates.
        - Classify severity and recommend mitigation strategies.
    """,
    expected_output="A detailed vulnerability assessment report prioritizing risks and outlining remediation recommendations.",
    agent=analyst_agent
)

remediation_task = Task(
    description="""
        Remediate high-priority issues using Git-based workflows.
        - Apply secure code/config changes.
        - Commit via Git with detailed messages.
        - Validate fixes with automated tests.
    """,
    expected_output="Validated code commits addressing vulnerabilities, with confirmation of successful mitigation.",
    agent=fix_agent
)

# Define the Crew
crew = Crew(
    agents=[hacker_agent, analyst_agent, fix_agent],
    tasks=[audit_task, analysis_task, remediation_task],
    verbose=True
)

# Inputs
inputs = {
    "url": "https://example.com",
    "scan_tool": "Zap",
    "protocol": "MCP",
    "platform": "Defect Dojo"
}

# Run
result = crew.kickoff(inputs=inputs)

# Shutdown MCP servers
dojo_server_adapter.stop()
git_server_adapter.stop()
