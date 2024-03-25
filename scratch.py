# For test purpose.

from log import Logger
log = Logger.get_instance()


from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem, SoftwareEngine, HardwareType, Popularity, SoftwareType

user_agent_rotator = UserAgent(
            hardware_types=HardwareType.COMPUTER.value,
            software_types=SoftwareType.WEB_BROWSER.value,
            software_names=SoftwareName.CHROME.value, 
            operating_systems=OperatingSystem.WINDOWS.value,
            popularity=Popularity.POPULAR.value,
            limit=1000
            )
        # # Get list of user agents.
user_agents = user_agent_rotator.get_user_agents()
user_agent = ""
for ua in user_agents:
    if "Windows NT 10.0" in ua['user_agent']:
        user_agent = ua['user_agent']
        log.info(f"user_agent: {user_agent}")        

