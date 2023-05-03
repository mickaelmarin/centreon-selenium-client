perfdata = {"1": 1500, "2": 852, "3": 727, "4": 319, "5": 164, "6": 381, "7": 373, "8": 753, "9": 710, "PUTAINDESTEP": {"total": 533, "steps": [10, 11, 12]}, "10": 17, "11": 80, "12": 436, "13": 27, "STEP3": {"total": 1451, "steps": [14, 15, 16, 17]}, "14": 13, "15": 354, "16": 324, "17": 760}
options={
            "global_warn_crit_timeout": {
                "warn": 1200,
                "crit": 1300,
                "timeout": 60000
            },
            "all_each_step_warn_crit_timeout": {
                "warn": 1800,
                "crit": 5509,
                "timeout": 7000
            },
            "by_step_warn_crit_timeout": {
                "PUTAINDESTEP": {
                "warn": 1222,
                "crit": 4000,
                "timeout": 6000
                },
                "STEP3": {
                "warn": 2000,
                "crit": 4000,
                "timeout": 8000
                },
                "STEP10": {
                "warn": 300,
                "crit": 4000,
                "timeout": 5000
                }
            }
        }
# metric1=<value>[UOM];<warning_value>;<critical_value>;<minimum>;<maximum>
# '/boot#storage.space.usage.bytes'=255832064B;;0:99579084;0;995790848
# milliseconds
#SCENARIO1~step1#scenario1.step1.time.milliseconds'=<steptime>ms;<warning>;<critical>;0;<timeout>'



    
def buildperf(perfdata):
    scenario_name = "scenario1"
    metrics = []
    for k, v in perfdata.items():
        if type(v) == dict:
            step_name = k
            steps_list = ""
            max=options["by_step_warn_crit_timeout"][step_name]["timeout"]
            warn=options["by_step_warn_crit_timeout"][step_name]["warn"]
            crit=options["by_step_warn_crit_timeout"][step_name]["crit"]
            
            steps_list_of_named_step = ','.join(str(x) for x in v["steps"])
            metrics.append(scenario_name + '~'+ step_name + '(steps:' + steps_list_of_named_step + ')' + '#' + \
                scenario_name +'.'+ step_name + '.time.milliseconds=' + \
                    str(v["total"]) + 'ms;' + str(warn) + ';' + str(crit) + ";0;" + str(max))
            
        else:
            if "all_each_step_warn_crit_timeout" in options:
                max=options["all_each_step_warn_crit_timeout"]["timeout"]
                warn=options["all_each_step_warn_crit_timeout"]["warn"]
                crit=options["all_each_step_warn_crit_timeout"]["crit"]
            else:
                max= options["global_warn_crit_timeout"]["timeout"]
                warn=options["global_warn_crit_timeout"]["warn"]
                crit=options["global_warn_crit_timeout"]["crit"]
                
            step_name = "step"+ str(k)
            metrics.append(scenario_name + '~'+ step_name + '#' + \
                scenario_name +'.'+ step_name + '.time.milliseconds=' + \
                    str(v) + 'ms;' + str(warn) + ';' + str(crit) + ";0;" + str(max))
    metrics = " ".join(metrics)

    print(metrics)
buildperf(perfdata)