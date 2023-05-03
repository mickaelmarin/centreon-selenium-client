from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class ScenarioCustom(object):
    def run(self):
        try:
            #DEBUT SCENARIO
            self.step_timer()
            #self.step_timer(step_name="TEST1")
            #self.driver.get("https://www.google.com/")

            
            # FIN SCENARIO
            self.step_timer(last_step=True)
            self.build_centreon_output()

        except  Exception as e:
            self.step_timer(last_step=True, abort=True)
            self.build_centreon_output(abort = True)

if __name__ == "__main__":
    main = ScenarioCustom()
    main.run()