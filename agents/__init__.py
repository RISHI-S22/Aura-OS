from agents.base.agent_registry import agent_registry
from agents.research.research_agent import ResearchAgent
from agents.coding.coding_agent import CodingAgent
from agents.browser.browser_agent import BrowserAgent
from agents.computer.desktop_agent import DesktopAgent
from agents.personal.email_agent import EmailAgent
from agents.knowledge.document_agent import DocumentAgent

agent_registry.register(ResearchAgent())
agent_registry.register(CodingAgent())
agent_registry.register(BrowserAgent())
agent_registry.register(DesktopAgent())
agent_registry.register(EmailAgent())
agent_registry.register(DocumentAgent())
