from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class ScenarioCustom(object):
    def scenario_steps(self):
            # DEBUT SCENARIO
            self.step_timer()
            self.driver.get("https://www.selenium.dev/")

            self.step_timer()
            self.driver.find_element(By.CSS_SELECTOR, ".nav-item:nth-child(4) span").click()
            
            self.step_timer()
            self.driver.find_element(By.ID, "m-documentationwebdriver").click()
            
            self.step_timer(step_name="TEST0")
            self.driver.find_element(By.XPATH, "//*[@id=\"docsearch\"]/button").click()
            
            self.step_timer(step_name="TEST0")
            self.driver.find_element(By.ID, "docsearch-input").send_keys("test")
            
            self.step_timer(step_name="TEST0")
            WebDriverWait(self.driver, self.timeout).until(\
                EC.presence_of_element_located((By.XPATH, "//*[@id=\"docsearch-item-0\"]/a")))
            
            self.step_timer(step_name="TEST0")
            self.driver.find_element(By.XPATH, "//*[@id=\"docsearch-item-0\"]/a").click()
            
            self.step_timer()
            self.driver.find_element(By.CSS_SELECTOR, "#m-documentationlegacy > span").click()
            
            self.step_timer(step_name="TEST1")
            self.driver.find_element(By.CSS_SELECTOR, ".entry:nth-child(4) a").click()
            # step 10
            self.step_timer(step_name="TEST1")
            element = self.driver.find_element(By.ID, "m-documentation-li")
            
            self.step_timer()
            actions = ActionChains(self.driver)

            self.step_timer()
            actions.move_to_element(element).click_and_hold().perform()

            self.step_timer()
            element = self.driver.find_element(By.ID, "m-documentationoverview")
            
            self.step_timer()
            actions = ActionChains(self.driver)
            
            self.step_timer()
            actions.move_to_element(element).release().perform()
            
            self.step_timer()
            self.driver.find_element(By.ID, "m-documentation-li").click()
            
            self.step_timer()
            self.driver.find_element(By.CSS_SELECTOR, "#m-documentationoverview > span").click()
            # FIN SCENARIO