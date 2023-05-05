#! /opt/python38-venv/bin/python3
import sys, os, re, argparse, importlib
import time
import ast
from selenium import webdriver

# from xvfbwrapper import Xvfb
# display = Xvfb()

sys.tracebacklimit=0

class Manage_options(object):
    def __init__(self, pattern):
        
        self.options_dict = {}
        self.pattern = pattern
        self.global_timeout = 0

    def validate_syntax_gwct_eswct(self, value):
        
        pattern = re.compile(self.pattern[0])
            
        if not pattern.match(value):
            
            raise argparse.ArgumentTypeError(
                "Incorrect syntax, please refer to help with selenium-client.py -h"
            )
        else:
            return value
    def validate_syntax_beswct(self, value):
        
        pattern = re.compile(self.pattern[1])
            
        if not pattern.match(value):
            
            raise argparse.ArgumentTypeError(
                "Incorrect syntax, please refer to help with selenium-client.py -h"
            )
        else:
            return value

    def validate_semantic(self, option, gwct_list, parser):
        
        errors = ""
        
        if int(gwct_list[2]) > self.global_timeout:
            errors += f"\nTimeout can not > global timeout of global_warn_crit_timeout({self.global_timeout}) in the option: {option}"
        
        if int(gwct_list[0]) >= int(gwct_list[1]):
            errors += f"\nWarning: {gwct_list[0]} can not > Critical: {gwct_list[1]} in the option: {option}"
        
        if int(gwct_list[0]) >= int(gwct_list[2]) or \
            int(gwct_list[1]) >= int(gwct_list[2]):
                errors += f"\nWarning or Critical can not > Timeout {gwct_list[2]} in the option: {option}"

        if len(errors) > 0:
            # return errors
            parser.print_usage()
            raise  argparse.ArgumentTypeError(errors)

    def validate_scenario_dir(self, dir):
        if not os.path.isdir(f'{os.path.dirname(__file__)}/{dir}'):
            raise  argparse.ArgumentTypeError(f'{dir} isn\'t a directory')
        else:
            return dir       

    def build_options_dict(self, option, value, parser):
        if option in ["headless"]:
            self.options_dict[option] = value
        if option in [
                "scenarios_dir",
                "scenario",
                "browser",
                "selenium_server",
                "selenium_server_port"
            ]:
            if len(value) > 0:
                self.options_dict[option] = value
            else:
            
                raise  argparse.ArgumentTypeError(\
                    f"Option {option.replace('_','-')} can not be empty string"
                ) 
                
        if option in [
                "global_warn_crit_timeout",
                "by_step_warn_crit_timeout",
                "each_step_warn_crit_timeout",
            ]:

            gwct_list = list(value.split(";"))

            if option == "global_warn_crit_timeout":
                self.global_timeout = int(gwct_list[2])
            
            if option == "by_step_warn_crit_timeout":
                
                if option not in self.options_dict:
                    self.options_dict[option] = {}
                
                step_name = str(gwct_list[0])
                gwct_list.pop(0)
                self.validate_semantic(option, gwct_list, parser)
                self.options_dict[option].update({step_name: {"warn":  int(gwct_list[0]), \
                    "crit":  int(gwct_list[1]) , "timeout": int(gwct_list[2])}})
            else:
                self.validate_semantic(option, gwct_list, parser)
                self.options_dict[option] = {"warn":  int(gwct_list[0]), \
                    "crit":  int(gwct_list[1]) , "timeout": int(gwct_list[2])}

