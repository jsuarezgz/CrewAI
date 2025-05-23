
from crewai import LLM
from crewai import Agent, Task, Crew
from openai import OpenAI
import os
from dotenv import load_dotenv

from mcp import StdioServerParameters
from crewai_tools import MCPServerAdapter

# Load environment variables from the .env file
load_dotenv()

#os.environ['OPENAI_API_BASE'] = os.getenv('OPENROUTER_BASE_URL')
#os.environ['OPENAI_MODEL_NAME'] = os.getenv('OPENROUTER_MODEL_NAME')
#os.environ['OPENAI_API_KEY'] = os.getenv('OPENROUTER_API_KEY')

llm = LLM(
    model=os.getenv("OPENROUTER_MODEL_NAME"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")  # Force the env var for downstream clients

serverparams = StdioServerParameters(
    command="uvx",
    args=["../defectdojo-mcp"], # This runs the MCP server installed via uvx
    env={"UV_PYTHON": "3.12", **os.environ},
)

mcp_server_adapter = MCPServerAdapter(serverparams)
mcp_tools = mcp_server_adapter.tools

# Define Agents
analyst = Agent(
    role="Vulnerability Analyst",
    goal="Retrieve findings from {platform} via {protocol}, perform risk analysis, generate reports and track remediation",
    tools = mcp_tools,
    backstory=(
        "As a Vulnerability Analyst mantain proactive security."
        "Instead of waiting for a breach occur, help ensure known weaknesses are found and fixed before attackers can exploit them." 
        "Work with IT and Dev Teams to effective remediation of vulnerabilities"
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Creating Tasks
analysis_task = Task(
    description=(
        "1. Vulnerability Identification:"
        "- Review results from penetration tests, static code analysis tools, and cloud security scanners."
        "- Stay updated on emerging threats, CVEs, zero-days, and vendor disclosur"
        "2. Assessment & Triage:"
        "- Analyze and validate vulnerabilities to determine severity, exploitability, and potential business impact."
        "- Eliminate false positives and duplicate findings to reduce noise."
        "Prioritize vulnerabilities based on risk factors such as CVSS scores, EPSS predictions, asset criticality, and exposure level."
        "3. Collaboration & Remediation Support:"
        " - Work closely with IT, development, DevOps, and infrastructure teams to advise on remediation strategies."
        "- Open, track, and manage tickets in systems like Jira, ServiceNow, or Remedy."
        "- Monitor patching cycles, configuration changes, and compensating controls."
        "4. Reporting & Communication"
        "- Generate reports for technical teams, management, and compliance auditors."
        "- Escalate high-risk vulnerabilities and communicate clearly with stakeholders about timelines and risk posture."
        "- Support regulatory audits by maintaining accurate records of findings and remediations."
    ),
    expected_output=(
        "A structured and actionable Vulnerability Assessment Report (or Risk Report), which provides clear insight into discovered security weaknesses, their potential impact, and recommended remediation steps"
    ),
    agent=analyst
)

crew = Crew(
    agents=[analyst],
    tasks=[analysis_task],
    verbose=True
)

# Sepecify the inputs
inputs = {
    'protocol': 'Model Context Protocol',
    'platform': 'Defect Dojo'
}

# Kick off the crew
result = crew.kickoff(inputs=inputs)

# Stop the MCP Server
mcp_server_adapter.stop()
