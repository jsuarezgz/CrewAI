
from crewai import LLM
from crewai import Agent, Task, Crew
from openai import OpenAI
import os
from dotenv import load_dotenv

from mcp import StdioServerParameters
from crewai_tools import CodeInterpreterTool, MCPServerAdapter

# Load environment variables from the .env file
load_dotenv()

llm = LLM(
    model=os.getenv("OPENROUTER_MODEL_NAME"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENROUTER_API_KEY")  # Force the env var for downstream clients


# Initilize the MCP Server
dojo_serverparams = StdioServerParameters(
    command="uvx",
    args=["../defectdojo-mcp"], # This runs the MCP server installed via uvx
    env={"UV_PYTHON": "3.12", **os.environ},
)
dojo_server_adapter = MCPServerAdapter(dojo_serverparams)

git_serverparams = StdioServerParameters(
    command="uvx",
    args=["../mcp-servers/src/git"], # This runs the MCP server installed via uvx
)
git_server_adapter = MCPServerAdapter(git_serverparams)


# Initialize the tools
code_interpreter = CodeInterpreterTool()
dojo_tools = dojo_server_adapter.tools
git_tools = git_server_adapter.tools

# Define the Agents
hacker_agent = Agent(
    role="Ethical Hacker",
    goal="Write and execute Python code to identify and exploit security vulnerabilities in this {url} application",
    backstory="An expert Python programmer who can write efficient code to Write Python scripts to scan, exploit, and adaptively interact with web applications, targeting authentication, injection, and misconfiguration vulnerabilities.",
    tools=[code_interpreter], # You can also enable code execution directly with "allow_code_execution=True" that automatically adds the CodeInterpreter
    llm=llm,
    verbose=True
)

analyst_agent = Agent(
    role="Vulnerability Analyst",
    goal="Retrieve findings from {platform} via {protocol}, perform risk analysis, generate reports and track remediation",
    tools = dojo_tools,
    backstory=(
        """
        As a Vulnerability Analyst mantain proactive security.
        Instead of waiting for a breach occur, help ensure known weaknesses are found and fixed before attackers can exploit them.
        Work with IT and Dev Teams to effective remediation of vulnerabilities.
        """
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

fix_agent = Agent(
    role="Remediation Manager",
    goal= "Automatically apply, test, and validate code or configuration changes to remediate identified security vulnerabilities, ensuring long-term system integrity.",
    tools = git_tools,
    backstory=(
        """
        A detail-oriented engineer specialized in patch management, secure coding practices,
        and continuous integration workflows. You collaborate with developers and analysts
        to ensure that all identified vulnerabilities are effectively mitigated through 
        validated code or system changes. You use version control, CI/CD systems, and 
        automated testing to ensure secure and stable remediations are deployed promptly.
        """
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

# Creating Tasks
audit_task = Task(
    description="Write a Python function to calculate the Fibonacci sequence up to the 10th number and print the result.",
    expected_output="The Fibonacci sequence up to the 10th number.",
    agent=hacker_agent,
)

analysis_task = Task(
    description=(
        """
        1. Vulnerability Identification:
           - Review results from penetration tests, static code analysis tools, and cloud security scanners.
           - Stay updated on emerging threats, CVEs, zero-days, and vendor disclosur
        2. Assessment & Triage:
           - Analyze and validate vulnerabilities to determine severity, exploitability, and potential business impact.
           - Eliminate false positives and duplicate findings to reduce noise.
           - Prioritize vulnerabilities based on risk factors such as CVSS scores, EPSS predictions, asset criticality, and exposure level.
       """
    ),
    expected_output=(
        """
        A structured and actionable Vulnerability Assessment Report (or Risk Report), 
        which provides clear insight into discovered security weaknesses, their potential impact, 
        and recommended remediation steps.
        """
    ),
    agent=analyst_agent
)

remediation_task = Task(
    description=(
        """
        1. Collaboration & Remediation Support:
           - Work closely with IT, development, DevOps, and infrastructure teams to advise on>
           - Open, track, and manage tickets in systems like Jira, ServiceNow, or Remedy.
           - Monitor patching cycles, configuration changes, and compensating controls.
        2. Reporting & Communication:
           - Generate reports for technical teams, management, and compliance auditors.
           - Escalate high-risk vulnerabilities and communicate clearly with stakeholders abo>
           - Support regulatory audits by maintaining accurate records of findings and remedi>
       """
    ),
    expected_output=(
        """
        """
    ),
    agent=fix_agent
)


crew = Crew(
    agents=[hacker_agent, analyst_agent, fix_agent],
    tasks=[audit_task, analysis_task, remediation_task],
    verbose=True
)

# Sepecify the inputs
inputs = {
    'url': 'url of the application to audit',
    'scan_tool': 'scan tool used to audit',
    'protocol': 'Model Context Protocol',
    'platform': 'Defect Dojo'
}

# Kick off the crew
result = crew.kickoff(inputs=inputs)

# Stop the MCP Server
dojo_server_adapter.stop()
git_server_adapter.stop()