class Scenario(object):
    def __init__(self, options):

        self.options = options
        
        self.centreon_status = {
            0: "OK",
            1: "WARNING",
            2: "CRITICAL",
            4: "UNKNOWN"
        }
        
        self.set_browser_options(self.options["browser"])

        self.driver = webdriver.Remote(
            command_executor=f'http://{self.options["selenium_server"]}:{self.options["selenium_server_port"]}/wd/hub',\
                options=self.browser_options
        )

        # self.driver.file_detector = LocalFileDetector()
        self.global_timeout = \
            self.options["global_warn_crit_timeout"]["timeout"]
        
        if "each_step_warn_crit_timeout" in self.options:
            self.each_step_timeout = \
                self.options["each_step_warn_crit_timeout"]["timeout"]
        else:
            self.each_step_timeout = False
            
        if "by_step_warn_crit_timeout" in self.options:
            self.named_step_timeout = {
                step_name: self.options["by_step_warn_crit_timeout"][step_name]["timeout"] \
                    for step_name in self.options["by_step_warn_crit_timeout"]
            }
        else:
            self.named_step_timeout = False
        
        # self.named_step_timeout = [name for name in self.options["by_step_warn_crit_timeout"]]
        
        self.timeout = self.calculate_timeout()
        self.steps_sum_time = 0
        self.scenario_start_time = 0
        self.start_time_step = 0
        self.prev_start_time_step = 0
        self.current_step_id = 0
        self.prev_step_id = 0
        self.scenario_end_time = 0
        self.prev_step_name = ""
        self.time_steps = {}
        
    def set_browser_options(self, browser):
        if browser == "firefox":
            from selenium.webdriver.firefox.options import Options
            self.browser_options = Options()
            if self.options["headless"]:
                self.browser_options.add_argument("--headless")
                self.browser_options.add_argument("--window-size=1366,768")
        elif browser == "chrome":
            from selenium.webdriver.chrome.options import Options
            self.browser_options = Options()
            self.browser_options.add_argument("--no-sandbox")
            if self.options["headless"]:
                self.browser_options.add_argument("--headless=new")
                self.browser_options.add_argument("--window-size=1366,768")
        elif browser == "edge":
            from selenium.webdriver.edge.options import Options
            self.browser_options = Options()
            self.browser_options.add_argument("--no-sandbox")
            if self.options["headless"]:
                self.browser_options.add_argument("--headless=new")
                self.browser_options.add_argument("--window-size=1366,768")
        else:
            print("browser unknown")
        
    def build_centreon_perfdata(self):
        metrics = []
        warn=self.options["global_warn_crit_timeout"]["warn"]
        crit=self.options["global_warn_crit_timeout"]["crit"]
        for k, v in self.time_steps.items():
            step_name = k
            
            if "by_step_warn_crit_timeout" in self.options:
                    if step_name in self.options["by_step_warn_crit_timeout"]:
                        # max=self.options["by_step_warn_crit_timeout"][step_name]["timeout"]
                        warn=self.options["by_step_warn_crit_timeout"][step_name]["warn"]
                        crit=self.options["by_step_warn_crit_timeout"][step_name]["crit"]
            elif "each_step_warn_crit_timeout" in self.options:
                warn=self.options["each_step_warn_crit_timeout"]["warn"]
                crit=self.options["each_step_warn_crit_timeout"]["crit"]
            
            
            if type(v) == dict:
    
                steps_list_of_named_step = ','.join(str(x) for x in v["steps"])
                metrics.append(
                    (
                        (
                            (
                                (
                                    f'{step_name}(steps:{steps_list_of_named_step})#scenario.step.time.milliseconds='
                                    + str(v["total"])
                                )
                                + 'ms;'
                            )
                            + str(warn)
                            + ';'
                        )
                        + str(crit)
                        + ";0;"
                    )
                    + ";"
                )

            else:
                step_name = "{:03d}".format(k) if type(k) == int else k
                
                metrics.append(
                    f'{step_name}#scenario.step.time.milliseconds={str(v)}ms;{str(warn)};{str(crit)};0;;'
                )
        
        total = f'total#scenario.step.time.milliseconds={str(self.steps_sum_time)}ms;{warn};{crit};0;;'
        
        metrics.append(total)
        
        return " ".join(metrics)
    
    def check_warn_crit(self, step_name, time_of_step):
        status = 0
        if  "by_step_warn_crit_timeout" in self.options \
                    and step_name in self.options["by_step_warn_crit_timeout"]:

                warn = self.options["by_step_warn_crit_timeout"][step_name]["warn"]
                crit = self.options["by_step_warn_crit_timeout"][step_name]["crit"]

        elif "each_step_warn_crit_timeout" in self.options \
                and step_name != "total":
            warn = self.options["each_step_warn_crit_timeout"]["warn"]
            crit = self.options["each_step_warn_crit_timeout"]["crit"]

        else:
            warn = self.options["global_warn_crit_timeout"]["warn"]
            crit = self.options["global_warn_crit_timeout"]["crit"]

        if time_of_step <= warn:
            status = 0
        elif time_of_step <= crit:
            status = 1
        else:
            status = 2

        return (step_name, status, time_of_step)
            
    def build_centreon_output(self, abort=False):
        exit_status=0
        output=[]
        total_time_scenario = self.time_steps["total"]
        status=self.check_warn_crit("total", total_time_scenario)
        
        if not abort:
            total_output = f'{self.current_step_id - 1}{" steps" if  int(self.current_step_id) > 1 else " step"  }:{self.centreon_status[status[1]]}:{status[2]}ms'
        else:
            status = ("total", 2, total_time_scenario)
            total_output = f'{self.current_step_id - 1}{" steps" if  int(self.current_step_id) > 1 else " step"  }:{self.centreon_status[2]}:Abort at Step {self.current_step_id-1}:{status[2]}ms'
        
        exit_status=status[1]
        output.append(total_output)
        
        for k, v in self.time_steps.items():
            if type(v) == dict:
                status = self.check_warn_crit(k, v["total"])
                if "by_step_warn_crit_timeout" in self.options:
                    if k in self.options["by_step_warn_crit_timeout"]:
                        steps_list_of_step = [f'{str(s)}' for s in v["steps"]]
                        step_output = f'{status[0]}(steps:{",".join(steps_list_of_step)}):{self.centreon_status[status[1]]}:{status[2]}ms'
                        if status[1] != 0:
                            output.append(step_output)
            else:
                status = self.check_warn_crit(k,v)
                step_output = f'step{status[0]}:{self.centreon_status[status[1]]}:{status[2]}ms'
                if status[1] != 0:
                    output.append(step_output)

            exit_status = max(exit_status,status[1])

        output = " ".join(output)
        
        metrics = self.build_centreon_perfdata()
        
        output = f'{output}|{metrics}'
        print(output)
        sys.exit(exit_status)

    def calculate_timeout(self, step_name=""):
        timeout = max(self.global_timeout, 0)
        
        if (
            self.each_step_timeout
            and (self.global_timeout - self.each_step_timeout) > 0
        ):
            timeout = self.each_step_timeout

        if (
            self.named_step_timeout
            and step_name in self.named_step_timeout
            and step_name != ""
        ):
            named_step_timeout = self.named_step_timeout[step_name]
            if (self.global_timeout - named_step_timeout) > 0:
                if (named_step_timeout - self.time_steps[step_name]["total"] > 0):
                    if self.each_step_timeout and (
                        self.each_step_timeout
                        <= named_step_timeout - self.time_steps[step_name]["total"]
                    ):
                        timeout = self.each_step_timeout
                    else:
                        timeout = named_step_timeout - self.time_steps[step_name]["total"]

                else:
                    timeout = 0


        if timeout == 0:
            raise('timeout exceded')

        timeout = timeout / 1000
        self.driver.set_page_load_timeout(timeout)
        self.driver.set_script_timeout(timeout)
        self.driver.implicitly_wait(timeout)
        return timeout
    
    def step_timer(self, step_name="", last_step = False, abort=False):
        if "by_step_warn_crit_timeout" in self.options:
            if step_name not in self.options["by_step_warn_crit_timeout"] and \
                len(step_name) > 0:
                print(f'{step_name} not in option "--by_step_warn_crit_timeout" passed to script')
                sys.exit(1)
        
        self.current_step_id += 1
        self.start_time_step = round(time.time() * 1000)
        if self.current_step_id == 1:
            self.scenario_start_time = self.start_time_step
        else:
            self.prev_step_id = self.current_step_id - 1
            self.calculate_time_step(step_name=step_name, last_step=last_step, abort=abort)
        
        if abort:
            return
        self.prev_start_time_step = self.start_time_step
        self.prev_step_name = step_name  
            
    def calculate_time_step(self, step_name="", last_step = False, abort=False):
        time_step = self.start_time_step - self.prev_start_time_step        
        self.time_steps.update({self.prev_step_id: time_step})

        if (step_name != "" and self.prev_step_name == "") or \
            (step_name !="" and self.prev_step_name != step_name):
            self.time_steps.update({ step_name: {"total": 0, \
                        "steps": []}})
            
        if self.prev_step_name != "":
            self.time_steps[self.prev_step_name]["steps"].append(self.prev_step_id)
            self.time_steps[self.prev_step_name]["total"] += time_step
                
        self.steps_sum_time += time_step
        self.time_steps.update({ "total": self.steps_sum_time}) 
        self.global_timeout -= time_step
        if last_step:
            self.driver.quit()
        else:
            
            self.timeout = self.calculate_timeout(step_name=step_name)
            return
    
