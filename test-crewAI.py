
from crewai_tools import ScrapeWebsiteTool, FileWriterTool, TXTSearchTool
from crewai import LLM
from crewai import Agent, Task, Crew
from openai import OpenAI
import os
from dotenv import load_dotenv

os.environ["OPENAI_API_KEY"] = "NA"

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

analyst = Agent(
    role="Data Analyst",
    goal="Analyze data trends in the market {topic}",
    backstory="An experienced data analyst with a background in economics ",
    llm=llm,
    allow_delegation=False,
    verbose=True
)

researcher = Agent(
    role="Market Researcher",
    goal="Gather information on market dynamics ",
    backstory="A diligent researcher with a keen eye for detail",
    allow_delegation=False,
    llm=llm,
    verbose=True
)

editor = Agent(
    role="Editor",
    goal="Edit a given blog post to align with "
         "the writing style of the organization 'https://medium.com/'. ",
    backstory="You are an editor who receives a financial analysis blog post "
              "from the Content Writer. "
              "Your goal is to review the blog post "
              "to ensure that it follows journalistic best practices,",
    llm=llm,
    allow_delegation=False,
    verbose=True
)

analysis_task = Task(
    description= "Collect recent market data and identify trends. ",
    expected_output="A report summarizing key trends in the market.",
    agent=analyst,
)

research_task = Task(
    description= "Research factors affecting market dynamics.",
    expected_output="An analysis of factors influencing the market.",
    agent=researcher,
)

edit = Task(
    description=("Proofread the given blog post for "
                 "grammatical errors and "
                 "alignment with the brand's voice."),
    expected_output="A well-written blog post in markdown format, "
                    "ready for publication, "
                    "each section should have 2 or 3 paragraphs.",
    agent=editor
)

crew = Crew(
    agents=[analyst, researcher, editor],
    tasks=[analysis_task, research_task, edit],
    verbose=True
)

inputs = {"topic":"NASDAQ in 2024"}
result = crew.kickoff(inputs=inputs)


from IPython.display import Markdown,display
display(Markdown(result))