class Main(object):
    
  
    def __init__(self):
            
        syntax_pattern = [
            r"^[1-9][0-9]{0,5};[1-9][0-9]{0,5};[1-9][0-9]{0,5}$",
            r"^[A-Za-z0-9]{1,20};[1-9][0-9]{0,5};[1-9][0-9]{0,5};[1-9][0-9]{0,5}$"     
        ]
        self.manage_options = Manage_options(syntax_pattern)

        
    def __call__(self):  # sourcery skip: de-morgan
        parser = argparse.ArgumentParser(description="Utilisation selenium-client.py")
        
        parser.add_argument("--global_warn_crit_timeout",  metavar='<warn>;<crit>;<timeout>',\
            type=self.manage_options.validate_syntax_gwct_eswct,\
                help= 'ex: "5000;6000;9000" each value in milliseconds',\
                required=True)
        
        parser.add_argument("--each_step_warn_crit_timeout",metavar='<warn>;<crit>;<timeout>', \
                    type=self.manage_options.validate_syntax_gwct_eswct, required=False, \
                        help= 'ex: "1000;2000;4000" each value in milliseconds')
        
        parser.add_argument("--by_step_warn_crit_timeout", \
                    type=self.manage_options.validate_syntax_beswct, nargs='*',\
                        metavar='<step name>;<warn>;<crit>;<timeout>',\
                            required=False, action="append",\
                        help= 'ex: "LOGIN;2500;3800;6000" <step name> is string \
                            and <warn>;<crit>;<timeout> value in milliseconds')
        
        parser.add_argument("--scenarios-dir", required=True, metavar='<directory path>',\
            help= 'ex: scenarios', type=self.manage_options.validate_scenario_dir)

        parser.add_argument("--scenario", required=True, type=str, metavar='<scenario name without .py on end>',\
            help="ex: myfirstscenario")
        
        parser.add_argument("--selenium-server",default="127.0.0.1", required=False, type=str, metavar='<selenium standalone server>',\
            help="ex: 127.0.0.1")
        
        parser.add_argument("--selenium-server-port",default="4444", required=False, type=str, metavar='<selenium standalone server>',\
            help="ex: 4444")
        
        parser.add_argument("--browser",  choices=['chrome', 'firefox', 'edge'],\
            required=True)
        
        parser.add_argument('--headless', action='store_true')
        
        args = parser.parse_args()

        for option in args.__dict__:
            value = getattr(args, option)
            if value != None:
                if type(value) == list:
                    for v in value:
                        self.manage_options.build_options_dict(option, v[0],parser)
                else:
                    self.manage_options.build_options_dict(option, value, parser)

        # add directory of python scenario module to the python path
        sys.path.append(f'{os.path.dirname(__file__)}/{self.manage_options.options_dict["scenarios_dir"]}')

        try:
            scenario = importlib.import_module(getattr(args, "scenario"))
        except ModuleNotFoundError as e:
            sys.exit(1)
        # ScenarioCustom = scenario.ScenarioCustom

        self.set_import_from_scenario(scenario)

        class ScenarioRunner(Scenario, scenario.ScenarioCustom):
            def __init__(self, options):
                super().__init__(options)
            def run(self):
                try:
                    
                    self.scenario_steps()
                    
                    self.step_timer(last_step=True)
                    self.build_centreon_output()

                except  Exception as e:
                    self.step_timer(last_step=True, abort=True)
                    self.build_centreon_output(abort = True)
            
        
        scenario_instance = ScenarioRunner(self.manage_options.options_dict)
            # display.start()
        scenario_instance.run()


    def set_import(self, module,name,alias):
        setattr(
                __import__(__name__),
                alias,
                eval(
                    f'importlib.import_module("{module}").{name}'
                ),
        )
    
    def set_import_from_scenario(self, scenario):
        filename = scenario.__file__

        with open(filename, "r") as file:
            source = file.read()
            tree = ast.parse(source)

        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                for name in node.names:
                    if name.asname:
                        self.set_import(node.module, name.name, name.asname)
                    else:
                        self.set_import(node.module, name.name, name.name)

if __name__ == "__main__":
    main = Main()
    main()